from mcp_server.registry import mcp
from mcp_server.utils.lo_data import lookup_lo_pipeline


@mcp.tool()
def get_lo_performance_analytics(lo_name: str) -> str:
    """
    Return performance analytics for a loan officer — volume, pull-through, referrals, and fallout.

    Use this when an LO asks about their production metrics, e.g.:
    - "What is my total loan volume closed this month vs. last month?"
    - "Show me my pull-through rate for applications this quarter."
    - "How many leads in my pipeline converted to applications this week?"
    - "What is my average loan size and product mix for the past 90 days?"
    - "Which of my borrowers have loans eligible for refinancing at today's rates?"
    - "Show me my top referral sources by volume for this year."
    - "What is my fallout rate by loan type and reason code this quarter?"

    Pass lo_name as the loan officer's full name, e.g. "Jane Smith".

    Do NOT use this for:
    - Per-loan details → use get_lo_borrower_profile or get_loan_compliance_status
    - Pipeline view → use get_lo_pipeline
    """
    item = lookup_lo_pipeline(lo_name)
    if not item:
        return (
            f"## ❌ Loan Officer Not Found\n\n"
            f"No record found for **\"{lo_name}\"**.\n\n"
            "Please check the name spelling (e.g. \"Jane Smith\")."
        )

    name = item.get("lo_name", lo_name)
    a = item.get("analytics", {})

    vol_this = float(a.get("volume_this_month_dollars", 0))
    vol_this_ct = int(a.get("volume_this_month_count", 0))
    vol_last = float(a.get("volume_last_month_dollars", 0))
    vol_last_ct = int(a.get("volume_last_month_count", 0))
    pull_through = str(a.get("pull_through_rate_pct", "—"))
    avg_size = float(a.get("avg_loan_size_90d", 0))
    product_mix = a.get("product_mix", {})
    leads_wk = int(a.get("leads_this_week", 0))
    apps_wk = int(a.get("applications_this_week", 0))
    fallout = a.get("fallout_by_type", [])
    referrals = a.get("top_referrals", [])
    refi_ct = int(a.get("refi_eligible_count", 0))
    avg_close = int(a.get("avg_days_to_close", 0))

    vol_delta = vol_this - vol_last
    vol_pct = (vol_delta / vol_last * 100) if vol_last > 0 else 0
    vol_trend = f"{'📈' if vol_delta >= 0 else '📉'} {'+' if vol_delta >= 0 else ''}{vol_pct:.1f}% vs last month"

    conversion_rate = f"{apps_wk}/{leads_wk} ({apps_wk/leads_wk*100:.0f}%)" if leads_wk > 0 else f"{apps_wk}/{leads_wk}"

    product_mix_rows = ""
    for product, pct in product_mix.items():
        product_mix_rows += f"| {product} | {pct} |\n"

    fallout_section = ""
    if fallout:
        fallout_section = "\n### 📉 Fallout Rate by Type\n\n"
        fallout_section += "| Loan Type | Reason | Count |\n|---|---|---|\n"
        for f in fallout:
            fallout_section += f"| {f.get('type', '—')} | {f.get('reason', '—')} | {int(f.get('count', 0))} |\n"
    else:
        fallout_section = "\n### 📉 Fallout\n\n✅ No fallout recorded this quarter.\n"

    referral_section = ""
    if referrals:
        referral_section = "\n### 🤝 Top Referral Sources (YTD)\n\n"
        referral_section += "| Source | Volume YTD | Loans |\n|---|---|---|\n"
        for r in referrals:
            vol = float(r.get("volume_ytd", 0))
            referral_section += f"| {r.get('source', '—')} | ${vol:,.0f} | {int(r.get('count', 0))} |\n"
    else:
        referral_section = "\n### 🤝 Referral Sources\n\n_No referral data on file._\n"

    return (
        f"## 📊 PERFORMANCE ANALYTICS — {name}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### 💰 Volume\n\n"
        "| Metric | This Month | Last Month |\n"
        "|---|---|---|\n"
        f"| **Loan Volume ($)** | ${vol_this:,.0f} | ${vol_last:,.0f} |\n"
        f"| **Loan Count** | {vol_this_ct} | {vol_last_ct} |\n"
        f"| **Trend** | {vol_trend} | — |\n"
        "\n---\n\n"
        "### 📈 Conversion & Pipeline Health\n\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| **Pull-Through Rate (QTD)** | {pull_through}% |\n"
        f"| **Avg Loan Size (90 days)** | ${avg_size:,.0f} |\n"
        f"| **Avg Days to Close** | {avg_close} days |\n"
        f"| **Leads → Apps This Week** | {conversion_rate} |\n"
        f"| **Refi-Eligible Borrowers** | {refi_ct} |\n"
        "\n---\n\n"
        "### 🏦 Product Mix (90 Days)\n\n"
        "| Product | Share |\n"
        "|---|---|\n"
        f"{product_mix_rows}"
        f"{fallout_section}"
        f"{referral_section}"
        "\n---\n\n"
        "_Data as of March 30, 2026. Analytics reflect seeded demo data._\n"
    )
