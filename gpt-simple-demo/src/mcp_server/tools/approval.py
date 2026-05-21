import datetime
import boto3
from mcp_server.registry import mcp
from mcp_server.config import LOAN_DOCUMENTS_BUCKET, LOW_RISK_STATES, HIGH_RISK_INSURANCE_STATES
from mcp_server.utils.dynamo import lookup_loan_dynamo
from mcp_server.utils.docext import invoke_docext, DEFAULT_ORGS

_CONFORMING_LIMIT = 766_550
_TITLE_ELEVATED_STATES = {"FL", "TX", "NY", "NJ", "MD", "GA"}
_WILDFIRE_STATES = {"CA", "OR", "WA", "CO", "NM", "ID", "MT", "AZ"}
_HURRICANE_STATES = {"FL", "LA", "MS", "AL", "SC", "TX", "NC", "GA"}

_PORTAL_URL = "https://autoapproval.prajnagpt.net/login"


def _flag_hit(flags: list, *keywords: str) -> bool:
    text = " ".join(str(f).lower() for f in flags)
    return any(kw.lower() in text for kw in keywords)


def run_title_approval_rules(loan: dict, document_present: bool) -> dict:
    """
    Title document approval rule engine.
    Mirrors real underwriting criteria: loan size vs conforming limit, LTV proxy,
    property type, chain-of-title completeness, state complexity, pipeline age,
    and existing risk flags.
    """
    rules_applied = []

    def rule(name: str, points: int, passed: bool, detail: str = "") -> int:
        entry = {"rule": name, "points": points if passed else 0, "passed": passed}
        if detail:
            entry["detail"] = detail
        rules_applied.append(entry)
        return points if passed else 0

    score = 0
    amount = float(loan.get("base_loan_amount", 0))
    state = str(loan.get("state", "")).upper()
    purpose = str(loan.get("loan_purpose", "")).lower()
    prop_type = str(loan.get("property_type", "")).lower()
    parcel = str(loan.get("parcel_number", "")).strip()
    seller = str(loan.get("seller_names", "")).strip()
    days = int(loan.get("days_in_pipeline", 0) or 0)
    median = float(loan.get("market_median_price", 0) or 0)
    risk_flags = loan.get("risk_flags", [])

    if amount <= _CONFORMING_LIMIT:
        score += rule("Conforming loan amount", 20, True,
                      f"${amount:,.0f} is within the ${_CONFORMING_LIMIT:,.0f} conforming limit")
    elif amount <= 1_000_000:
        score += rule("Conforming loan amount", 20, False)
        score += rule("High-balance / agency-eligible", 10, True,
                      f"${amount:,.0f} is above conforming but below $1M — title search complexity increases")
    else:
        score += rule("Conforming loan amount", 20, False)
        score += rule("Jumbo loan — enhanced title review required", -5, True,
                      f"${amount:,.0f} exceeds $1M; full title chain audit and extended search required")

    if prop_type == "detached":
        score += rule("Property type: single-family detached", 15, True,
                      "Simplest title profile — no HOA right-of-first-refusal or shared-wall encumbrances")
    elif prop_type in ("condo", "attached"):
        score += rule("Property type: single-family detached", 15, False)
        score += rule("Condo/attached — HOA lien search required", 8, True,
                      "HOA super-lien states require additional CC&R review; master policy check needed")
    else:
        score += rule("Property type: single-family detached", 15, False)
        score += rule("Non-standard property type", 5, True,
                      f"'{prop_type}' properties require specialized title review")

    if purpose == "purchase":
        score += rule("Loan purpose: purchase — clean title transfer", 15, True,
                      "New title search establishes fresh chain of title from seller to buyer")
    elif purpose == "refinance":
        score += rule("Loan purpose: purchase — clean title transfer", 15, False)
        score += rule("Refinance — existing lien search required", 10, True,
                      "Must verify all existing liens and encumbrances are satisfied or subordinated")
    else:
        score += rule("Loan purpose: purchase — clean title transfer", 15, False)
        score += rule("Refinance — existing lien search required", 10, False)
        score += rule("Cash-out refi — elevated lien complexity", 5, True,
                      "Cash-out increases lien exposure; requires full encumbrance audit")

    if state in _TITLE_ELEVATED_STATES:
        score += rule(f"State title risk: {state}", 10, False,
                      f"{state} has elevated title complexity (attorney state, high fraud index, or complex lien law)")
    elif state in LOW_RISK_STATES:
        score += rule(f"State title risk: {state}", 10, True,
                      f"{state} has a clean title environment with low fraud index and standard lien law")
    else:
        score += rule(f"State title risk: {state}", 10, False)
        score += rule(f"State title risk: {state} (standard)", 6, True,
                      f"{state} is standard — no elevated complexity, but not in low-risk tier")

    score += rule("Parcel number on file", 10, bool(parcel),
                  f"APN {parcel}" if parcel else "Missing APN — cannot run automated title search without it")

    if purpose == "purchase":
        score += rule("Seller / grantor identity confirmed", 10, bool(seller),
                      f"Grantor: {seller}" if seller else "Seller name missing — chain of title cannot be verified")
    else:
        score += rule("Seller / grantor identity confirmed (N/A for refi)", 10, True,
                      "Not required for refinance")

    if median > 0:
        ltv = amount / median
        if ltv <= 0.80:
            score += rule("Estimated LTV ≤ 80%", 10, True,
                          f"Loan ${amount:,.0f} vs median ${median:,.0f} → ~{ltv:.0%} LTV; strong equity cushion")
        elif ltv <= 0.95:
            score += rule("Estimated LTV ≤ 80%", 10, False)
            score += rule("Estimated LTV 80–95%", 6, True,
                          f"~{ltv:.0%} LTV — standard range but PMI or additional review may be required")
        else:
            score += rule("Estimated LTV ≤ 80%", 10, False)
            score += rule("Estimated LTV > 95% — high leverage flag", -5, True,
                          f"~{ltv:.0%} LTV exceeds 95%; elevated title risk due to minimal equity")

    if days > 90:
        score += rule("Loan not stale (< 90 days in pipeline)", 5, False,
                      f"{days} days in pipeline — commitments and title search may need refresh")
    else:
        score += rule("Loan not stale (< 90 days in pipeline)", 5, True,
                      f"{days} days — within standard processing window")

    title_flag_hits = [f for f in risk_flags if any(
        kw in str(f).lower() for kw in ["lien", "dispute", "hoa", "encumbrance", "easement", "flood", "commercial"]
    )]
    flag_penalty = min(len(title_flag_hits) * 5, 15)
    if title_flag_hits:
        score -= flag_penalty
        rules_applied.append({
            "rule": f"Risk flags requiring title attention ({len(title_flag_hits)} found)",
            "points": -flag_penalty,
            "passed": False,
            "detail": "; ".join(str(f) for f in title_flag_hits),
        })

    score += rule("Title document uploaded", 5, document_present,
                  "Document confirmed in S3" if document_present else "No document on file — upload required for full review")

    score = max(score, 0)
    if score >= 70:
        decision = "APPROVED"
    elif score >= 50:
        decision = "MANUAL REVIEW"
    else:
        decision = "DENIED"

    return {"decision": decision, "score": score, "max_score": 105, "rules_applied": rules_applied}


