from mcp_server.registry import mcp
from mcp_server.utils.dynamo import lookup_client_profile


def _star_rating(rating_str: str) -> tuple[str, str]:
    """Return (stars, display_str) from a numeric rating string."""
    try:
        val = float(rating_str)
        full = int(val)
        half = "½" if (val - full) >= 0.5 else ""
        empty = 5 - full - (1 if half else 0)
        stars = "★" * full + half + "☆" * empty
        return stars, f"{val:.1f} / 5.0"
    except (ValueError, TypeError):
        return "", "N/A"


@mcp.tool()
def get_client_profile(identifier: str) -> str:
    """
    Retrieve background, loan history, and peer reviews for a borrower.

    Returns: personal background notes, complete loan history, ratings and
    written reviews from other loan officers, and overall star rating.

    Use this when the user asks about a borrower or client as a person, e.g.:
    - "tell me about the borrower on loan 265561631"
    - "what's the background on John Homeowner?"
    - "pull up the client profile for loan 265561631"
    - "what do other loan officers say about this borrower?"
    - "give me a client review for 265561631"
    - "what's the rating for this borrower?"

    Do NOT use this for:
    - Loan data or status → use get_loan_overview or get_loan_intelligence_report
    - Approval checks → use check_loan_approval
    """
    item = lookup_client_profile(identifier)
    if not item:
        return (
            f"## ❌ Client Profile Not Found\n\n"
            f"No borrower profile on record for `{identifier}`.\n\n"
            "The loan may exist but no client profile has been seeded yet."
        )

    name = item.get("borrower_name", identifier)
    stars, rating_display = _star_rating(str(item.get("overall_rating", "N/A")))
    background = item.get("background", "_No background notes on file._")

    # Loan history table
    loan_history = item.get("loan_history", [])
    if loan_history:
        history_rows = "\n".join(
            f"| `{h.get('loan_id', 'N/A')}` | {h.get('amount', 'N/A')} "
            f"| {h.get('status', 'N/A')} | {h.get('date', 'N/A')} |"
            for h in loan_history
        )
        history_section = (
            "\n### 📁 Loan History\n\n"
            "| Loan ID | Amount | Status | Date |\n"
            "|---|---|---|---|\n"
            f"{history_rows}\n"
        )
    else:
        history_section = "\n### 📁 Loan History\n\n_No loan history on file._\n"

    # Reviews
    reviews = item.get("reviews", [])
    if reviews:
        review_blocks = []
        for r in reviews:
            reviewer = r.get("reviewer", "Unknown")
            comment = r.get("comment", "")
            rating = int(r.get("rating", 0))
            review_blocks.append(
                f"> **{reviewer}** — {'★' * rating}{'☆' * (5 - rating)}\n"
                f'> "{comment}"'
            )
        reviews_section = "\n\n".join(review_blocks)
    else:
        reviews_section = "_No reviews on file._"

    return (
        f"## 👤 CLIENT PROFILE — {name}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Overall Rating:** {stars}  **{rating_display}**\n\n"
        "---\n\n"
        "### 📋 Background\n\n"
        f"{background}\n"
        f"{history_section}"
        "---\n\n"
        "### 💬 Loan Officer Reviews\n\n"
        f"{reviews_section}\n"
    )
