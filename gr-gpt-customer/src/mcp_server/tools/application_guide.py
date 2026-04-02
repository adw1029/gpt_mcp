from mcp_server.registry import mcp

_APPLY_URL = "https://avatar.prajnagpt.net/"
_FIND_LO_URL = "https://www.rate.com/find-a-loan-officer"
_VIRTUAL_AGENT_URL = "https://avatar.prajnagpt.net"

_STAGES = [
    ("1", "Application", "Submit your application online or with a loan officer. Takes ~20–30 minutes."),
    ("2", "Processing", "Your processor verifies documents and orders appraisal, title, and insurance."),
    ("3", "Underwriting", "An underwriter reviews your full file and makes a credit decision. 3–7 business days."),
    ("4", "Conditional Approval", "Approved with conditions — typically document items or clarifications needed."),
    ("5", "Clear to Close (CTC)", "All conditions satisfied. Loan docs are ordered and closing is scheduled."),
    ("6", "Closing", "Sign loan documents with a title company or notary. Funds are disbursed."),
    ("7", "Funded / Recorded", "Wire sent, deed recorded. You're a homeowner!"),
]


@mcp.tool()
def get_application_guide() -> str:
    """
    Return a complete guide for starting a mortgage application with Rate.

    Use this when a borrower asks about the application or pre-approval process, e.g.:
    - "How do I start my mortgage application with Rate?"
    - "Can I apply online or do I need to meet someone in person?"
    - "How long does the application process take?"
    - "I want to get pre-approved — what is the first step?"
    - "Can you connect me with a loan officer near me?"
    - "What is the difference between pre-qualification and pre-approval?"
    - "What documents do I need to apply?"

    Do NOT use this for:
    - Rate quotes → use get_rate_quote
    - Eligibility checks → use check_borrower_eligibility
    - Existing loan status → use get_loan_status
    """
    stages_table = "\n".join(
        f"| **Stage {n}** | {name} | {desc} |"
        for n, name, desc in _STAGES
    )

    return (
        "## 🚀 HOW TO APPLY FOR A MORTGAGE WITH RATE\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### ✅ Step 1: Choose Your Path\n\n"
        "| Option | Best For | How |\n"
        "|---|---|---|\n"
        f"| **Apply Online** | Self-starters who know what they want | [{_APPLY_URL}]({_APPLY_URL}) — takes ~20 min |\n"
        f"| **Work with a Loan Officer** | First-time buyers or complex situations | [{_FIND_LO_URL}]({_FIND_LO_URL}) |\n"
        f"| **Chat with Virtual Agent** | Questions before you apply | [{_VIRTUAL_AGENT_URL}]({_VIRTUAL_AGENT_URL}) |\n"
        "\n---\n\n"
        "### 📋 Step 2: What You'll Need to Apply\n\n"
        "**Income & Employment:**\n"
        "- Last 2 years W-2s (or 1099s / tax returns if self-employed)\n"
        "- Most recent 30-day pay stubs\n"
        "- For self-employed: 2 years personal + business tax returns + YTD P&L\n\n"
        "**Assets:**\n"
        "- Last 2 months bank statements (all accounts)\n"
        "- Investment / retirement account statements\n"
        "- Gift letter (if down payment is a gift)\n\n"
        "**Property:**\n"
        "- Signed purchase contract (for purchases)\n"
        "- Current mortgage statement (for refinances)\n"
        "- Homeowners insurance quote\n\n"
        "**Identity:**\n"
        "- Government-issued photo ID\n"
        "- Social Security Number (for credit pull authorization)\n\n"
        "---\n\n"
        "### 🗺️ The Mortgage Process — 7 Stages\n\n"
        "| Stage | Name | What Happens |\n"
        "|---|---|---|\n"
        f"{stages_table}\n\n"
        "**Typical timeline:** 21–45 days from application to closing, depending on loan type and property.\n\n"
        "---\n\n"
        "### 🔍 Pre-Qualification vs. Pre-Approval\n\n"
        "| | Pre-Qualification | Pre-Approval |\n"
        "|---|---|---|\n"
        "| **Credit Pull** | Soft (no impact) | Hard (small impact) |\n"
        "| **Income Verified** | Self-reported | Document-verified |\n"
        "| **Seller Weight** | Low | High — sellers take offers more seriously |\n"
        "| **How Long** | Minutes | 1–2 business days |\n"
        "| **Best For** | Exploring options | Ready to make offers |\n\n"
        "> 💡 **Rate recommends starting with Pre-Approval** — it gives you a firm budget "
        "and makes your offers competitive in today's market.\n\n"
        "---\n\n"
        f"**Ready to get started?** → [Begin your application]({_APPLY_URL})  \n"
        f"**Find a loan officer near you** → [LO Locator]({_FIND_LO_URL})\n"
    )
