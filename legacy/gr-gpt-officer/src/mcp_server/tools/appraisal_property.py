from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal


@mcp.tool()
def get_property_and_appraisal(loan_id: str) -> str:
    """
    Return appraisal status, property value, LTV, AUS waiver, flood zone, and title/HOA flags.

    Use this when an LO asks about a property or appraisal, e.g.:
    - "What is the current appraisal status for the property at [Address]?"
    - "Show me the appraised value and LTV for file #[XXXXX]."
    - "Is the appraisal on file #[XXXXX] flagged for review by underwriting?"
    - "Has the appraisal waiver (AUS waiver) been approved for file #[XXXXX]?"
    - "What is the flood zone designation for the property at [Address]?"
    - "Are there any active HOA issues or title flags on file #[XXXXX]?"

    Do NOT use this for:
    - Borrower profile → use get_lo_borrower_profile
    - Compliance status → use get_loan_compliance_status
    - Closing logistics → use get_closing_and_funding_status
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`."
        )

    borrower = item.get("borrower_name", "—")
    cl = item.get("closing", {})
    property_location = cl.get("location", "—")

    ap = item.get("appraisal", {})
    if not ap:
        return (
            f"## 🏡 Property & Appraisal — #{loan_id}\n\n"
            f"No appraisal data on file for this loan. Appraisal may not have been ordered yet.\n"
        )

    status = ap.get("status", "—")
    amc = ap.get("amc", "—")
    ordered = ap.get("ordered_date", "—")
    insp_date = ap.get("inspection_date", "—")
    insp_time = ap.get("inspection_time", "—")
    report_received = ap.get("report_received_date") or "Pending"
    value = ap.get("value")
    ltv = ap.get("ltv")
    meets_price = ap.get("meets_purchase_price")
    waiver = ap.get("waiver_approved", False)
    flagged = ap.get("flagged", False)
    flag_reason = ap.get("flag_reason", "—")
    flood_zone = ap.get("flood_zone", "—")

    value_section = ""
    if value:
        meets_str = "✅ Yes" if meets_price else "⚠️ Below contract price — discuss with borrower and underwriter"
        value_section = (
            "\n### 💰 Appraisal Results\n\n"
            "| Field | Value |\n"
            "|---|---|\n"
            f"| **Appraised Value** | ${float(value):,.0f} |\n"
            f"| **LTV** | {ltv}% |\n"
            f"| **Meets Contract Price** | {meets_str} |\n"
        )

    flag_section = ""
    if flagged:
        flag_section = (
            "\n### 🔴 UW Appraisal Flag\n\n"
            f"Underwriting has flagged this appraisal for review:\n\n"
            f"> _{flag_reason}_\n\n"
            "Action required: Resolve with underwriter before advancing file.\n"
        )

    waiver_section = ""
    if waiver:
        waiver_section = "\n### ✅ Appraisal Waiver\n\nAUS appraisal waiver **approved** (DU/LP). No in-person inspection required.\n"
    else:
        waiver_section = "\n### 📋 Appraisal Waiver\n\nNo AUS waiver approved — standard appraisal required.\n"

    return (
        f"## 🏡 PROPERTY & APPRAISAL — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Borrower:** {borrower}\n\n"
        "### 📋 Appraisal Details\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Status** | {status} |\n"
        f"| **AMC** | {amc} |\n"
        f"| **Ordered Date** | {ordered} |\n"
        f"| **Inspection** | {insp_date} at {insp_time} |\n"
        f"| **Report Received** | {report_received} |\n"
        f"| **Flood Zone** | {flood_zone} |\n"
        f"{value_section}"
        f"{flag_section}"
        f"{waiver_section}"
        "\n### 🏘️ Title & HOA\n\n"
        "_Title and HOA data are not yet flagged in this demo. "
        "Integration with Title/HOA API is a production follow-on._\n"
    )
