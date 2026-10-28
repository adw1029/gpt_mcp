import logging
from mcp_server.registry import mcp
from mcp_server.utils.docext import invoke_docext, DEFAULT_ORGS

logger = logging.getLogger(__name__)

_FIELD_LABELS = {
    "guid": ("🔑", "GUID"),
    "cx_eid": ("🏢", "CX Entity ID"),
    "state": ("🗺️", "State"),
    "loan_purpose_type": ("📋", "Loan Purpose"),
    "street_address": ("🏠", "Property Address"),
    "base_loan_amount": ("💰", "Loan Amount"),
    "cx_cc_ins_amt": ("🛡️", "CC Insurance Amount"),
    "extracted_buyer_names": ("👤", "Borrower Names"),
    "extracted_buyer_vesting": ("📜", "Vesting"),
    "extracted_seller_names": ("🤝", "Seller Names"),
    "extracted_property_type": ("🏷️", "Property Type"),
    "extracted_property_address": ("📍", "Property Address (extracted)"),
    "extracted_property_county": ("🏙️", "County"),
    "extracted_parcel_number": ("🔢", "Parcel Number"),
    "borrower_last_name": ("👤", "Borrower Last Name"),
}


@mcp.tool()
def lookup_loan_document_extraction(
    loan_identifier: str,
    organization: str = "",
    environment: str = "prod",
) -> str:
    """
    Fetch raw OneLoan document extraction data from the OneLoan system.

    Only use this when the user EXPLICITLY mentions "OneLoan" or the OneLoan
    system. Do NOT use this for general loan lookups — use get_loan_overview.

    CRITICAL PARAMETER RULES — follow exactly, do not invent values:
    - loan_identifier: the loan ID or GUID exactly as provided. Required.
    - organization: leave BLANK ("") unless the user explicitly names one.
      Valid values ONLY: "gri", "gra", "kbhs", "citywide", "op", "premia", "pr".
      Do NOT pass "default", "unknown", "all", or any invented string.
      When blank, the tool auto-searches all orgs in order.
    - environment: leave as default "prod" unless user explicitly says otherwise.
      Valid values ONLY: "prod", "staging", "dev".
      Do NOT pass "production", "default", or any alias — use "prod" exactly.

    Use this ONLY when the user explicitly mentions OneLoan, e.g.:
    - "get the OneLoan data for loan 265561631"
    - "look up loan 265561631 in OneLoan"
    - "what does OneLoan say about this loan?"
    - "pull the OneLoan extraction for this loan"
    - "show me the OneLoan record"

    Do NOT use this for:
    - General loan lookups → use get_loan_overview instead
    - Full briefings → use get_loan_intelligence_report instead
    - Approval checks → use check_loan_approval instead
    """
    org_normalized = organization.strip().lower()
    if org_normalized and org_normalized not in DEFAULT_ORGS:
        logger.warning("Unknown org '%s' passed — falling back to all orgs", org_normalized)
        org_normalized = ""
    orgs_to_try = [org_normalized] if org_normalized else DEFAULT_ORGS

    data = None
    matched_org = None
    for org in orgs_to_try:
        result = invoke_docext(loan_identifier, org, environment)
        if result:
            data = result
            matched_org = org
            break

    if not data:
        orgs_display = ", ".join(f"`{o}`" for o in orgs_to_try)
        return (
            f"## ❌ OneLoan Record Not Found\n\n"
            f"| Field | Value |\n"
            f"|---|---|\n"
            f"| **Loan ID** | `{loan_identifier}` |\n"
            f"| **Organizations searched** | {orgs_display} |\n"
            f"| **Environment** | `{environment}` |\n\n"
            "Verify the loan ID/GUID is correct. "
            "Valid org codes: `gri`, `gra`, `kbhs`, `citywide`, `op`, `premia`, `pr`."
        )

    org_display = matched_org.upper() if matched_org else "N/A"
    rows = []
    for key, (icon, label) in _FIELD_LABELS.items():
        val = str(data.get(key, "")).strip()
        if val:
            rows.append(f"| {icon} **{label}** | {val} |")

    # Any extra keys not in the label map
    known_keys = set(_FIELD_LABELS.keys()) | {"_matched_organization"}
    for key, val in data.items():
        if key not in known_keys and str(val).strip():
            rows.append(f"| **{key}** | {val} |")

    table = "\n".join(rows) if rows else "_No fields returned._"

    return (
        f"## 📄 ONELOAN RECORD — #{loan_identifier}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Organization:** `{org_display}` &nbsp;|&nbsp; **Environment:** `{environment}`\n\n"
        "---\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"{table}\n"
    )
