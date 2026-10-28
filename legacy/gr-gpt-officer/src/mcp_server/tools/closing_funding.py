from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal


@mcp.tool()
def get_closing_and_funding_status(loan_id: str) -> str:
    """
    Return the complete closing and funding status for a loan — LO internal view.

    Use this when an LO asks about closing or funding, e.g.:
    - "What is the confirmed closing date and time for file #[XXXXX]?"
    - "Has the wire been confirmed for the closing of file #[XXXXX]?"
    - "Who is the closing attorney / title company on file #[XXXXX]?"
    - "Are all closing conditions cleared for file #[XXXXX]?"
    - "What is the final cash-to-close amount for borrower [Name]?"
    - "Show me the closing cost breakdown for file #[XXXXX]."
    - "Has the Closing Disclosure been acknowledged by the borrower?"

    Do NOT use this for:
    - Compliance/TRID details → use get_loan_compliance_status
    - Pipeline overview → use get_lo_pipeline
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`."
        )

    borrower = item.get("borrower_name", "—")
    stage = item.get("loan_stage", "—")
    cl = item.get("closing", {})
    comp = item.get("compliance", {})
    escrow = item.get("escrow", {})

    if not cl:
        return (
            f"## 📅 Closing & Funding — #{loan_id}\n\n"
            "No closing data on file. Loan may still be in early stages."
        )

    date = cl.get("date", "TBD")
    time_ = cl.get("time", "TBD")
    location = cl.get("location", "—")
    attorney = cl.get("attorney")
    title_co = cl.get("title_company", "—")
    ctc = cl.get("cash_to_close")
    ctc_issued = cl.get("ctc_issued", False)
    cd_sent = comp.get("cd_sent_date", "Not yet sent")
    cd_ack = cl.get("cd_acknowledged", False)
    cd_ack_at = cl.get("cd_acknowledged_at", "—")
    funded = cl.get("funded", False)
    funded_at = cl.get("funded_at")
    wire_confirmed = cl.get("wire_confirmed", False)
    wire_amount = cl.get("wire_amount")
    deed = cl.get("deed_recording_status", "Pending")

    monthly_escrow = escrow.get("monthly_escrow", 0)
    pmi = escrow.get("pmi_monthly", 0)
    tax = escrow.get("property_tax_monthly", 0)
    hoi = escrow.get("hoi_monthly", 0)

    conditions = item.get("open_conditions", [])
    open_count = sum(1 for c in conditions if str(c.get("status", "")).lower() not in ("accepted", "waived", "satisfied"))
    ctc_display = "✅ CTC Issued" if ctc_issued else f"⏳ Pending — {open_count} condition(s) outstanding"

    funded_section = ""
    if funded:
        funded_section = (
            "\n### 🎉 Funding Confirmed\n\n"
            "| Field | Value |\n"
            "|---|---|\n"
            f"| **Funded At** | {str(funded_at or '—').replace('T', ' ').replace('Z', ' UTC')} |\n"
            + (f"| **Wire Amount** | ${float(wire_amount):,.0f} |\n" if wire_amount else "")
            + f"| **Wire Confirmed** | {'✅ Yes' if wire_confirmed else '⏳ Pending'} |\n"
            + f"| **Deed Recording** | {deed} |\n"
        )
    else:
        funded_section = "\n### ⏳ Funding\n\n_Loan not yet funded._\n"

    return (
        f"## 📅 CLOSING & FUNDING — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Borrower:** {borrower}  |  **Stage:** {stage}\n\n"
        "### 🗓️ Closing Details\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Date & Time** | {date} at {time_} |\n"
        f"| **Location** | {location} |\n"
        f"| **Title Company** | {title_co} |\n"
        + (f"| **Closing Attorney** | {attorney} |\n" if attorney else "")
        + "\n---\n\n"
        "### 💵 Cash to Close & Conditions\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Cash to Close** | {'$' + f'{float(ctc):,.0f}' if ctc else 'TBD'} |\n"
        f"| **CTC Status** | {ctc_display} |\n"
        "\n---\n\n"
        "### 📄 Closing Disclosure\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **CD Sent** | {cd_sent} |\n"
        f"| **Borrower Acknowledged** | {'✅ Yes — ' + str(cd_ack_at).replace('T', ' ').replace('Z', ' UTC') if cd_ack else '⏳ No'} |\n"
        "\n---\n\n"
        "### 📊 Monthly Payment Breakdown (Post-Close)\n\n"
        "| Component | Monthly |\n"
        "|---|---|\n"
        f"| Property Tax | ${float(tax):,.0f} |\n"
        f"| Homeowners Insurance | ${float(hoi):,.0f} |\n"
        + (f"| PMI | ${float(pmi):,.0f} |\n" if float(pmi) > 0 else "")
        + f"| **Total Escrow** | **${float(monthly_escrow):,.0f}** |\n"
        f"{funded_section}"
    )
