from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal

_VIRTUAL_AGENT_URL = "https://avatar.prajnagpt.net"


@mcp.tool()
def get_loan_officer_contact(loan_id: str) -> str:
    """
    Return loan officer contact information, scheduling link, document upload portal, and escalation path.

    Use this when a borrower asks about contacting their loan officer or support, e.g.:
    - "Who is my loan officer and how do I reach them?"
    - "Can I schedule a call with my loan officer?"
    - "How do I send documents securely?"
    - "I need to update my phone number or email — how do I do that?"
    - "Can someone explain the terms on my Loan Estimate?"
    - "I have a concern — who do I contact?"
    - "Connect me with a loan officer"
    - "I want to speak with a live agent"

    Do NOT use this for:
    - Conditions or document checklist → use get_conditions_checklist
    - Loan status → use get_loan_status
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`.\n\n"
            f"If you'd like to connect with a loan officer without a loan ID, "
            f"visit our [LO locator](https://www.rate.com/find-a-loan-officer) "
            f"or [chat with our virtual agent]({_VIRTUAL_AGENT_URL})."
        )

    lo = item.get("loan_officer", {})
    if not lo:
        return (
            f"## 📞 Contact — #{loan_id}\n\n"
            "Loan officer assignment not yet on file.\n\n"
            f"In the meantime, [chat with our virtual agent]({_VIRTUAL_AGENT_URL}) "
            "for immediate assistance."
        )

    name = lo.get("name", "Your Loan Officer")
    phone = lo.get("phone", "—")
    email = lo.get("email", "—")
    calendar = lo.get("calendar_link", "—")
    upload_link = lo.get("upload_portal_link", "https://docs.rate.com")
    escalation = lo.get("escalation_contact", "Contact Rate customer service at 1-800-RATE-COM")

    calendar_line = (
        f"[📅 Schedule a call with {name}]({calendar})"
        if calendar and calendar != "—" else
        f"Call or email {name} directly to schedule a call."
    )

    return (
        f"## 📞 LOAN OFFICER CONTACT — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"### 👤 {name}\n\n"
        "| | |\n"
        "|---|---|\n"
        f"| 📱 **Phone** | {phone} |\n"
        f"| 📧 **Email** | [{email}](mailto:{email}) |\n"
        f"| 📅 **Schedule a Call** | {calendar_line} |\n"
        "\n---\n\n"
        "### 📤 Upload Documents Securely\n\n"
        f"[{upload_link}]({upload_link})\n\n"
        "Documents uploaded here are transmitted via encrypted connection and stored securely.\n\n"
        "---\n\n"
        "### ✏️ Update Your Contact Information\n\n"
        f"To update your phone number or email address, contact {name} directly "
        "by phone or email. Include your loan ID in the subject line.\n\n"
        "---\n\n"
        "### 🚨 Escalation\n\n"
        f"If you have an urgent concern or are unable to reach {name}:\n\n"
        f"_{escalation}_\n\n"
        "---\n\n"
        f"### 💬 24/7 Virtual Agent\n\n"
        f"For immediate help at any time: [{_VIRTUAL_AGENT_URL}]({_VIRTUAL_AGENT_URL})\n"
    )