def run_insurance_approval_rules(loan: dict, document_present: bool) -> dict:
    """
    Insurance document approval rule engine.
    Mirrors real underwriting criteria: catastrophic hazard exposure by state and county,
    property type, loan size vs replacement cost, loan purpose, pipeline age,
    and existing risk flags indicating flood/wildfire/prior claims.
    """
    rules_applied = []

    def rule(name: str, points: int, passed: bool, detail: str = "") -> int:
        entry = {"rule": name, "points": points if passed else 0, "passed": passed}
        if detail:
            entry["detail"] = detail
        rules_applied.append(entry)
        return points if passed else 0

    score = 0
    amount = float(loan.get("base_loan_amount", 0))
    state = str(loan.get("state", "")).upper()
    prop_type = str(loan.get("property_type", "")).lower()
    purpose = str(loan.get("loan_purpose", "")).lower()
    county = str(loan.get("property_county", "")).lower()
    days = int(loan.get("days_in_pipeline", 0) or 0)
    median = float(loan.get("market_median_price", 0) or 0)
    risk_flags = loan.get("risk_flags", [])

    is_hurricane = state in _HURRICANE_STATES
    is_wildfire = state in _WILDFIRE_STATES
    if is_hurricane and is_wildfire:
        score += rule(f"Catastrophic hazard: {state}", 25, False,
                      f"{state} carries BOTH hurricane and wildfire exposure — specialty coverage and reinsurance required")
    elif is_hurricane:
        score += rule(f"Catastrophic hazard: {state}", 25, False,
                      f"{state} is in the hurricane belt — wind/flood endorsements and carrier availability checks required")
    elif is_wildfire:
        score += rule(f"Catastrophic hazard: {state}", 25, False)
        score += rule(f"Elevated wildfire risk: {state}", 12, True,
                      f"{state} has wildfire exposure but standard homeowner coverage is generally available outside high-risk zones")
    else:
        score += rule(f"Low catastrophic hazard: {state}", 25, True,
                      f"{state} is outside primary hurricane and wildfire corridors — standard HO-3 policy expected")

    if prop_type == "detached":
        score += rule("Property type: single-family detached", 20, True,
                      "Standard HO-3 open-perils policy applies; straightforward coverage underwriting")
    elif prop_type in ("condo", "attached"):
        score += rule("Property type: single-family detached", 20, False)
        score += rule("Condo/attached — walls-in HO-6 required", 12, True,
                      "Must verify master HOA policy covers structure; HO-6 covers interior and personal property")
    else:
        score += rule("Property type: single-family detached", 20, False)
        score += rule(f"Non-standard property type: {prop_type}", 8, True,
                      "Specialty form may be required; confirm carrier eligibility")

    if amount <= 300_000:
        score += rule("Loan amount — standard replacement cost band", 20, True,
                      f"${amount:,.0f} is within the standard homeowner market; broad carrier availability")
    elif amount <= 600_000:
        score += rule("Loan amount — standard replacement cost band", 20, False)
        score += rule("Loan amount — mid-market ($300k–$600k)", 12, True,
                      f"${amount:,.0f} is serviceable by most carriers, but replacement cost endorsement recommended")
    elif amount <= 1_000_000:
        score += rule("Loan amount — standard replacement cost band", 20, False)
        score += rule("High-value property ($600k–$1M)", 6, True,
                      f"${amount:,.0f} may require admitted high-value or excess/surplus lines carrier")
    else:
        score += rule("Loan amount — standard replacement cost band", 20, False)
        score += rule("High-value property ($600k–$1M)", 6, False)
        score += rule("Jumbo replacement cost — specialty coverage required", -5, True,
                      f"${amount:,.0f} requires specialty or E&S carrier; standard markets likely unavailable")

    if purpose == "refinance":
        score += rule("Loan purpose: refinance — existing policy in force", 10, True,
                      "Active homeowner policy expected to be in place; verify no lapse and lender is listed as mortgagee")
    elif purpose == "purchase":
        score += rule("Loan purpose: refinance — existing policy in force", 10, False)
        score += rule("Loan purpose: purchase — new policy required", 8, True,
                      "Borrower must bind new HO-3 before closing; evidence of insurance (EOI) required at settlement")
    else:
        score += rule("Loan purpose: refinance — existing policy in force", 10, False)
        score += rule("Loan purpose: purchase — new policy required", 8, False)
        score += rule("Cash-out refi — confirm coverage not reduced", 5, True,
                      "Ensure increased loan amount is still covered by existing policy limits")

    flood_flag = _flag_hit(risk_flags, "flood")
    high_flood_counties = {"harris", "miami-dade", "broward", "palm beach", "new orleans", "jefferson"}
    in_flood_county = any(hc in county for hc in high_flood_counties)
    if flood_flag or in_flood_county:
        score += rule("No flood zone exposure", 10, False,
                      "Property may be in a FEMA Special Flood Hazard Area — NFIP or private flood policy required in addition to HO-3")
    else:
        score += rule("No flood zone exposure", 10, True,
                      "No flood zone indicators on record; standard HO-3 flood exclusion accepted")

    wildfire_flag = _flag_hit(risk_flags, "wildfire", "fire", "wind", "hurricane", "hail")
    if wildfire_flag:
        score += rule("No active wildfire/wind risk flags", 10, False,
                      "Risk flags indicate potential exposure — FAIR plan or admitted wildfire endorsement may be required")
    else:
        score += rule("No active wildfire/wind risk flags", 10, True,
                      "No wildfire or wind risk flags on record")

    if median > 0:
        ltv = amount / median
        if ltv <= 0.80:
            score += rule("Adequate equity cushion for coverage adequacy", 5, True,
                          f"~{ltv:.0%} LTV — replacement cost likely exceeds loan balance; co-insurance risk low")
        else:
            score += rule("Adequate equity cushion for coverage adequacy", 5, False,
                          f"~{ltv:.0%} LTV — ensure policy limits meet or exceed replacement cost, not just loan balance")

    if days > 60:
        score += rule("Insurance binder current (< 60 days)", 5, False,
                      f"{days} days in pipeline — verify binder has not expired; most carriers issue 30–60 day binders")
    else:
        score += rule("Insurance binder current (< 60 days)", 5, True,
                      f"{days} days — within standard binder window")

    claim_flag_hits = [f for f in risk_flags if any(
        kw in str(f).lower() for kw in ["claim", "loss", "damage", "mold", "sinkhole", "prior"]
    )]
    flag_penalty = min(len(claim_flag_hits) * 5, 15)
    if claim_flag_hits:
        score -= flag_penalty
        rules_applied.append({
            "rule": f"Prior loss / high-risk flags ({len(claim_flag_hits)} found)",
            "points": -flag_penalty,
            "passed": False,
            "detail": "; ".join(str(f) for f in claim_flag_hits),
        })

    score += rule("Insurance document / EOI uploaded", 5, document_present,
                  "Evidence of insurance confirmed in S3" if document_present else "No EOI on file — binder or declarations page required before closing")

    score = max(score, 0)
    if score >= 70:
        decision = "APPROVED"
    elif score >= 50:
        decision = "MANUAL REVIEW"
    else:
        decision = "DENIED"

    return {"decision": decision, "score": score, "max_score": 110, "rules_applied": rules_applied}


