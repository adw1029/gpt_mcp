from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal


@mcp.tool()
def get_closing_status(loan_id: str) -> str:
    """
    Return full closing and funding details — date, cash-to-close, CD status, funding, wire, and deed.

    Use this when a borrower asks about their closing or funding, e.g.:
    - "When is my closing appointment and where is it?"
    - "How much do I need to bring to closing?"
    - "Can I review my Closing Disclosure before the appointment?"
    - "What forms of payment are accepted at closing?"
    - "Has my loan funded yet?"
    - "When do I make my first mortgage payment?"
    - "When is my closing date?"
    - "Has my Closing Disclosure been sent?"
    - "Have I acknowledged receipt of my Closing Disclosure?"
    - "Are all my closing conditions cleared?"
    - "Has my loan funded yet?"
    - "Has the closing agent received the wire from Rate?"
    - "When will the deed be recorded?"

    Do NOT use this for:
    - Rate lock information → use get_rate_lock_status
    - Conditions checklist → use get_conditions_checklist
    - Servicing / first payment details → use get_servicing_info
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`. Please check your loan ID."
        )

    cl = item.get("closing", {})
    if not cl:
        return (
            f"## 📅 Closing — #{loan_id}\n\n"
            "Closing details are not yet available. Your loan may still be in early processing.\n\n"
            "Use `get_loan_status` to check your current stage."
        )

    date = cl.get("date", "TBD")
    time_ = cl.get("time", "TBD")
    location = cl.get("location", "TBD")
    attorney = cl.get("attorney", "N/A")
    title_co = cl.get("title_company", "—")
    ctc = cl.get("cash_to_close")
    cd_sent = cl.get("cd_sent_date")
    cd_ack = cl.get("cd_acknowledged", False)
    cd_ack_at = cl.get("cd_acknowledged_at", "—")
    ctc_issued = cl.get("ctc_issued", False)
    funded = cl.get("funded", False)
    funded_at = cl.get("funded_at")
    wire_confirmed = cl.get("wire_confirmed", False)
    wire_amount = cl.get("wire_amount")
    deed = cl.get("deed_recording_status", "Pending")
    first_payment = cl.get("first_payment_date", "—")
    payment_methods = cl.get("accepted_payment_methods", "Cashier's check or wire transfer")

    funded_section = ""
    if funded:
        funded_section = (
            "\n### 🎉 Loan Funded!\n\n"
            f"**Funded:** {str(funded_at or '—').replace('T', ' at ').replace('Z', ' UTC')}\n"
            + (f"**Wire confirmed:** ${float(wire_amount):,.0f} received by {title_co}\n" if wire_confirmed and wire_amount else "")
            + f"**Deed recording:** {deed}\n"
            + f"**First mortgage payment due:** {first_payment}\n"
        )
    else:
        cd_section = ""
        if cd_sent:
            cd_section += f"**CD sent:** {cd_sent} — 3-business-day waiting period\n"
            cd_section += f"**CD acknowledged:** {'✅ Yes — ' + str(cd_ack_at).replace('T', ' at ').replace('Z', ' UTC') if cd_ack else '⏳ Awaiting acknowledgment via DocuSign'}\n"
        else:
            cd_section += "**Closing Disclosure:** Not yet sent. CD will be sent at least 3 business days before closing.\n"

        ctc_section = (
            "\n✅ **Clear to Close (CTC) has been issued.** All conditions are cleared.\n"
            if ctc_issued else
            "\n⏳ **CTC not yet issued.** Outstanding conditions must be cleared before CTC.\n"
        )

        funded_section = (
            f"\n### 📄 Closing Disclosure\n\n{cd_section}"
            f"{ctc_section}"
        )

    ctc_display = f"**${float(ctc):,.0f}**" if ctc else "TBD — will be confirmed in your Closing Disclosure"

    return (
        f"## 📅 CLOSING STATUS — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### 🗓️ Closing Appointment\n\n"
        "| Field | Details |\n"
        "|---|---|\n"
        f"| **Date** | {date} |\n"
        f"| **Time** | {time_} |\n"
        f"| **Location** | {location} |\n"
        f"| **Title Company** | {title_co} |\n"
        + (f"| **Closing Attorney** | {attorney} |\n" if attorney and attorney != "N/A" else "")
        + f"\n---\n\n"
        "### 💵 Cash to Close\n\n"
        f"**Estimated amount needed:** {ctc_display}\n\n"
        f"**Accepted payment forms:** {payment_methods}\n\n"
        "> 💡 Bring a cashier's check made out to the title company, or arrange a wire transfer. "
        "Personal checks and cash are typically not accepted.\n"
        f"{funded_section}"
        "\n---\n\n"
        f"**First mortgage payment due:** {first_payment}\n"
    )
