from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal


@mcp.tool()
def get_lo_borrower_profile(loan_id: str) -> str:
    """
    Return the full borrower profile for a loan — credit, income, assets, docs, co-borrowers, and history.

    Use this when an LO needs to look up borrower details, e.g.:
    - "Pull the full borrower profile for [Name] including credit, income, and assets."
    - "What is the current credit score on file for borrower [Name]?"
    - "Show me all co-borrowers linked to loan file #[XXXXX]."
    - "Has borrower [Name] had any recent credit inquiries in the past 90 days?"
    - "What documents has [Name] submitted so far and what is still missing?"
    - "Show me the employment and income verification status for [Name]."
    - "Has [Name] applied for a loan with Rate before? Show previous applications."

    Do NOT use this for:
    - Pipeline overview → use get_lo_pipeline
    - Compliance status → use get_loan_compliance_status
    - Appraisal details → use get_property_and_appraisal
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Borrower Not Found\n\n"
            f"No portal record found for loan `{loan_id}`.\n\n"
            "Verify the loan ID and confirm the borrower has been seeded in the BorrowerPortal table."
        )

    name = item.get("borrower_name", "—")
    stage = item.get("loan_stage", "—")
    credit = item.get("credit_score")
    inquiries = item.get("credit_inquiries_90d", 0)
    co_borrowers = item.get("co_borrowers", [])
    docs_submitted = item.get("documents_submitted", [])
    docs_missing = item.get("documents_missing", [])
    voe = item.get("voe_status", "—")
    voi = item.get("voi_status", "—")
    prior = item.get("prior_applications", [])
    pricing_ex = item.get("pricing_exceptions", [])

    credit_display = f"{int(credit)}" if credit else "Not on file"
    inquiry_flag = " ⚠️ Elevated" if int(inquiries) >= 3 else ""

    co_section = ""
    if co_borrowers:
        co_section = "\n### 👥 Co-Borrowers\n\n"
        for c in co_borrowers:
            co_section += f"- **{c.get('name', '—')}** — {c.get('role', '—')}\n"
    else:
        co_section = "\n### 👥 Co-Borrowers\n\n_No co-borrowers on file._\n"

    docs_section = "\n### 📁 Documents\n\n"
    if docs_submitted:
        docs_section += "**Submitted:**\n"
        docs_section += "\n".join(f"- ✅ {d}" for d in docs_submitted) + "\n"
    if docs_missing:
        docs_section += "\n**Missing / Outstanding:**\n"
        docs_section += "\n".join(f"- 🔴 {d}" for d in docs_missing) + "\n"
    if not docs_submitted and not docs_missing:
        docs_section += "_No document data on file._\n"

    prior_section = ""
    if prior:
        prior_section = "\n### 📋 Prior Rate Applications\n\n"
        prior_section += "| Loan ID | Year | Purpose | Status | Amount |\n"
        prior_section += "|---|---|---|---|---|\n"
        for p in prior:
            amt = float(p.get("amount", 0))
            prior_section += (
                f"| `{p.get('loan_id', '—')}` | {p.get('year', '—')} "
                f"| {p.get('purpose', '—')} | {p.get('status', '—')} | ${amt:,.0f} |\n"
            )
    else:
        prior_section = "\n### 📋 Prior Rate Applications\n\n_No prior applications on file._\n"

    pricing_section = ""
    if pricing_ex:
        pricing_section = "\n### 💲 Pricing Exceptions / Adjustments\n\n"
        for px in pricing_ex:
            pricing_section += f"- _{px.get('description', '—')}_ (applied {px.get('applied_date', '—')})\n"

    return (
        f"## 👤 BORROWER PROFILE — {name} (Loan #{loan_id})\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### 📊 Credit & Financial Profile\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Borrower Name** | {name} |\n"
        f"| **Current Loan Stage** | {stage} |\n"
        f"| **Credit Score (on file)** | {credit_display} |\n"
        f"| **Credit Inquiries (90 days)** | {int(inquiries)}{inquiry_flag} |\n"
        "\n---\n\n"
        "### ✅ Verification Status\n\n"
        "| Check | Status |\n"
        "|---|---|\n"
        f"| **Employment (VOE)** | {voe} |\n"
        f"| **Income (VOI)** | {voi} |\n"
        f"{co_section}"
        f"{docs_section}"
        f"{prior_section}"
        f"{pricing_section}"
    )