def _score_bar(score: int, max_score: int) -> str:
    filled = round(score / max_score * 10)
    return "█" * filled + "░" * (10 - filled)


def _rules_table(rules_applied: list) -> str:
    rows = []
    for r in rules_applied:
        pts = r["points"]
        status = "✅" if r["passed"] else ("➖" if pts == 0 else "⬇️")
        pts_display = f"+{pts}" if pts > 0 else str(pts)
        detail = r.get("detail", "")
        detail_cell = f"<br><small>{detail[:90]}</small>" if detail else ""
        rows.append(
            f"| {status} | {r['rule']}{detail_cell} | **{pts_display}** |"
        )
    return (
        "| | Rule | Points |\n"
        "|---|---|---|\n"
        + "\n".join(rows)
    )


def _oneloan_section(loan_id: str) -> str:
    for org in DEFAULT_ORGS:
        data = invoke_docext(loan_id, org, "prod")
        if data:
            org_display = org.upper()
            rows = []
            labels = {
                "guid": "GUID",
                "state": "State",
                "loan_purpose_type": "Loan Purpose",
                "extracted_buyer_names": "Borrower",
                "extracted_property_type": "Property Type",
                "extracted_property_address": "Property Address",
                "extracted_property_county": "County",
            }
            for key, label in labels.items():
                val = str(data.get(key, "")).strip()
                if val:
                    rows.append(f"| **{label}** | {val} |")
            table = "\n".join(rows) if rows else "_No fields returned._"
            return (
                f"\n---\n\n### 📄 ONELOAN DATA — `{org_display}`\n\n"
                "| Field | Value |\n"
                "|---|---|\n"
                f"{table}\n"
            )
    return "\n---\n\n### 📄 ONELOAN DATA\n\n_No OneLoan record found for this loan._\n"


