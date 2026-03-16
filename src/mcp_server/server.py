"""
MCP server exposing tools for GPT: get_loan_overview, lookup_loan_document_extraction,
get_client_profile, get_upload_url, and check_loan_approval.
Designed to run on AWS Lambda behind API Gateway (Streamable HTTP).
"""
import json
import os
import re
import datetime
import urllib.parse
import boto3
from boto3.dynamodb.conditions import Key
from awslabs.mcp_lambda_handler import MCPLambdaHandler

mcp = MCPLambdaHandler(name="gpt-app-mcp", version="1.0.0")

_LOAN_OVERVIEW_TABLE = os.environ.get("LOAN_OVERVIEW_TABLE", "gpt-mcp-loan-overview-demo")
_CLIENT_PROFILE_TABLE = os.environ.get("CLIENT_PROFILE_TABLE", "gpt-mcp-client-profile-demo")
_LOAN_DOCUMENTS_BUCKET = os.environ.get("LOAN_DOCUMENTS_BUCKET", "gpt-mcp-loan-documents-demo")


def _lookup_loan_dynamo(loan_identifier: str) -> dict | None:
    """
    Look up a loan record from DynamoDB by loan_id or guid.
    Tries a direct GetItem by loan_id first; if that misses, queries the guid GSI.
    Returns the item dict, or None if not found.
    """
    table = boto3.resource("dynamodb").Table(_LOAN_OVERVIEW_TABLE)

    # Try loan_id first (primary key — O(1))
    response = table.get_item(Key={"loan_id": loan_identifier})
    item = response.get("Item")
    if item:
        return item

    # Fall back to GUID GSI query
    response = table.query(
        IndexName="guid-index",
        KeyConditionExpression=Key("guid").eq(loan_identifier),
        Limit=1,
    )
    items = response.get("Items", [])
    return items[0] if items else None


@mcp.tool()
def get_loan_overview(loan_identifier: str) -> str:
    """
    Retrieve a structured loan overview for a loan officer.

    Accepts either a numeric loan_id (e.g. "265561631") or a GUID
    (e.g. "4707ee03-e10d-4792-840f-eb871db8dfd4") as loan_identifier.

    Returns a comprehensive overview of the loan including: buyer names,
    state, property address, property type, property county, parcel number,
    base loan amount, loan purpose, loan status, organization, and the
    assigned loan officer.

    Use this whenever a loan officer asks about a loan by its ID or GUID,
    e.g. "give me an overview of loan 265561631" or "what do we know about
    4707ee03-e10d-4792-840f-eb871db8dfd4?".
    """
    item = _lookup_loan_dynamo(loan_identifier)
    if not item:
        return json.dumps({
            "error": "Loan not found",
            "loan_identifier": loan_identifier,
        })
    return json.dumps(item, indent=2, default=str)


_DOCEXT_LAMBDA = "document_extraction_OneLoan_Lookup"

# Searched in order — stops at the first organization that returns a match.
_DEFAULT_ORGS = ["gri", "gra", "kbhs", "citywide", "op", "premia", "pr"]


def _invoke_docext(loan_identifier: str, organization: str, environment: str) -> dict | None:
    """
    Invoke the document extraction Lambda for a single org.
    loan_identifier may be a numeric loan_id or a GUID — the Lambda accepts either.
    Returns the parsed inner body dict on success, or None if not found / error.
    """
    client = boto3.client("lambda")
    payload = {
        "organization": organization,
        "environment": environment,
        "loan_id": loan_identifier,
        "method": "get_docext",
    }
    response = client.invoke(
        FunctionName=_DOCEXT_LAMBDA,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode(),
    )
    result = json.loads(response["Payload"].read())

    if result.get("statusCode", 0) != 200:
        return None

    outer_body = result.get("body", {})
    if isinstance(outer_body, str):
        outer_body = json.loads(outer_body)

    if outer_body.get("statusCode", 0) != 200:
        return None

    inner_body = outer_body.get("body", {})
    if isinstance(inner_body, str):
        inner_body = json.loads(inner_body)

    return inner_body if inner_body else None


