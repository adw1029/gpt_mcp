import os
import urllib.parse

from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal

_UPLOAD_BASE = os.environ.get(
    "UPLOAD_PAGE_URL",
    "https://1gdypgoned.execute-api.us-east-2.amazonaws.com/upload",
)

_STATUS_ICONS = {
    "Outstanding": "🔴",
    "In Review": "🟡",
    "Accepted": "✅",
    "Waived": "✅",
    "Satisfied": "✅",
}

_TYPE_LABELS = {
    "PTD": "Prior to Doc",
    "PTF": "Prior to Funding",
    "general": "General",
}


@mcp.tool()
def get_conditions_checklist(loan_id: str) -> str:
    """
    Return the full conditions checklist — outstanding items, deadlines, and document status.

    Use this when a borrower asks about their conditions or documents, e.g.:
    - "What documents do I still need to submit?"
    - "How do I securely upload my pay stubs and bank statements?"
    - "Did you receive the documents I uploaded yesterday?"
    - "Why is the underwriter asking for [specific document]?"
    - "How long do I have to submit the outstanding conditions?"
    - "Is my income verification complete?"
    - "Show me my full conditions checklist right now."
    - "Have all my conditions been satisfied?"
    - "What is the deadline to submit my outstanding conditions?"
    - "Did my uploaded W-2s get reviewed and accepted?"
    - "Is there a new condition added to my file since I last checked?"
    - "Is my employment verification complete?"
    - "Are there any prior-to-doc (PTD) or prior-to-funding (PTF) conditions open?"

    Do NOT use this for:
    - Overall loan status → use get_loan_status
    - Closing details → use get_closing_status
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`. Please check your loan ID."
        )

    conditions = item.get("open_conditions", [])
    voe = item.get("voe_status", "—")
    voi = item.get("voi_status", "—")
    docs_submitted = item.get("documents_submitted", [])
    docs_missing = item.get("documents_missing", [])
    borrower_name = item.get("borrower_name", "")
    upload_link = (
        _UPLOAD_BASE
        + "?loan_id=" + urllib.parse.quote(loan_id)
        + "&borrower=" + urllib.parse.quote(borrower_name)
    )

    outstanding = [c for c in conditions if str(c.get("status", "")).lower() not in ("accepted", "waived", "satisfied")]
    accepted = [c for c in conditions if str(c.get("status", "")).lower() in ("accepted", "waived", "satisfied")]

    if not conditions:
        summary = "✅ **No open conditions.** Your file is clean — great news!\n"
    else:
        summary = (
            f"**{len(outstanding)} condition(s) outstanding** out of {len(conditions)} total.\n"
        )

    conditions_table = ""
    if outstanding:
        conditions_table += "\n### 🔴 Outstanding Conditions\n\n"
        conditions_table += "| ID | Description | Type | Deadline | Notes |\n"
        conditions_table += "|---|---|---|---|---|\n"
        for c in outstanding:
            ctype = _TYPE_LABELS.get(c.get("type", "general"), c.get("type", "—"))
            conditions_table += (
                f"| `{c.get('id', '—')}` | {c.get('description', '—')} "
                f"| {ctype} | {c.get('deadline', '—')} | _{c.get('notes', '—')}_ |\n"
            )

    in_review = [c for c in conditions if str(c.get("status", "")).lower() == "in review"]
    if in_review:
        conditions_table += "\n### 🟡 In Review\n\n"
        conditions_table += "| ID | Description | Type |\n"
        conditions_table += "|---|---|---|\n"
        for c in in_review:
            ctype = _TYPE_LABELS.get(c.get("type", "general"), c.get("type", "—"))
            conditions_table += f"| `{c.get('id', '—')}` | {c.get('description', '—')} | {ctype} |\n"

    if accepted:
        conditions_table += "\n### ✅ Accepted / Cleared\n\n"
        for c in accepted:
            conditions_table += f"- ✅ `{c.get('id', '—')}` — {c.get('description', '—')} _(Accepted {c.get('accepted_date', '')})_\n"

    docs_section = ""
    if docs_submitted:
        docs_section += "\n### 📁 Documents on File\n\n"
        docs_section += "\n".join(f"- ✅ {d}" for d in docs_submitted) + "\n"
    if docs_missing:
        docs_section += "\n### ⚠️ Still Needed\n\n"
        docs_section += "\n".join(f"- 🔴 {d}" for d in docs_missing) + "\n"

    return (
        f"## 📋 CONDITIONS CHECKLIST — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{summary}\n"
        f"{conditions_table}"
        f"{docs_section}"
        "\n---\n\n"
        "### 📊 Verification Status\n\n"
        "| Check | Status |\n"
        "|---|---|\n"
        f"| **Employment Verification (VOE)** | {voe} |\n"
        f"| **Income Verification (VOI)** | {voi} |\n"
        "\n---\n\n"
        "### 📤 Submit Your Documents\n\n"
        f"> **[Upload to your Rate loan file →]({upload_link})**\n\n"
        "No login required — drag and drop your PDF or photo directly on the page. "
        "Your processor will review within **1–2 business days** "
        "and you'll get an email confirmation once the condition is cleared.\n"
    )