@mcp.tool()
def check_loan_approval(
    loan_id: str,
    document_type: str = "title",
    s3_key: str = "",
    check_type: str = "quick",
) -> str:
    """
    Run the auto-approval engine on a loan and return a scored verdict.

    This is the ONLY tool to use for anything related to approval, approval
    check, approval status, approval score, or whether a loan can be approved.

    check_type:
    - "quick"    (default) — instant scored rule engine, returns decision now
    - "thorough" — directs the user to the full Auto-Approval portal

    document_type:
    - "title"     — title document underwriting rules
    - "insurance" — insurance/hazard coverage underwriting rules

    Use this when the user asks about approval, approval check, or approval
    status for a loan, e.g.:
    - "run a quick title approval check for loan 265561631"
    - "check approval for loan 265561631"
    - "is loan 265561631 approved?"
    - "run the approval engine on loan 265561631"
    - "do a title approval check on loan 123456789"
    - "check insurance approval for loan 265561631"
    - "run insurance auto approval for loan 265561631"
    - "I've uploaded the document, now check the approval"
    - "do a thorough approval check for loan 265561631"
    - "can this loan be auto-approved?"

    Do NOT use this for:
    - General loan info or status → use get_loan_overview or get_loan_intelligence_report
    - Uploading a document → use get_upload_url first
    """
    if check_type.lower().strip() == "thorough":
        doc_label = document_type.title()
        return (
            f"## 🔍 THOROUGH REVIEW — Loan #{loan_id}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"**Document Type:** {doc_label}\n\n"
            "> A thorough review requires a licensed underwriter and cannot be\n"
            "> completed automatically. Please use the full Auto-Approval portal.\n\n"
            "---\n\n"
            f"### 🌐 Auto-Approval Portal\n\n"
            f"**[→ Log in to the Auto-Approval Portal]({_PORTAL_URL})**\n\n"
            f"`{_PORTAL_URL}`\n\n"
            "Log in to run a comprehensive underwriting review for this loan.\n"
        )

    document_present = False
    if s3_key:
        try:
            boto3.client("s3").head_object(Bucket=LOAN_DOCUMENTS_BUCKET, Key=s3_key)
            document_present = True
        except Exception:
            pass

    loan = lookup_loan_dynamo(loan_id)
    if not loan:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No loan record found for `{loan_id}`. Please verify the loan ID."
        )

    doc_type = document_type.lower().strip()
    if doc_type == "insurance":
        result = run_insurance_approval_rules(loan, document_present)
    else:
        doc_type = "title"
        result = run_title_approval_rules(loan, document_present)

    score = result["score"]
    max_score = result["max_score"]
    decision = result["decision"]

    verdict_map = {
        "APPROVED": ("✅", "APPROVED", "All key criteria passed. This loan is cleared for auto-approval."),
        "MANUAL REVIEW": ("⚠️", "MANUAL REVIEW", "One or more factors require underwriter sign-off before approval can be granted."),
        "DENIED": ("❌", "DENIED", "Blocking factors prevent auto-approval. Manual underwriting or remediation required."),
    }
    verdict_icon, verdict_label, verdict_note = verdict_map.get(decision, ("❓", decision, ""))

    bar = _score_bar(score, max_score)
    doc_label = doc_type.title()

    # Narrative
    amount = float(loan.get("base_loan_amount", 0))
    prop_type = str(loan.get("property_type", "")).title()
    state = str(loan.get("state", ""))
    address = str(loan.get("property_address", ""))
    purpose = str(loan.get("loan_purpose", "")).title()

    failed_rules = [r["rule"] for r in result["rules_applied"] if not r["passed"] and r["points"] == 0]
    top_failure = failed_rules[0] if failed_rules else None

    if decision == "APPROVED":
        narrative = (
            f"{prop_type} property at {address} cleared all key {doc_type} criteria. "
            f"{purpose} loan of ${amount:,.0f} in {state} presents a clean underwriting profile."
        )
    elif decision == "MANUAL REVIEW":
        detail = f" Primary flag: _{top_failure}_." if top_failure else ""
        narrative = (
            f"${amount:,.0f} {purpose.lower()} in {state} passed most criteria "
            f"but requires underwriter sign-off.{detail}"
        )
    else:
        detail = f" Blocking factor: _{top_failure}_." if top_failure else ""
        narrative = (
            f"Auto-approval cannot be issued for this ${amount:,.0f} {purpose.lower()} in {state}.{detail}"
        )

    # Market context
    median = loan.get("market_median_price", "N/A")
    rate_env = loan.get("rate_environment", "N/A")
    comp = loan.get("comparable_approvals_qtd", "N/A")
    try:
        median_fmt = f"${float(median):,.0f}"
    except (ValueError, TypeError):
        median_fmt = str(median)

    reviewed_at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    doc_status = "✅ Document on file" if document_present else "📭 No document uploaded"

    rules_table = _rules_table(result["rules_applied"])
    oneloan_section = _oneloan_section(loan_id)

    portal_note = ""
    if decision in ("MANUAL REVIEW", "DENIED"):
        portal_note = (
            f"\n> 💡 **For a full review:** [Open the Auto-Approval Portal]({_PORTAL_URL})\n"
        )

    return (
        f"## {verdict_icon} AUTO-APPROVAL — Loan #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Document:** {doc_label} &nbsp;|&nbsp; **Check:** Quick &nbsp;|&nbsp; **Reviewed:** {reviewed_at}\n\n"
        "---\n\n"
        f"### {verdict_icon} VERDICT: {verdict_label}\n\n"
        f"```\n{bar}  {score}/{max_score}\n```\n\n"
        f"> {verdict_note}\n\n"
        f"_{narrative}_\n\n"
        f"**Document status:** {doc_status}\n"
        f"{portal_note}"
        "---\n\n"
        "### 📋 RULE BREAKDOWN\n\n"
        f"{rules_table}\n\n"
        "---\n\n"
        "### 📈 MARKET CONTEXT\n\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| Median Home Price | {median_fmt} |\n"
        f"| Rate Environment | {rate_env} |\n"
        f"| Comparable Approvals (QTD) | {comp} |\n"
        f"{oneloan_section}"
    )