@mcp.tool()
def lookup_loan_document_extraction(
    loan_identifier: str,
    organization: str = "",
    environment: str = "prod",
) -> str:
    """
    Look up document extraction data for a loan from the OneLoan system.

    Accepts either a numeric loan_id (e.g. "265561631") or a GUID
    (e.g. "4707ee03-e10d-4792-840f-eb871db8dfd4") as loan_identifier.

    Retrieves all available data about the loan including: GUID, state,
    loan purpose, base loan amount, buyer names, buyer vesting, seller names,
    property type, property address, property county, parcel number, and
    borrower last name.

    If organization is not provided, the tool automatically searches all known
    organizations in order — gri, gra, kbhs, citywide, op, premia, pr — and
    returns results from the first match found.

    Use this whenever the user mentions a loan ID or GUID and asks anything
    about that loan, e.g. "tell me about loan 265561631", "who is the borrower
    on 4707ee03-e10d-4792-840f-eb871db8dfd4?", or "what is the property address
    for loan 265561631?".
    """
    orgs_to_try = [organization] if organization else _DEFAULT_ORGS

    for org in orgs_to_try:
        data = _invoke_docext(loan_identifier, org, environment)
        if data:
            data["_matched_organization"] = org
            return json.dumps(data, indent=2)

    return json.dumps({
        "error": "Loan not found in any organization",
        "loan_identifier": loan_identifier,
        "organizations_tried": orgs_to_try,
    })


def _lookup_client_profile(identifier: str) -> dict | None:
    """
    Look up a client profile from DynamoDB by borrower_id, loan_id, guid, or borrower name.
    Auto-detects the identifier type and tries the appropriate index.
    Returns the item dict, or None if not found.
    """
    table = boto3.resource("dynamodb").Table(_CLIENT_PROFILE_TABLE)

    # UUID format → guid GSI
    if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", identifier, re.IGNORECASE):
        resp = table.query(IndexName="guid-index", KeyConditionExpression=Key("guid").eq(identifier), Limit=1)
        items = resp.get("Items", [])
        return items[0] if items else None

    # All digits → loan_id GSI
    if identifier.isdigit():
        resp = table.query(IndexName="loan_id-index", KeyConditionExpression=Key("loan_id").eq(identifier), Limit=1)
        items = resp.get("Items", [])
        return items[0] if items else None

    # Contains a space → name lookup via name GSI.
    # Handles "First Last", "First M Last", "First Middle Last", "Last First".
    if " " in identifier.strip():
        tokens = identifier.strip().split()
        # Try: first=tokens[0], last=tokens[-1] (covers "John Homeowner", "John A Homeowner")
        first, last = tokens[0], tokens[-1]
        resp = table.query(
            IndexName="name-index",
            KeyConditionExpression=Key("borrower_last_name").eq(last) & Key("borrower_first_name").eq(first),
            Limit=1,
        )
        items = resp.get("Items", [])
        if items:
            return items[0]
        # Try reversed: last=tokens[0], first=tokens[-1] (covers "Homeowner John")
        resp = table.query(
            IndexName="name-index",
            KeyConditionExpression=Key("borrower_last_name").eq(tokens[0]) & Key("borrower_first_name").eq(tokens[-1]),
            Limit=1,
        )
        items = resp.get("Items", [])
        if items:
            return items[0]
        # Last fallback: last=tokens[0], first prefix match on rest
        resp = table.query(
            IndexName="name-index",
            KeyConditionExpression=Key("borrower_last_name").eq(tokens[0]) & Key("borrower_first_name").begins_with(tokens[1]),
            Limit=1,
        )
        items = resp.get("Items", [])
        return items[0] if items else None

    # Fall back to borrower_id direct lookup
    resp = table.get_item(Key={"borrower_id": identifier})
    return resp.get("Item")


