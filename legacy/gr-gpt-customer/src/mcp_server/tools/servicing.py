from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal


@mcp.tool()
def get_servicing_info(loan_id: str) -> str:
    """
    Return post-closing servicing information — first payment, servicer, autopay, and refinance opportunity.

    Use this when a borrower asks about their mortgage servicer or post-closing, e.g.:
    - "When is my first mortgage payment due?"
    - "Who will be servicing my loan after closing?"
    - "Has my loan been transferred to a new servicer?"
    - "Can I set up autopay for my mortgage?"
    - "Am I eligible to refinance at today's rates?"
    - "When do I make my first mortgage payment?"

    Do NOT use this for:
    - Closing details → use get_closing_status
    - Escrow breakdown → use get_escrow_and_insurance
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`. Please check your loan ID."
        )

    svc = item.get("servicing", {})
    if not svc:
        return (
            f"## 🏦 Servicing Info — #{loan_id}\n\n"
            "Servicing details will be available after your loan closes and funds.\n\n"
            "Use `get_loan_status` to check your current stage."
        )

    first_payment = svc.get("first_payment_date", "—")
    servicer = svc.get("servicer", "—")
    autopay_link = svc.get("autopay_link")
    transfer_pending = svc.get("transfer_pending", False)
    transfer_servicer = svc.get("transfer_servicer")
    transfer_date = svc.get("transfer_effective_date")
    refi_savings = svc.get("refi_savings_monthly", 0)
    refi_rate = svc.get("refi_rate_available")

    transfer_section = ""
    if transfer_pending and transfer_servicer:
        transfer_section = (
            "\n### 🔄 Servicing Transfer\n\n"
            f"⚠️ **Your loan is being transferred to a new servicer.**\n\n"
            "| Field | Value |\n"
            "|---|---|\n"
            f"| **New Servicer** | {transfer_servicer} |\n"
            f"| **Transfer Effective** | {transfer_date or 'TBD'} |\n\n"
            "You will receive a Welcome Letter from the new servicer with login details. "
            "Continue making payments to your current servicer until the transfer date.\n"
        )
    else:
        transfer_section = (
            "\n### 🔄 Servicing Transfer\n\n"
            "✅ No transfer pending — your loan will remain with the servicer listed above.\n"
        )

    refi_section = ""
    if refi_savings and float(refi_savings) > 0:
        refi_section = (
            "\n### 💡 Refinance Opportunity\n\n"
            f"Current market rates suggest you could save approximately "
            f"**${float(refi_savings):,.0f}/month** by refinancing now"
            + (f" at **{refi_rate}%**" if refi_rate else "") + ".\n\n"
            "Speak with your loan officer to run a full refinance analysis — "
            "including break-even timeline, closing costs, and long-term savings.\n"
        )

    autopay_section = ""
    if autopay_link:
        autopay_section = (
            f"\n### ⚡ Set Up Autopay\n\n"
            f"Enroll in autopay to never miss a payment: [{autopay_link}]({autopay_link})\n\n"
            "Many servicers offer a rate discount (0.25%) for autopay enrollment.\n"
        )

    return (
        f"## 🏦 SERVICING INFO — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### 📅 Payment Details\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **First Payment Due** | {first_payment} |\n"
        f"| **Loan Servicer** | {servicer} |\n\n"
        "> 💡 Your first mortgage payment is typically due on the 1st of the month that is "
        "**two months after closing**. For example, if you close in March, your first payment "
        "is due May 1st.\n"
        f"{autopay_section}"
        f"{transfer_section}"
        f"{refi_section}"
    )
