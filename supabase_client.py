"""
supabase_client.py — Supabase integration for FlashRFP.ai
Wraps all DB calls. Swap admin_db.py to use these functions.

Project: https://hxhugijpyoyhzfyvybzf.supabase.co
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://hxhugijpyoyhzfyvybzf.supabase.co")
SUPABASE_ANON_KEY    = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

_client = None
_is_configured = False

def get_client():
    """Returns a Supabase client using the service role key (full DB access)."""
    global _client, _is_configured
    if _client and _is_configured:
        return _client
    if not SUPABASE_SERVICE_KEY or SUPABASE_SERVICE_KEY.startswith("PASTE_"):
        raise RuntimeError(
            "Supabase service key not configured.\n"
            "Open FlashRFP_Ai/.env and paste your service_role key into SUPABASE_SERVICE_KEY."
        )
    from supabase import create_client, Client
    _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    _is_configured = True
    return _client

def is_supabase_ready() -> bool:
    """Returns True if Supabase keys are set and connection works."""
    try:
        if not SUPABASE_SERVICE_KEY or SUPABASE_SERVICE_KEY.startswith("PASTE_"):
            return False
        c = get_client()
        c.table("users").select("id").limit(1).execute()
        return True
    except Exception:
        return False

# ──────────────────────────── USERS ────────────────────────────────────────────

def get_all_users() -> dict:
    """Returns {username: user_dict} — mirrors admin_db.get_all_users()."""
    c = get_client()
    res = c.table("users").select("*").execute()
    return {row["username"]: row for row in (res.data or [])}

def get_user(username: str) -> dict | None:
    c = get_client()
    res = c.table("users").select("*").eq("username", username).single().execute()
    return res.data

def create_user(username: str, name: str, email: str, company: str = "",
                plan: str = "trial") -> dict:
    from admin_db import PLAN_PRICES
    trial_exp = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d") if plan == "trial" else None
    row = {
        "username": username,
        "name": name,
        "email": email,
        "company": company,
        "plan": plan,
        "status": "trial" if plan == "trial" else "active",
        "is_admin": False,
        "trial_expires_at": trial_exp,
        "monthly_amount": PLAN_PRICES.get(plan, 0),
    }
    c = get_client()
    res = c.table("users").insert(row).execute()
    return res.data[0] if res.data else {}

def update_user(username: str, updates: dict) -> bool:
    c = get_client()
    res = c.table("users").update(updates).eq("username", username).execute()
    return bool(res.data)

def delete_user(username: str) -> bool:
    user = get_user(username)
    if not user or user.get("is_admin"):
        return False
    c = get_client()
    c.table("users").delete().eq("username", username).execute()
    return True

def activate_user(username: str) -> bool:
    return update_user(username, {"status": "active"})

def suspend_user(username: str) -> bool:
    return update_user(username, {"status": "suspended"})

def extend_trial(username: str, extra_days: int) -> bool:
    user = get_user(username)
    if not user:
        return False
    current_exp = user.get("trial_expires_at")
    try:
        base = datetime.strptime(current_exp, "%Y-%m-%d") if current_exp else datetime.now()
    except Exception:
        base = datetime.now()
    new_exp = (base + timedelta(days=extra_days)).strftime("%Y-%m-%d")
    return update_user(username, {"trial_expires_at": new_exp, "status": "trial"})

def change_user_plan(username: str, new_plan: str) -> bool:
    from admin_db import PLAN_PRICES
    return update_user(username, {
        "plan": new_plan,
        "monthly_amount": PLAN_PRICES.get(new_plan, 0),
        "status": "active" if new_plan != "trial" else "trial",
    })

def increment_response_count(username: str):
    """Atomically increments responses_this_month by 1."""
    c = get_client()
    # Use RPC for atomic increment — define this function in Supabase SQL editor:
    # create or replace function inc_responses(uname text)
    # returns void language sql as $$
    #   update users set responses_this_month = responses_this_month + 1,
    #                    last_active = current_date
    #   where username = uname;
    # $$;
    try:
        c.rpc("inc_responses", {"uname": username}).execute()
    except Exception:
        # Fallback: fetch + update
        user = get_user(username)
        if user:
            update_user(username, {
                "responses_this_month": user.get("responses_this_month", 0) + 1,
                "last_active": datetime.now().strftime("%Y-%m-%d"),
            })

def check_plan_limits(username: str) -> tuple[bool, str]:
    """Returns (allowed, reason). Call before every generation."""
    from admin_db import PLAN_LIMITS
    user = get_user(username)
    if not user:
        return False, "User not found."
    status = user.get("status", "")
    if status in ("suspended", "cancelled"):
        return False, "Your account is suspended. Please contact support."
    plan = user.get("plan", "trial")
    if plan == "trial" and status == "trial":
        exp = user.get("trial_expires_at")
        if exp and datetime.now().date() > datetime.strptime(exp, "%Y-%m-%d").date():
            return False, "Your 14-day free trial has expired. Please upgrade to continue."
    limits = PLAN_LIMITS.get(plan, {})
    max_resp = limits.get("responses", 10)
    if max_resp != -1 and user.get("responses_this_month", 0) >= max_resp:
        return False, (
            f"Monthly limit of {max_resp} responses reached. "
            f"Upgrade your plan to continue."
        )
    return True, "ok"

def purge_tenant_data(username: str) -> str:
    """Delete ChromaDB vectors for this tenant + remove from users table."""
    try:
        import chromadb
        db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        if os.path.exists(db_path):
            client = chromadb.PersistentClient(path=db_path)
            for coll_meta in client.list_collections():
                coll = client.get_collection(coll_meta.name)
                coll.delete(where={"tenant_id": username})
    except Exception as e:
        return f"ChromaDB purge error: {e}"
    delete_user(username)
    return "success"

# ──────────────────────────── SUBSCRIPTIONS ────────────────────────────────────

def get_all_subscriptions() -> dict:
    c = get_client()
    res = c.table("subscriptions").select("*").execute()
    return {row["subscription_id"]: row for row in (res.data or [])}

def create_subscription(sub_id: str, username: str, plan: str, amount: int) -> dict:
    row = {
        "subscription_id": sub_id,
        "username": username,
        "plan": plan,
        "status": "active",
        "amount": amount,
        "currency": "INR",
        "billing_cycle": "monthly",
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "next_billing_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
    }
    c = get_client()
    res = c.table("subscriptions").insert(row).execute()
    return res.data[0] if res.data else {}

def update_subscription(sub_id: str, updates: dict) -> bool:
    c = get_client()
    res = c.table("subscriptions").update(updates).eq("subscription_id", sub_id).execute()
    return bool(res.data)

# ──────────────────────────── AUDIT LOGS ───────────────────────────────────────

def log_audit_event(username: str, question: str, sources: list,
                    response: str, provider: str = None,
                    model: str = None, latency_ms: int = None):
    """Write an audit entry to Supabase. Falls back to local JSONL if DB not ready."""
    if not is_supabase_ready():
        # Fallback → local audit_log.jsonl (existing behaviour)
        _log_local(username, question, sources, response)
        return
    row = {
        "username": username or "anonymous",
        "question_asked": question,
        "source_docs": [s.get("source","") for s in (sources or [])],
        "llm_response": response[:4000] if response else "",
        "provider": provider,
        "model": model,
        "latency_ms": latency_ms,
    }
    try:
        get_client().table("audit_logs").insert(row).execute()
    except Exception:
        _log_local(username, question, sources, response)

def _log_local(username, question, sources, response):
    import json, time
    log_file = os.path.join(os.path.dirname(__file__), "audit_log.jsonl")
    event = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "user_id": username or "anonymous",
        "question_asked": question,
        "source_docs_retrieved": [s.get("source","") for s in (sources or [])],
        "llm_response": response,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

def get_audit_logs(username: str | None = None, limit: int = 100) -> list:
    if not is_supabase_ready():
        from admin_db import get_audit_logs as _local_logs
        return _local_logs(username)
    c = get_client()
    q = c.table("audit_logs").select("*").order("created_at", desc=True).limit(limit)
    if username:
        q = q.eq("username", username)
    res = q.execute()
    return res.data or []

# ──────────────────────────── SYSTEM METRICS ───────────────────────────────────

def upsert_daily_metric(date_str: str, updates: dict):
    c = get_client()
    row = {"metric_date": date_str, **updates}
    c.table("system_metrics").upsert(row, on_conflict="metric_date").execute()

def get_system_metrics_from_db(days: int = 30) -> list:
    if not is_supabase_ready():
        from admin_db import get_system_metrics
        return get_system_metrics().get("daily", [])
    c = get_client()
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    res = (c.table("system_metrics")
             .select("*")
             .gte("metric_date", cutoff)
             .order("metric_date")
             .execute())
    rows = res.data or []
    # Normalise field names to match admin_db format
    return [{
        "date": r["metric_date"],
        "new_signups": r.get("new_signups", 0),
        "responses_generated": r.get("responses_generated", 0),
        "api_errors": r.get("api_errors", 0),
        "p50_latency_ms": r.get("p50_latency_ms", 0),
        "p95_latency_ms": r.get("p95_latency_ms", 0),
        "llm_cost_usd": float(r.get("llm_cost_usd", 0)),
    } for r in rows]

# ──────────────────────────── REVENUE METRICS ──────────────────────────────────

def calculate_revenue_metrics() -> dict:
    """Full revenue metrics — uses Supabase if configured, else falls back to admin_db."""
    if not is_supabase_ready():
        from admin_db import calculate_revenue_metrics as _local
        return _local()

    users = get_all_users()
    subs  = get_all_subscriptions()
    from admin_db import PLAN_PRICES, PLAN_LIMITS

    now = datetime.now()
    mrr = sum(u["monthly_amount"] for u in users.values()
              if u["status"] == "active" and u["monthly_amount"] > 0)
    arr = mrr * 12
    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    new_signups = sum(1 for u in users.values()
                      if str(u.get("created_at","")) >= month_start)
    active_paying = sum(1 for u in users.values()
                        if u["status"] == "active" and u["monthly_amount"] > 0)
    trial_users = sum(1 for u in users.values() if u["status"] == "trial")
    churned     = sum(1 for u in users.values() if u["status"] == "cancelled")
    suspended   = sum(1 for u in users.values() if u["status"] == "suspended")

    rev_by_plan  = {p: 0 for p in PLAN_PRICES}
    user_by_plan = {p: 0 for p in PLAN_PRICES}
    for u in users.values():
        if u["status"] == "active":
            plan = u["plan"]
            rev_by_plan[plan]  = rev_by_plan.get(plan, 0) + u["monthly_amount"]
            user_by_plan[plan] = user_by_plan.get(plan, 0) + 1

    total_revenue = sum(s.get("total_paid", 0) for s in subs.values())
    daily = get_system_metrics_from_db()
    recent_llm = sum(d.get("llm_cost_usd", 0) for d in daily[-7:])

    return {
        "mrr": mrr, "arr": arr,
        "new_signups_month": new_signups,
        "active_paying": active_paying,
        "trial_users": trial_users,
        "churned": churned,
        "suspended": suspended,
        "total_revenue": total_revenue,
        "rev_by_plan": rev_by_plan,
        "user_by_plan": user_by_plan,
        "daily_responses": [(d["date"], d["responses_generated"]) for d in daily],
        "daily_signups":   [(d["date"], d["new_signups"]) for d in daily],
        "recent_llm_cost_usd": round(recent_llm, 2),
        "churn_rate": round(churned / max(active_paying + churned, 1) * 100, 1),
    }