@mcp.tool()
def get_client_profile(identifier: str) -> str:
    """
    Retrieve a comprehensive client profile for a borrower, displayed in a
    RateMyProfessor-style format with personal background, loan history, and
    reviews from other loan officers.

    Accepts any of the following as identifier:
    - Borrower full name (e.g. "John Homeowner" or "Homeowner John")
    - Numeric loan_id (e.g. "265561631")
    - GUID (e.g. "4707ee03-e10d-4792-840f-eb871db8dfd4")
    - borrower_id slug (e.g. "homeowner-john-a")

    Returns the full client profile including:
    - Personal background and notes
    - Complete loan history with amounts, purposes, and statuses
    - Reviews from other loan officers with ratings and comments
    - Overall rating across all reviews

    Use this whenever a loan officer asks about a client or borrower, e.g.:
    "tell me about this client", "what's the background on John Homeowner",
    "pull up the profile for loan 265561631", "what do other loan officers
    say about this borrower?", "give me a client review for 265561631".
    """
    item = _lookup_client_profile(identifier)
    if not item:
        return json.dumps({
            "error": "Client profile not found",
            "identifier": identifier,
        })
    return json.dumps(item, indent=2, default=str)


# ---------------------------------------------------------------------------
# Auto-approval tools
# ---------------------------------------------------------------------------

_LOW_RISK_STATES = {"IL", "TX", "CA", "WA", "CO", "FL", "NY", "AZ", "NV", "OR"}


def _run_approval_rules(loan: dict, document_present: bool) -> dict:
    """
    Score-based fake rule engine. Deterministic for a given loan_id.
    Returns a dict with decision, score, max_score, and rules_applied list.
    """
    rules_applied = []

    def rule(name: str, points: int, passed: bool) -> int:
        rules_applied.append({"rule": name, "points": points if passed else 0, "passed": passed})
        return points if passed else 0

    score = 0
    amount = float(loan.get("base_loan_amount", 0))

    if amount <= 400_000:
        score += rule("Loan amount <= $400k", 30, True)
    elif amount <= 600_000:
        score += rule("Loan amount <= $600k", 15, True)
        rule("Loan amount <= $400k", 30, False)
    else:
        rule("Loan amount <= $400k", 30, False)
        rule("Loan amount <= $600k", 15, False)
        score += rule("Loan amount > $600k penalty", -10, True)

    score += rule(
        "Property type is Detached",
        20,
        str(loan.get("property_type", "")).lower() == "detached",
    )
    purpose = str(loan.get("loan_purpose", "")).lower()
    if purpose == "purchase":
        score += rule("Loan purpose is Purchase", 15, True)
    elif purpose == "refinance":
        rule("Loan purpose is Purchase", 15, False)
        score += rule("Loan purpose is Refinance", 10, True)
    else:
        rule("Loan purpose is Purchase", 15, False)
        rule("Loan purpose is Refinance", 10, False)

    score += rule(
        "State in low-risk list",
        15,
        str(loan.get("state", "")).upper() in _LOW_RISK_STATES,
    )

    # Deterministic tiebreaker seeded by loan_id digit sum
    digit_sum = sum(int(c) for c in str(loan.get("loan_id", "0")) if c.isdigit())
    score += rule("Loan ID deterministic bonus", 10, digit_sum % 2 == 0)

    score += rule("Document received and on file", 10, document_present)

    max_score = 100
    if score >= 70:
        decision = "APPROVED"
    elif score >= 50:
        decision = "MANUAL REVIEW"
    else:
        decision = "DENIED"

    return {
        "decision": decision,
        "score": score,
        "max_score": max_score,
        "rules_applied": rules_applied,
    }


