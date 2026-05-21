import json
import logging
import boto3

logger = logging.getLogger(__name__)

DOCEXT_LAMBDA = "document_extraction_OneLoan_Lookup"

# Valid organization codes the Lambda accepts (all lowercase).
DEFAULT_ORGS = ["gri", "gra", "kbhs", "citywide", "op", "premia", "pr"]

# Normalize environment aliases → canonical value the Lambda expects.
_ENV_ALIASES = {
    "production": "prod",
    "prd": "prod",
    "staging": "staging",
    "stg": "staging",
    "development": "dev",
}


def _normalize_env(env: str) -> str:
    return _ENV_ALIASES.get(env.strip().lower(), env.strip().lower()) or "prod"


def invoke_docext(loan_identifier: str, organization: str, environment: str) -> dict | None:
    """
    Invoke the document extraction Lambda for a single org.
    Returns the parsed inner body dict on success, or None if not found / error.
    """
    client = boto3.client("lambda")
    payload = {
        "organization": organization,
        "environment": _normalize_env(environment),
        "loan_id": loan_identifier,
        "method": "get_docext",
    }

    response = client.invoke(
        FunctionName=DOCEXT_LAMBDA,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload).encode(),
    )

    if response.get("FunctionError"):
        raw = response["Payload"].read()
        logger.error("docext FunctionError org=%s loan=%s: %s", organization, loan_identifier, raw[:500])
        return None

    raw_payload = response["Payload"].read()
    try:
        result = json.loads(raw_payload)
    except json.JSONDecodeError:
        logger.error("docext non-JSON payload org=%s loan=%s: %s", organization, loan_identifier, raw_payload[:300])
        return None

    if result.get("statusCode", 0) != 200:
        logger.debug("docext outer statusCode=%s org=%s loan=%s", result.get("statusCode"), organization, loan_identifier)
        return None

    outer_body = result.get("body", {})
    if isinstance(outer_body, str):
        try:
            outer_body = json.loads(outer_body)
        except json.JSONDecodeError:
            logger.error("docext outer body not JSON org=%s: %s", organization, outer_body[:200])
            return None

    if outer_body.get("statusCode", 0) != 200:
        logger.debug("docext inner statusCode=%s org=%s loan=%s", outer_body.get("statusCode"), organization, loan_identifier)
        return None

    inner_body = outer_body.get("body", {})
    if isinstance(inner_body, str):
        try:
            inner_body = json.loads(inner_body)
        except json.JSONDecodeError:
            logger.error("docext inner body not JSON org=%s: %s", organization, inner_body[:200])
            return None

    return inner_body if inner_body else None