@mcp.tool()
def get_auto_approval_portal(loan_id: str = "") -> str:
    """
    Open the full Auto-Approval web portal / dashboard for comprehensive underwriting review.

    Use this when the user wants to ACCESS the auto-approval dashboard or portal itself,
    e.g.:
    - "I want to access the auto approval dashboard"
    - "open the auto approval portal"
    - "take me to the auto approval dashboard"
    - "I want to see the full approval dashboard"
    - "show me the auto approval portal"
    - "open the underwriting portal"
    - "I want to log into the approval system"
    - "give me the auto approval link"
    - "access the approval dashboard for loan 123456789"

    Do NOT use this for:
    - Running an instant approval check → use check_loan_approval instead
    - Uploading a document → use get_upload_url instead
    - Speaking with a virtual agent → use get_virtual_agent_link instead
    """
    loan_line = f"**Loan:** `{loan_id}`\n\n" if loan_id.strip() else ""
    return (
        "## 🖥️ AUTO-APPROVAL PORTAL\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{loan_line}"
        "Access the full underwriting dashboard to run comprehensive approval reviews,\n"
        "manage documents, and view detailed scoring history.\n\n"
        "---\n\n"
        f"### [→ Log in to the Auto-Approval Portal]({_PORTAL_URL})\n\n"
        f"`{_PORTAL_URL}`\n\n"
        "---\n\n"
        "**What you can do in the portal:**\n\n"
        "- Run thorough title and insurance approval reviews\n"
        "- View full rule-by-rule scoring breakdowns\n"
        "- Manage uploaded documents for multiple loans\n"
        "- Export approval reports and audit trails\n"
        "- Escalate loans for manual underwriter review\n"
    )