@mcp.tool()
def get_upload_url(loan_id: str, filename: str) -> str:
    """
    Generate a clickable https:// upload link for a loan document (PDF).

    Call this when a loan officer wants to submit a document for auto-approval review.
    Returns a real https:// URL the loan officer can click to open a browser-based
    drag-and-drop upload form. The form expires in 5 minutes.

    After the loan officer confirms the upload is complete, call check_loan_approval
    with the loan_id and the s3_key returned here.

    Use this whenever a loan officer says things like:
    "I want to upload a document for loan 265561631",
    "here is a PDF I want to submit for loan 265561631",
    "can you give me an upload link for this loan?".
    """
    s3_key = f"uploads/{loan_id}/{filename}"
    presigned = boto3.client("s3").generate_presigned_post(
        Bucket=_LOAN_DOCUMENTS_BUCKET,
        Key=s3_key,
        Fields={"Content-Type": "application/pdf"},
        Conditions=[{"Content-Type": "application/pdf"}],
        ExpiresIn=300,
    )

    # Build query string: action=<post_url> + loan metadata + f_<field>=<value> for each POST field
    qs_params = {
        "action": presigned["url"],
        "loan_id": loan_id,
        "filename": filename,
        "expires_in": "300",
    }
    for k, v in presigned["fields"].items():
        qs_params[f"f_{k}"] = v

    bucket_name = _LOAN_DOCUMENTS_BUCKET
    region = boto3.session.Session().region_name or "us-east-2"
    website_base = f"http://{bucket_name}.s3-website.{region}.amazonaws.com/upload.html"
    upload_link = website_base + "?" + urllib.parse.urlencode(qs_params)

    return json.dumps({
        "upload_link": upload_link,
        "s3_key": s3_key,
        "expires_in_seconds": 300,
        "instructions": (
            "Present upload_link as a clickable hyperlink. The loan officer opens it, "
            "drags and drops their PDF, and clicks Upload. Once they confirm it is done, "
            "call check_loan_approval with loan_id and s3_key."
        ),
    })


@mcp.tool()
def check_loan_approval(loan_id: str, s3_key: str = "") -> str:
    """
    Run the auto-approval engine on a loan and return a detailed approval verdict.

    Evaluates the loan against underwriting rules and returns a scored decision.
    Optionally pass the s3_key from get_upload_url — if a document was uploaded,
    the engine confirms its presence and awards a bonus 10 points.

    The engine evaluates:
    - Loan amount thresholds ($400k / $600k breakpoints)
    - Property type (Detached preferred)
    - Loan purpose (Purchase > Refinance)
    - State risk classification (IL, TX, CA and other low-risk states)
    - Document received and on file (+10 bonus if s3_key provided and file exists)
    - Deterministic loan ID tiebreaker (consistent results for same loan)

    Returns a structured verdict:
    - decision: APPROVED, MANUAL REVIEW, or DENIED
    - score and max_score (out of 100)
    - rules_applied: each rule with points earned and pass/fail
    - document_received: whether the uploaded document was confirmed in S3

    Display as a structured approval report with each rule listed clearly,
    showing the score breakdown and final decision prominently.

    Use this whenever a loan officer asks about auto-approval, e.g.:
    "check if loan 265561631 can be auto-approved",
    "run approval check on this loan",
    "is loan 265561631 eligible for auto-approval?",
    "I've uploaded the document, now check the approval".
    """
    document_present = False
    if s3_key:
        try:
            boto3.client("s3").head_object(Bucket=_LOAN_DOCUMENTS_BUCKET, Key=s3_key)
            document_present = True
        except Exception:
            pass

    loan = _lookup_loan_dynamo(loan_id)
    if not loan:
        return json.dumps({"error": "Loan not found", "loan_id": loan_id})

    result = _run_approval_rules(loan, document_present)
    result.update({
        "loan_id": loan_id,
        "document_received": document_present,
        "s3_key": s3_key or None,
        "reviewed_at": datetime.datetime.utcnow().isoformat() + "Z",
    })
    return json.dumps(result, indent=2, default=str)


def lambda_handler(event, context):
    """AWS Lambda entrypoint. Wire this in your Lambda configuration."""
    return mcp.handle_request(event, context)
