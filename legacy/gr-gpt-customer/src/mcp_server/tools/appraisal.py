from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal

_STATUS_ICONS = {
    "Ordered": "📋",
    "Inspection Scheduled": "📅",
    "Inspection Complete": "🔍",
    "Under Review": "🔍",
    "Accepted": "✅",
    "Flagged": "⚠️",
    "Waived": "✅",
}


@mcp.tool()
def get_appraisal_status(loan_id: str) -> str:
    """
    Return the current appraisal status for a loan, including value, LTV, and any flags.

    Use this when a borrower asks about their appraisal, e.g.:
    - "Has my appraisal been ordered yet?"
    - "What is the current status of my appraisal?"
    - "When is my appraisal inspection scheduled?"
    - "Has the appraisal report been received by Rate?"
    - "What did the property appraise for?"
    - "Did the appraisal come in at or above the purchase price?"
    - "Is an appraisal waiver available for my loan?"
    - "Is there a problem or flag on my appraisal?"

    Do NOT use this for:
    - Overall loan status → use get_loan_status
    - Conditions checklist → use get_conditions_checklist
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`. Please check your loan ID."
        )

    ap = item.get("appraisal", {})
    if not ap:
        return (
            f"## 📋 Appraisal — #{loan_id}\n\n"
            "No appraisal data is available for this loan yet. "
            "If your loan is in early processing, the appraisal may not have been ordered. "
            "Contact your loan officer for more details."
        )

    status = ap.get("status", "Unknown")
    icon = _STATUS_ICONS.get(status, "🔄")
    amc = ap.get("amc", "AMC")
    ordered = ap.get("ordered_date", "—")
    insp_date = ap.get("inspection_date", "—")
    insp_time = ap.get("inspection_time", "—")
    report_received = ap.get("report_received_date")
    value = ap.get("value")
    ltv = ap.get("ltv")
    meets_price = ap.get("meets_purchase_price")
    waiver = ap.get("waiver_approved", False)
    flagged = ap.get("flagged", False)
    flag_reason = ap.get("flag_reason", "—")
    flood_zone = ap.get("flood_zone", "—")

    value_section = ""
    if value:
        meets_str = "✅ Yes — appraised value meets or exceeds contract price." if meets_price else "⚠️ No — appraised value is below contract price. Discuss options with your loan officer."
        value_section = (
            "\n### 💰 Appraisal Results\n\n"
            "| Field | Value |\n"
            "|---|---|\n"
            f"| **Appraised Value** | ${float(value):,.0f} |\n"
            f"| **LTV** | {ltv}% |\n"
            f"| **Meets Purchase Price** | {meets_str} |\n"
        )

    flag_section = ""
    if flagged:
        flag_section = (
            "\n### ⚠️ Appraisal Flag\n\n"
            f"Your appraisal has been flagged for review by underwriting:\n\n"
            f"> _{flag_reason}_\n\n"
            "Your loan officer will reach out with next steps. This does not necessarily stop your loan.\n"
        )
    elif waiver:
        flag_section = (
            "\n### ✅ Appraisal Waiver Approved\n\n"
            "An appraisal waiver was approved via the automated underwriting system (DU/LP). "
            "No in-person inspection is required for your loan.\n"
        )

    report_section = ""
    if report_received:
        report_section = f"\n**Report received by Rate:** {report_received} — under review by underwriting.\n"
    elif insp_date and insp_date != "—":
        report_section = f"\n**Inspection scheduled:** {insp_date} at {insp_time} — report expected within 3–5 business days.\n"

    return (
        f"## 🏡 APPRAISAL STATUS — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### 📋 Appraisal Details\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Status** | {icon} {status} |\n"
        f"| **AMC** | {amc} |\n"
        f"| **Ordered Date** | {ordered} |\n"
        f"| **Inspection Date** | {insp_date} at {insp_time} |\n"
        f"| **Report Received** | {report_received or 'Pending'} |\n"
        f"| **Flood Zone** | {flood_zone} |\n"
        f"{report_section}"
        f"{value_section}"
        f"{flag_section}"
        "\n---\n\n"
        "_Questions about your appraisal? Contact your loan officer using `get_loan_officer_contact`._\n"
    )
