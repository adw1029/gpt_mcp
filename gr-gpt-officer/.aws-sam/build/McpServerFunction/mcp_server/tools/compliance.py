from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal


@mcp.tool()
def get_loan_compliance_status(loan_id: str) -> str:
    """
    Return full compliance and disclosure status for a loan — TRID, RESPA, HMDA, Fair Lending, and audit trail.

    Use this when an LO needs compliance details, e.g.:
    - "Has the Loan Estimate been sent for file #[XXXXX]? What was the sent date?"
    - "Is the Closing Disclosure on file #[XXXXX] within the required 3-day window?"
    - "Which loans are approaching RESPA or TRID deadline violations?"
    - "Show me all loans missing required Fair Lending disclosures."
    - "Has the Right of Rescission period expired for file #[XXXXX]?"
    - "Pull the audit trail for all disclosures sent on file #[XXXXX]."
    - "Are there any active HMDA flags or reporting issues in my pipeline?"

    Do NOT use this for:
    - Pipeline overview → use get_lo_pipeline
    - Borrower profile → use get_lo_borrower_profile
    - Closing logistics → use get_closing_and_funding_status
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`."
        )

    comp = item.get("compliance", {})
    borrower = item.get("borrower_name", "—")
    stage = item.get("loan_stage", "—")

    le_sent = comp.get("le_sent_date", "—") or "⚠️ NOT YET SENT"
    cd_sent = comp.get("cd_sent_date") or "Not yet sent"
    trid_ok = comp.get("trid_window_ok", True)
    trid_days = comp.get("trid_days_remaining")
    respa_flags = comp.get("respa_flags", [])
    rescission_expiry = comp.get("right_of_rescission_expiry")
    hmda_flags = comp.get("hmda_flags", [])
    fl_gaps = comp.get("fair_lending_gaps", [])
    audit_trail = comp.get("disclosure_audit_trail", [])

    trid_status = "✅ OK"
    trid_note = ""
    if not trid_ok:
        trid_status = "🔴 VIOLATION RISK"
        trid_note = "\n> 🚨 **TRID violation risk detected.** CD must be received by borrower at least 3 business days before closing. Review immediately.\n"
    elif trid_days is not None and int(trid_days) <= 1:
        trid_status = f"⚠️ {int(trid_days)} business day(s) remaining"
        trid_note = "\n> ⚠️ CD waiting period is nearly expired. Confirm borrower has acknowledged before scheduling closing.\n"

    respa_section = ""
    if respa_flags:
        respa_section = "\n### ⚠️ RESPA Flags\n\n" + "\n".join(f"- {f}" for f in respa_flags) + "\n"
    else:
        respa_section = "\n### ✅ RESPA\n\n_No RESPA flags identified._\n"

    hmda_section = ""
    if hmda_flags:
        hmda_section = "\n### 🔴 HMDA Flags\n\n" + "\n".join(f"- {f}" for f in hmda_flags) + "\n"
    else:
        hmda_section = "\n### ✅ HMDA\n\n_No HMDA reporting issues._\n"

    fl_section = ""
    if fl_gaps:
        fl_section = "\n### ⚠️ Fair Lending Gaps\n\n" + "\n".join(f"- {f}" for f in fl_gaps) + "\n"
    else:
        fl_section = "\n### ✅ Fair Lending\n\n_No Fair Lending disclosure gaps identified._\n"

    rescission_section = ""
    if rescission_expiry:
        rescission_section = (
            f"\n### ⏱️ Right of Rescission\n\n"
            f"Applicable for this refinance. Rescission period expires: **{rescission_expiry}**\n"
        )

    audit_section = "\n### 📜 Disclosure Audit Trail\n\n"
    if audit_trail:
        audit_section += "| Date | Document | Action |\n|---|---|---|\n"
        for entry in audit_trail:
            audit_section += f"| {entry.get('date', '—')} | {entry.get('document', '—')} | {entry.get('action', '—')} |\n"
    else:
        audit_section += "_No disclosure events on record._\n"

    return (
        f"## ✅ COMPLIANCE STATUS — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Borrower:** {borrower}  |  **Stage:** {stage}\n\n"
        "### 📋 Disclosure Tracking\n\n"
        "| Disclosure | Status |\n"
        "|---|---|\n"
        f"| **Loan Estimate (LE) Sent** | {le_sent} |\n"
        f"| **Closing Disclosure (CD) Sent** | {cd_sent} |\n"
        f"| **TRID 3-Day Window** | {trid_status} |\n"
        f"{trid_note}"
        f"{respa_section}"
        f"{hmda_section}"
        f"{fl_section}"
        f"{rescission_section}"
        f"{audit_section}"
    )
