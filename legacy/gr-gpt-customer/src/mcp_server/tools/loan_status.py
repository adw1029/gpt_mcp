from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal

_STAGE_ICONS = {
    1: "📝", 2: "⚙️", 3: "🔍", 4: "🟡", 5: "✅", 6: "🏠", 7: "🎉",
}

_UW_ICONS = {
    "Conditional": "🟡",
    "Approved": "✅",
    "Clear to Close": "✅",
    "Denied": "🔴",
    "Suspended": "🔴",
    "None": "⏳",
}


@mcp.tool()
def get_loan_status(loan_id: str) -> str:
    """
    Return the current live status of a mortgage application by loan ID.

    Use this when a borrower asks about their application status, e.g.:
    - "What is the current status of my loan application?"
    - "Has my loan been approved?"
    - "What stage is my loan in right now?"
    - "Is my loan in conditional approval? What are the open conditions?"
    - "Has underwriting cleared my file yet?"
    - "What is the expected timeline to get a final approval decision?"
    - "Have there been any recent updates to my file in the last 48 hours?"
    - "Who is currently reviewing my file?"

    Do NOT use this for:
    - Document checklist details → use get_conditions_checklist
    - Rate lock information → use get_rate_lock_status
    - Closing details → use get_closing_status
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No loan record found for `{loan_id}`.\n\n"
            "Please verify your loan ID and try again. Your loan ID appears on your Loan Estimate "
            "and any correspondence from Rate."
        )

    stage = item.get("loan_stage", "Unknown")
    stage_num = int(item.get("stage_number", 0))
    uw_decision = item.get("uw_decision", "None")
    underwriter = item.get("assigned_underwriter", "Not yet assigned")
    borrower = item.get("borrower_name", "—")

    stage_icon = _STAGE_ICONS.get(stage_num, "🔄")
    uw_icon = _UW_ICONS.get(uw_decision, "⏳")

    stage_bar = ""
    for i in range(1, 8):
        if i < stage_num:
            stage_bar += "🟩"
        elif i == stage_num:
            stage_bar += "🟨"
        else:
            stage_bar += "⬜"

    open_conditions = item.get("open_conditions", [])
    open_count = sum(1 for c in open_conditions if str(c.get("status", "")).lower() not in ("accepted", "waived", "satisfied"))

    updates = item.get("recent_updates", [])
    updates_section = ""
    if updates:
        updates_section = "\n### 📋 Recent Activity (Last 48 Hours)\n\n"
        for u in updates[:4]:
            updates_section += f"- **{u.get('date', '—')}** — {u.get('description', '—')}\n"
    else:
        updates_section = "\n### 📋 Recent Activity\n\n_No recent updates on file._\n"

    timeline_note = {
        1: "Application received. Processing begins within 1 business day.",
        2: "Processing in progress — appraisal, title, and insurance being ordered. Typically 3–5 days.",
        3: "File in underwriting review. Typical decision time: 3–7 business days.",
        4: "Conditional Approval issued. Clear open conditions to advance to CTC.",
        5: "Clear to Close! Closing docs being prepared. Expect closing within 3–5 days.",
        6: "Closing complete. Awaiting funding and deed recording.",
        7: "Loan funded and recorded. Congratulations!",
    }.get(stage_num, "Contact your loan officer for a timeline estimate.")

    return (
        f"## 📊 LOAN STATUS — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Borrower:** {borrower}\n\n"
        f"### {stage_icon} Stage {stage_num} of 7 — {stage}\n\n"
        f"{stage_bar}  _(Stage {stage_num}/7)_\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Loan Stage** | {stage_icon} {stage} |\n"
        f"| **UW Decision** | {uw_icon} {uw_decision} |\n"
        f"| **Assigned Underwriter** | {underwriter} |\n"
        f"| **Open Conditions** | {'⚠️ ' + str(open_count) + ' outstanding' if open_count > 0 else '✅ None outstanding'} |\n"
        "\n---\n\n"
        f"### ⏱️ What Happens Next\n\n_{timeline_note}_\n"
        f"{updates_section}"
        "\n---\n\n"
        "> _For condition details: ask for your **conditions checklist**. "
        "For closing details: ask for your **closing status**._\n"
    )
