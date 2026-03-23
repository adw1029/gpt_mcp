from mcp_server.registry import mcp
from mcp_server.utils.dynamo import lookup_loan_dynamo, lookup_client_profile
from mcp_server.tools.approval import run_title_approval_rules, run_insurance_approval_rules

_STATUS_EMOJI = {
    "In Progress": "🟡",
    "Approved": "🟢",
    "Submitted": "🔵",
    "Closed": "⚫",
    "Denied": "🔴",
}


def _score_bar(score: int, max_score: int, width: int = 10) -> str:
    filled = round(score / max_score * width)
    return "█" * filled + "░" * (width - filled)


def _star_str(rating_str: str) -> str:
    try:
        val = float(rating_str)
        full = int(val)
        half = "½" if (val - full) >= 0.5 else ""
        return "★" * full + half
    except (ValueError, TypeError):
        return ""


@mcp.tool()
def get_loan_intelligence_report(loan_id: str) -> str:
    """
    Generate a comprehensive Loan Intelligence Briefing for a loan officer.

    This is the ONLY tool to use when the user wants a full picture, summary,
    overview, or briefing on a loan. It combines loan data + borrower profile
    + approval readiness scores + market context + risk flags in one report.

    Use this when the user asks for any kind of summary, briefing, or full
    analysis of a loan, e.g.:
    - "brief me on loan 265561631"
    - "give me a full overview / full picture / summary of loan 265561631"
    - "what's everything on loan 265561631?"
    - "run a full report on loan 123456789"
    - "show me everything about this loan"
    - "what's the status on loan 408823917?" (when context implies a full review)
    - "pull up loan 265561631" (when no specific field is requested)

    Do NOT use this for:
    - A specific single field → use get_loan_overview instead
    - Auto-approval checks → use check_loan_approval instead
    - Client background only → use get_client_profile instead
    """
    loan = lookup_loan_dynamo(loan_id)
    if not loan:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No loan record found for `{loan_id}`. Please verify the loan ID."
        )

    profile = lookup_client_profile(loan_id)
    title_result = run_title_approval_rules(loan, False)
    ins_result = run_insurance_approval_rules(loan, False)

    # Basic loan fields
    amount = float(loan.get("base_loan_amount", 0))
    status_raw = str(loan.get("loan_status", "Unknown"))
    status_icon = _STATUS_EMOJI.get(status_raw, "⚪")
    borrower = loan.get("buyer_names", "Unknown")
    officer = loan.get("loan_officer", "Unknown")
    address = loan.get("property_address", "Unknown")
    purpose = loan.get("loan_purpose", "Unknown")
    org = str(loan.get("organization", "")).upper()
    state = loan.get("state", "N/A")
    county = loan.get("property_county", "N/A")
    days = loan.get("days_in_pipeline", "N/A")
    prop_type = loan.get("property_type", "N/A")
    next_action = loan.get("next_action_due", "No pending actions")

    # Borrower rating
    rating_str = str(profile.get("overall_rating", "N/A")) if profile else "N/A"
    stars = _star_str(rating_str)

    # Approval score rows
    def score_row(label: str, icon: str, result: dict) -> str:
        s, m = result["score"], result["max_score"]
        bar = _score_bar(s, m)
        d = result["decision"]
        verdict_icon = {"APPROVED": "✅", "MANUAL REVIEW": "⚠️", "DENIED": "❌"}.get(d, "")
        return f"| {icon} {label} | `{bar}` | **{s}/{m}** | {verdict_icon} {d} |"

    # Reviews (top 2)
    reviews = profile.get("reviews", []) if profile else []
    if reviews:
        review_lines = []
        for r in reviews[:2]:
            reviewer = r.get("reviewer", "Unknown")
            comment = r.get("comment", "")[:90]
            rating = int(r.get("rating", 0))
            review_lines.append(f'> **{reviewer}** {"★" * rating}  \n> "{comment}..."')
        reviews_section = "\n\n".join(review_lines)
    else:
        reviews_section = "_No reviews on file._"

    # Risk flags
    risk_flags = loan.get("risk_flags", [])
    flags_section = (
        "_None identified_"
        if not risk_flags
        else "\n".join(f"- ⚠️ {f}" for f in risk_flags)
    )

    # Market context
    median = loan.get("market_median_price", "N/A")
    rate_env = loan.get("rate_environment", "N/A")
    comp = loan.get("comparable_approvals_qtd", "N/A")
    try:
        median_fmt = f"${float(median):,.0f}"
    except (ValueError, TypeError):
        median_fmt = str(median)

    return (
        f"## 🏦 LOAN INTELLIGENCE BRIEFING — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "| Field | Details |\n"
        "|---|---|\n"
        f"| 🏠 **Property** | {address} |\n"
        f"| 💰 **Loan Amount** | ${amount:,.0f} ({purpose}) |\n"
        f"| 📊 **Status** | {status_icon} {status_raw} |\n"
        f"| 👤 **Borrower** | {borrower} &nbsp; {stars} ({rating_str} / 5.0) |\n"
        f"| 🏢 **Loan Officer** | {officer} |\n"
        f"| 🏛️ **Organization** | {org} |\n"
        f"| 🗺️ **State / County** | {state} / {county} |\n"
        f"| 🏷️ **Property Type** | {prop_type} |\n"
        f"| 📅 **Days in Pipeline** | {days} days |\n"
        "\n---\n\n"
        "### 🤖 AUTO-APPROVAL READINESS\n\n"
        "| Document | Score | Points | Verdict |\n"
        "|---|---|---|---|\n"
        f"{score_row('Title', '📄', title_result)}\n"
        f"{score_row('Insurance', '🛡️', ins_result)}\n"
        "\n---\n\n"
        "### 👥 OFFICER REVIEWS\n\n"
        f"{reviews_section}\n"
        "\n---\n\n"
        "### 📈 MARKET CONTEXT — " + county + "\n\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| Median Home Price | {median_fmt} |\n"
        f"| Rate Environment | {rate_env} |\n"
        f"| Comparable Approvals (QTD) | {comp} |\n"
        "\n---\n\n"
        "### ⚠️ RISK FLAGS\n\n"
        f"{flags_section}\n"
        "\n---\n\n"
        "### ✅ RECOMMENDED NEXT STEP\n\n"
        f"> {next_action}\n"
    )
