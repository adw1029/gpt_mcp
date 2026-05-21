from mcp_server.registry import mcp
from mcp_server.utils.lo_data import lookup_lo_pipeline


@mcp.tool()
def get_lo_pipeline(lo_name: str) -> str:
    """
    Return a loan officer's full active pipeline with urgency flags and status breakdown.

    Use this for any pipeline-related question, e.g.:
    - "Show me all active loans in my pipeline right now."
    - "Which loans in my pipeline are past their rate lock expiration?"
    - "How many loans are currently in underwriting and what are their statuses?"
    - "Which files are pending conditions from the borrower?"
    - "Show me all loans expected to close within the next 14 days."
    - "Which loans have been in the same status for more than 10 business days?"
    - "List all loans that are suspended or on hold and the reason."
    - "What is the average time-to-close for my loans this quarter?"

    Pass lo_name as the loan officer's full name, e.g. "Jane Smith".

    Do NOT use this for:
    - Per-loan compliance details → use get_loan_compliance_status
    - Borrower profile → use get_lo_borrower_profile
    - Analytics/volume metrics → use get_lo_performance_analytics
    """
    item = lookup_lo_pipeline(lo_name)
    if not item:
        return (
            f"## ❌ Loan Officer Not Found\n\n"
            f"No pipeline record found for **\"{lo_name}\"**.\n\n"
            "Please check the name and try again. Names are case-sensitive (e.g. \"Jane Smith\")."
        )

    name = item.get("lo_name", lo_name)
    loans = item.get("loans", [])
    analytics = item.get("analytics", {})
    avg_days = analytics.get("avg_days_to_close", "—")

    if not loans:
        return (
            f"## 📊 PIPELINE — {name}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ No active loans in pipeline.\n"
        )

    total = len(loans)
    in_uw = [l for l in loans if "underwriting" in str(l.get("stage", "")).lower()]
    pending_cond = [l for l in loans if int(l.get("open_conditions_count", 0)) > 0]
    closing_soon = [l for l in loans if int(l.get("days_to_close", 999)) <= 14 and not l.get("funded")]
    stale = [l for l in loans if int(l.get("days_in_status", 0)) > 10]
    expired_lock = [l for l in loans if l.get("lock_days_remaining") is not None and int(l.get("lock_days_remaining", 999)) <= 0 and not l.get("funded")]
    expiring_lock = [l for l in loans if l.get("lock_days_remaining") is not None and 0 < int(l.get("lock_days_remaining", 999)) <= 7]
    suspended = [l for l in loans if l.get("suspended")]

    summary = (
        f"**{total} active loan(s)** | "
        f"{len(in_uw)} in UW | "
        f"{len(pending_cond)} pending conditions | "
        f"{len(closing_soon)} closing ≤14 days | "
        f"Avg close time: {avg_days} days\n"
    )

    alerts = []
    if expired_lock:
        alerts.append(f"🔴 **{len(expired_lock)} rate lock(s) EXPIRED** — immediate action required")
    if expiring_lock:
        alerts.append(f"🟠 **{len(expiring_lock)} rate lock(s) expiring within 7 days**")
    if stale:
        alerts.append(f"⚠️ **{len(stale)} loan(s) stale > 10 business days**")
    if suspended:
        alerts.append(f"🔴 **{len(suspended)} loan(s) suspended or on hold**")

    alerts_section = ""
    if alerts:
        alerts_section = "\n### 🚨 Alerts\n\n" + "\n".join(f"- {a}" for a in alerts) + "\n"

    rows = ""
    for l in sorted(loans, key=lambda x: int(x.get("days_to_close", 999))):
        loan_id = l.get("loan_id", "—")
        borrower = l.get("borrower_name", "—")
        stage = l.get("stage", "—")
        amount = float(l.get("amount", 0))
        state = l.get("state", "—")
        days_in = int(l.get("days_in_status", 0))
        lock_exp = l.get("lock_expiry", "—") or "Not locked"
        lock_days = l.get("lock_days_remaining")
        close_dt = l.get("close_date", "—")
        days_close = int(l.get("days_to_close", 0))
        cond_count = int(l.get("open_conditions_count", 0))
        comp_alerts = l.get("compliance_alerts", [])

        lock_display = (
            f"🔴 EXPIRED" if lock_days is not None and int(lock_days) <= 0 else
            f"⚠️ {lock_days}d left" if lock_days is not None and int(lock_days) <= 7 else
            f"{lock_exp}"
        )

        flags = []
        if cond_count > 0:
            flags.append(f"📋 {cond_count} conditions")
        if days_in > 10:
            flags.append(f"🕐 Stale ({days_in}d)")
        if l.get("suspended"):
            flags.append("🔴 SUSPENDED")
        for ca in comp_alerts[:1]:
            flags.append(f"⚠️ {ca}")

        rows += (
            f"| `{loan_id}` | {borrower} | {stage} | ${amount:,.0f} | {state} "
            f"| {lock_display} | {close_dt} ({days_close}d) "
            f"| {', '.join(flags) if flags else '✅'} |\n"
        )

    return (
        f"## 📊 PIPELINE — {name}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{summary}\n"
        f"{alerts_section}"
        "\n### 📋 Active Loans\n\n"
        "| Loan ID | Borrower | Stage | Amount | State | Rate Lock | Close Date | Flags |\n"
        "|---|---|---|---|---|---|---|---|\n"
        f"{rows}"
        "\n---\n\n"
        "_For per-loan details, use `get_lo_borrower_profile`, `get_loan_compliance_status`, "
        "or `get_closing_and_funding_status` with the loan ID._\n"
    )
