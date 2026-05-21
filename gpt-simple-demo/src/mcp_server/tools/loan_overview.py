from mcp_server.registry import mcp
from mcp_server.utils.dynamo import lookup_loan_dynamo

_STATUS_EMOJI = {
    "In Progress": "🟡",
    "Approved": "🟢",
    "Submitted": "🔵",
    "Closed": "⚫",
    "Denied": "🔴",
}


@mcp.tool()
def get_loan_overview(loan_identifier: str) -> str:
    """
    Look up raw loan data fields for a specific loan by ID or GUID.

    Returns structured fields only: buyer names, state, property address,
    property type, property county, parcel number, base loan amount, loan
    purpose, loan status, organization, and assigned loan officer.

    Use this ONLY when the user wants specific data fields from a loan record,
    e.g.:
    - "what is the loan amount for loan 265561631?"
    - "who is the loan officer on loan 265561631?"
    - "what state is loan 265561631 in?"
    - "look up the property address for loan 265561631"
    - "what is the status of loan 265561631?"

    Do NOT use this for:
    - Full briefings or analysis → use get_loan_intelligence_report instead
    - Approval checks → use check_loan_approval instead
    - Borrower/client background → use get_client_profile instead
    - OneLoan document data → use lookup_loan_document_extraction instead
    """
    item = lookup_loan_dynamo(loan_identifier)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No loan record found for `{loan_identifier}`. "
            "Please verify the loan ID and try again."
        )

    amount = float(item.get("base_loan_amount", 0))
    status_raw = str(item.get("loan_status", "Unknown"))
    status_icon = _STATUS_EMOJI.get(status_raw, "⚪")
    org = str(item.get("organization", "N/A")).upper()

    risk_flags = item.get("risk_flags", [])
    flags_line = (
        "  None identified"
        if not risk_flags
        else "\n".join(f"⚠️ {f}" for f in risk_flags)
    )

    return (
        f"## 🏦 LOAN OVERVIEW — #{loan_identifier}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "| Field | Details |\n"
        "|---|---|\n"
        f"| 🏠 **Property** | {item.get('property_address', 'N/A')} |\n"
        f"| 💰 **Loan Amount** | ${amount:,.0f} |\n"
        f"| 📋 **Purpose** | {item.get('loan_purpose', 'N/A')} |\n"
        f"| 📊 **Status** | {status_icon} {status_raw} |\n"
        f"| 👤 **Borrower** | {item.get('buyer_names', 'N/A')} |\n"
        f"| 🏢 **Loan Officer** | {item.get('loan_officer', 'N/A')} |\n"
        f"| 🏛️ **Organization** | {org} |\n"
        f"| 🗺️ **State** | {item.get('state', 'N/A')} |\n"
        f"| 📍 **County** | {item.get('property_county', 'N/A')} |\n"
        f"| 🏷️ **Property Type** | {item.get('property_type', 'N/A')} |\n"
        f"| 🔢 **Parcel Number** | {item.get('parcel_number', 'N/A')} |\n"
        f"| 🏘️ **Seller** | {item.get('seller_names', 'N/A')} |\n"
        "\n---\n\n"
        "### ⚠️ Risk Flags\n"
        f"{flags_line}\n"
    )
