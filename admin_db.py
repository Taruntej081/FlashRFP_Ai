"""
admin_db.py — Data layer for FlashRFP.ai Admin Panel.
Uses JSON files for persistence. Each function can be swapped 1:1 for Supabase.
"""
import os
import json
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_DATA_DIR = os.path.join(BASE_DIR, "admin_data")
USERS_FILE = os.path.join(ADMIN_DATA_DIR, "users.json")
SUBSCRIPTIONS_FILE = os.path.join(ADMIN_DATA_DIR, "subscriptions.json")
METRICS_FILE = os.path.join(ADMIN_DATA_DIR, "metrics.json")

PLAN_PRICES = {
    "trial": 0,
    "starter": 2999,
    "professional": 7999,
    "enterprise": 24999,
}

PLAN_LIMITS = {
    "trial":        {"responses": 10,   "documents": 5,   "batches": 3},
    "starter":      {"responses": 100,  "documents": 50,  "batches": 20},
    "professional": {"responses": 500,  "documents": 500, "batches": 100},
    "enterprise":   {"responses": -1,   "documents": -1,  "batches": -1},
}

# ─────────────────── internal helpers ────────────────────────

def _ensure_data_dir():
    os.makedirs(ADMIN_DATA_DIR, exist_ok=True)

def _load_json(path: str):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

# ─────────────────── initialise mock data ────────────────────

def initialize_mock_data():
    """Creates realistic demo dataset if not already present."""
    _ensure_data_dir()
    now = datetime.now()

    users = {
        "admin": {
            "username": "admin",
            "name": "Administrator",
            "email": "admin@flashrfp.ai",
            "company": "FlashRFP Internal",
            "plan": "enterprise",
            "status": "active",
            "is_admin": True,
            "created_at": (now - timedelta(days=180)).strftime("%Y-%m-%d"),
            "trial_expires_at": None,
            "subscription_id": None,
            "responses_this_month": 0,
            "documents_count": 0,
            "batches_this_month": 0,
            "last_active": now.strftime("%Y-%m-%d"),
            "monthly_amount": 0,
        },
        "priya_mehta": {
            "username": "priya_mehta",
            "name": "Priya Mehta",
            "email": "priya@infosys.com",
            "company": "Infosys Limited",
            "plan": "professional",
            "status": "active",
            "is_admin": False,
            "created_at": (now - timedelta(days=95)).strftime("%Y-%m-%d"),
            "trial_expires_at": None,
            "subscription_id": "sub_PFX8291",
            "responses_this_month": 214,
            "documents_count": 43,
            "batches_this_month": 18,
            "last_active": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "monthly_amount": 7999,
        },
        "rahul_verma": {
            "username": "rahul_verma",
            "name": "Rahul Verma",
            "email": "rahul.v@tataconsult.com",
            "company": "Tata Consultancy Services",
            "plan": "enterprise",
            "status": "active",
            "is_admin": False,
            "created_at": (now - timedelta(days=145)).strftime("%Y-%m-%d"),
            "trial_expires_at": None,
            "subscription_id": "sub_ETP2847",
            "responses_this_month": 1843,
            "documents_count": 312,
            "batches_this_month": 67,
            "last_active": now.strftime("%Y-%m-%d"),
            "monthly_amount": 24999,
        },
        "sneha_kapoor": {
            "username": "sneha_kapoor",
            "name": "Sneha Kapoor",
            "email": "sneha@wipro.com",
            "company": "Wipro Technologies",
            "plan": "starter",
            "status": "active",
            "is_admin": False,
            "created_at": (now - timedelta(days=28)).strftime("%Y-%m-%d"),
            "trial_expires_at": None,
            "subscription_id": "sub_WIP4512",
            "responses_this_month": 67,
            "documents_count": 18,
            "batches_this_month": 8,
            "last_active": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "monthly_amount": 2999,
        },
        "arjun_nair": {
            "username": "arjun_nair",
            "name": "Arjun Nair",
            "email": "arjun.n@hexaware.com",
            "company": "Hexaware Technologies",
            "plan": "trial",
            "status": "trial",
            "is_admin": False,
            "created_at": (now - timedelta(days=8)).strftime("%Y-%m-%d"),
            "trial_expires_at": (now + timedelta(days=6)).strftime("%Y-%m-%d"),
            "subscription_id": None,
            "responses_this_month": 6,
            "documents_count": 3,
            "batches_this_month": 1,
            "last_active": now.strftime("%Y-%m-%d"),
            "monthly_amount": 0,
        },
        "vikram_shah": {
            "username": "vikram_shah",
            "name": "Vikram Shah",
            "email": "vikram@mphasis.com",
            "company": "Mphasis Corporation",
            "plan": "professional",
            "status": "suspended",
            "is_admin": False,
            "created_at": (now - timedelta(days=60)).strftime("%Y-%m-%d"),
            "trial_expires_at": None,
            "subscription_id": "sub_MPH9341",
            "responses_this_month": 0,
            "documents_count": 28,
            "batches_this_month": 0,
            "last_active": (now - timedelta(days=12)).strftime("%Y-%m-%d"),
            "monthly_amount": 7999,
        },
        "deepa_iyer": {
            "username": "deepa_iyer",
            "name": "Deepa Iyer",
            "email": "deepa@ltimindtree.com",
            "company": "LTIMindtree",
            "plan": "starter",
            "status": "cancelled",
            "is_admin": False,
            "created_at": (now - timedelta(days=75)).strftime("%Y-%m-%d"),
            "trial_expires_at": None,
            "subscription_id": "sub_LTI7823",
            "responses_this_month": 0,
            "documents_count": 0,
            "batches_this_month": 0,
            "last_active": (now - timedelta(days=18)).strftime("%Y-%m-%d"),
            "monthly_amount": 0,
        },
        "karthik_rajan": {
            "username": "karthik_rajan",
            "name": "Karthik Rajan",
            "email": "karthik@zensar.com",
            "company": "Zensar Technologies",
            "plan": "trial",
            "status": "trial",
            "is_admin": False,
            "created_at": (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            "trial_expires_at": (now + timedelta(days=11)).strftime("%Y-%m-%d"),
            "subscription_id": None,
            "responses_this_month": 2,
            "documents_count": 1,
            "batches_this_month": 0,
            "last_active": now.strftime("%Y-%m-%d"),
            "monthly_amount": 0,
        },
        "ananya_bose": {
            "username": "ananya_bose",
            "name": "Ananya Bose",
            "email": "ananya@cognizant.com",
            "company": "Cognizant Technology",
            "plan": "professional",
            "status": "active",
            "is_admin": False,
            "created_at": (now - timedelta(days=52)).strftime("%Y-%m-%d"),
            "trial_expires_at": None,
            "subscription_id": "sub_COG5512",
            "responses_this_month": 134,
            "documents_count": 76,
            "batches_this_month": 22,
            "last_active": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "monthly_amount": 7999,
        },
    }
    if not os.path.exists(USERS_FILE):
        _save_json(USERS_FILE, users)

    subscriptions = {
        "sub_PFX8291": {
            "subscription_id": "sub_PFX8291",
            "username": "priya_mehta",
            "plan": "professional",
            "status": "active",
            "amount": 7999,
            "currency": "INR",
            "billing_cycle": "monthly",
            "start_date": (now - timedelta(days=95)).strftime("%Y-%m-%d"),
            "next_billing_date": (now + timedelta(days=15)).strftime("%Y-%m-%d"),
            "total_paid": 63992,
            "invoices": 8,
        },
        "sub_ETP2847": {
            "subscription_id": "sub_ETP2847",
            "username": "rahul_verma",
            "plan": "enterprise",
            "status": "active",
            "amount": 24999,
            "currency": "INR",
            "billing_cycle": "monthly",
            "start_date": (now - timedelta(days=145)).strftime("%Y-%m-%d"),
            "next_billing_date": (now + timedelta(days=5)).strftime("%Y-%m-%d"),
            "total_paid": 124995,
            "invoices": 5,
        },
        "sub_WIP4512": {
            "subscription_id": "sub_WIP4512",
            "username": "sneha_kapoor",
            "plan": "starter",
            "status": "active",
            "amount": 2999,
            "currency": "INR",
            "billing_cycle": "monthly",
            "start_date": (now - timedelta(days=28)).strftime("%Y-%m-%d"),
            "next_billing_date": (now + timedelta(days=2)).strftime("%Y-%m-%d"),
            "total_paid": 2999,
            "invoices": 1,
        },
        "sub_MPH9341": {
            "subscription_id": "sub_MPH9341",
            "username": "vikram_shah",
            "plan": "professional",
            "status": "halted",
            "amount": 7999,
            "currency": "INR",
            "billing_cycle": "monthly",
            "start_date": (now - timedelta(days=60)).strftime("%Y-%m-%d"),
            "next_billing_date": (now - timedelta(days=12)).strftime("%Y-%m-%d"),
            "total_paid": 15998,
            "invoices": 2,
        },
        "sub_LTI7823": {
            "subscription_id": "sub_LTI7823",
            "username": "deepa_iyer",
            "plan": "starter",
            "status": "cancelled",
            "amount": 2999,
            "currency": "INR",
            "billing_cycle": "monthly",
            "start_date": (now - timedelta(days=75)).strftime("%Y-%m-%d"),
            "next_billing_date": None,
            "total_paid": 5998,
            "invoices": 2,
        },
        "sub_COG5512": {
            "subscription_id": "sub_COG5512",
            "username": "ananya_bose",
            "plan": "professional",
            "status": "active",
            "amount": 7999,
            "currency": "INR",
            "billing_cycle": "monthly",
            "start_date": (now - timedelta(days=52)).strftime("%Y-%m-%d"),
            "next_billing_date": (now + timedelta(days=8)).strftime("%Y-%m-%d"),
            "total_paid": 15998,
            "invoices": 2,
        },
    }
    if not os.path.exists(SUBSCRIPTIONS_FILE):
        _save_json(SUBSCRIPTIONS_FILE, subscriptions)

    # Simulated daily system metrics for last 30 days with weekly cycle and growth trend
    daily = []
    base_responses = 40  # Start with 40 responses/day 30 days ago
    for i in range(30, 0, -1):
        target_date = now - timedelta(days=i)
        day_str = target_date.strftime("%Y-%m-%d")
        
        # Day of week multiplier (weekend traffic drops by 80%)
        is_weekend = target_date.weekday() in (5, 6)
        day_mult = 0.2 if is_weekend else 1.0
        
        # Steady growth trend over 30 days (+3% per day compound-ish)
        growth_mult = 1.0 + (30 - i) * 0.035
        
        # Calculate responses
        rand_variance = random.uniform(0.8, 1.25)
        responses = int(base_responses * growth_mult * day_mult * rand_variance)
        
        # New signups correlate with weekdays and growth
        signup_chance = random.random()
        if is_weekend:
            new_signups = 1 if signup_chance > 0.85 else 0
        else:
            new_signups = random.choices([0, 1, 2, 3], weights=[0.4, 0.4, 0.15, 0.05])[0]
            if growth_mult > 1.4 and signup_chance > 0.6:
                new_signups += 1
                
        # Latency p50 / p95 (higher traffic slightly increases tail latency)
        p50 = int(random.randint(1800, 2400) + (responses * 2.5))
        p95 = int(p50 * random.uniform(2.8, 3.6))
        
        # Errors (low, occasionally a peak on heavy load days)
        if responses > 120 and random.random() > 0.7:
            api_errors = random.randint(2, 4)
        else:
            api_errors = random.choices([0, 1, 2], weights=[0.8, 0.15, 0.05])[0]
            
        # LLM cost (correlates with responses, ~0.025 USD per response + variance)
        llm_cost = round(responses * random.uniform(0.022, 0.029), 2)
        
        daily.append({
            "date": day_str,
            "new_signups": new_signups,
            "responses_generated": responses,
            "api_errors": api_errors,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "llm_cost_usd": llm_cost,
        })
    _save_json(METRICS_FILE, {"daily": daily})


# ─────────────────── CRUD: Users ─────────────────────────────

def get_all_users() -> dict:
    initialize_mock_data()
    return _load_json(USERS_FILE)

def get_user(username: str) -> dict | None:
    return get_all_users().get(username)

def update_user(username: str, updates: dict) -> bool:
    users = get_all_users()
    if username not in users:
        return False
    users[username].update(updates)
    _save_json(USERS_FILE, users)
    return True

def delete_user(username: str) -> bool:
    users = get_all_users()
    if username not in users:
        return False
    if users[username].get("is_admin"):
        return False   # never delete admin
    del users[username]
    _save_json(USERS_FILE, users)
    return True

def activate_user(username: str) -> bool:
    return update_user(username, {"status": "active"})

def suspend_user(username: str) -> bool:
    return update_user(username, {"status": "suspended"})

def reset_user_password(username: str, new_hashed_pw: str) -> bool:
    """Updates bcrypt hash in auth_config.json (main app auth file)."""
    config_path = os.path.join(BASE_DIR, "auth_config.json")
    if not os.path.exists(config_path):
        return False
    with open(config_path, "r") as f:
        config = json.load(f)
    usernames = config.get("credentials", {}).get("usernames", {})
    if username not in usernames:
        return False
    usernames[username]["password"] = new_hashed_pw
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
    return True

def extend_trial(username: str, extra_days: int) -> bool:
    user = get_user(username)
    if not user:
        return False
    current_expiry = user.get("trial_expires_at")
    if current_expiry:
        try:
            base = datetime.strptime(current_expiry, "%Y-%m-%d")
        except Exception:
            base = datetime.now()
    else:
        base = datetime.now()
    new_expiry = (base + timedelta(days=extra_days)).strftime("%Y-%m-%d")
    return update_user(username, {"trial_expires_at": new_expiry, "status": "trial"})

def change_user_plan(username: str, new_plan: str) -> bool:
    if new_plan not in PLAN_PRICES:
        return False
    return update_user(username, {
        "plan": new_plan,
        "monthly_amount": PLAN_PRICES[new_plan],
        "status": "active" if new_plan != "trial" else "trial",
    })

def purge_tenant_data(username: str) -> str:
    """Delete all ChromaDB vectors for this tenant. Returns status string."""
    try:
        import chromadb
        db_path = os.path.join(BASE_DIR, "chroma_db")
        if os.path.exists(db_path):
            client = chromadb.PersistentClient(path=db_path)
            for coll in client.list_collections():
                c = client.get_collection(coll.name)
                c.delete(where={"tenant_id": username})
        return "success"
    except Exception as e:
        return f"error: {e}"


# ─────────────────── CRUD: Subscriptions ─────────────────────

def get_all_subscriptions() -> dict:
    initialize_mock_data()
    return _load_json(SUBSCRIPTIONS_FILE)

def update_subscription(sub_id: str, updates: dict) -> bool:
    subs = get_all_subscriptions()
    if sub_id not in subs:
        return False
    subs[sub_id].update(updates)
    _save_json(SUBSCRIPTIONS_FILE, subs)
    return True


# ─────────────────── Metrics & Analytics ─────────────────────

def get_system_metrics() -> dict:
    initialize_mock_data()
    return _load_json(METRICS_FILE)

def get_audit_logs(username: str | None = None) -> list:
    """Reads audit_log.jsonl written by rag_engine.py."""
    log_file = os.path.join(BASE_DIR, "audit_log.jsonl")
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if username is None or entry.get("user_id") == username:
                        logs.append(entry)
                except Exception:
                    pass
    return list(reversed(logs[-300:]))   # newest first, cap 300

def calculate_revenue_metrics() -> dict:
    users  = get_all_users()
    subs   = get_all_subscriptions()
    metrics = get_system_metrics()
    now    = datetime.now()

    mrr = sum(
        u["monthly_amount"] for u in users.values()
        if u["status"] == "active" and u["monthly_amount"] > 0
    )
    arr = mrr * 12

    month_start = now.replace(day=1).strftime("%Y-%m-%d")
    new_signups_month = sum(
        1 for u in users.values()
        if u.get("created_at", "") >= month_start
    )
    active_paying = sum(
        1 for u in users.values()
        if u["status"] == "active" and u["monthly_amount"] > 0
    )
    trial_users = sum(1 for u in users.values() if u["status"] == "trial")
    churned     = sum(1 for u in users.values() if u["status"] == "cancelled")
    suspended   = sum(1 for u in users.values() if u["status"] == "suspended")

    rev_by_plan = {p: 0 for p in PLAN_PRICES}
    user_by_plan = {p: 0 for p in PLAN_PRICES}
    for u in users.values():
        if u["status"] == "active":
            plan = u["plan"]
            rev_by_plan[plan] = rev_by_plan.get(plan, 0) + u["monthly_amount"]
            user_by_plan[plan] = user_by_plan.get(plan, 0) + 1

    total_revenue = sum(s.get("total_paid", 0) for s in subs.values())

    daily = metrics.get("daily", [])
    recent_llm_cost = sum(d.get("llm_cost_usd", 0) for d in daily[-7:])
    daily_responses = [(d["date"], d.get("responses_generated", 0)) for d in daily]
    daily_signups   = [(d["date"], d.get("new_signups", 0)) for d in daily]

    churn_rate = round(churned / max(active_paying + churned, 1) * 100, 1)

    return {
        "mrr": mrr,
        "arr": arr,
        "new_signups_month": new_signups_month,
        "active_paying": active_paying,
        "trial_users": trial_users,
        "churned": churned,
        "suspended": suspended,
        "total_revenue": total_revenue,
        "rev_by_plan": rev_by_plan,
        "user_by_plan": user_by_plan,
        "daily_responses": daily_responses,
        "daily_signups": daily_signups,
        "recent_llm_cost_usd": round(recent_llm_cost, 2),
        "churn_rate": churn_rate,
    }

def get_chroma_stats() -> dict:
    """Returns live stats from the local ChromaDB directory."""
    try:
        import chromadb
        db_path = os.path.join(BASE_DIR, "chroma_db")
        if not os.path.exists(db_path):
            return {"collections": 0, "total_chunks": 0, "tenants": [], "db_size_mb": 0}
        client = chromadb.PersistentClient(path=db_path)
        colls  = client.list_collections()
        total_chunks = 0
        tenants = set()
        for coll_meta in colls:
            try:
                c = client.get_collection(coll_meta.name)
                data = c.get(include=["metadatas"])
                total_chunks += len(data["ids"])
                for meta in data.get("metadatas", []):
                    if meta and meta.get("tenant_id"):
                        tenants.add(meta["tenant_id"])
            except Exception:
                pass
        # Calculate folder size
        db_size = sum(
            os.path.getsize(os.path.join(dp, f))
            for dp, _, fs in os.walk(db_path)
            for f in fs
        ) / (1024 * 1024)
        return {
            "collections": len(colls),
            "total_chunks": total_chunks,
            "tenants": sorted(list(tenants)),
            "db_size_mb": round(db_size, 2),
        }
    except Exception as e:
        return {"collections": 0, "total_chunks": 0, "tenants": [], "db_size_mb": 0, "error": str(e)}

def get_latency_stats() -> dict:
    """Compute p50/p95 from last 30 days of daily metric data."""
    metrics = get_system_metrics()
    daily = metrics.get("daily", [])
    if not daily:
        return {"p50": 0, "p95": 0, "avg_errors_day": 0, "total_api_errors": 0}
    p50s = [d.get("p50_latency_ms", 0) for d in daily]
    p95s = [d.get("p95_latency_ms", 0) for d in daily]
    errors = [d.get("api_errors", 0) for d in daily]
    return {
        "p50": int(sum(p50s) / len(p50s)),
        "p95": int(sum(p95s) / len(p95s)),
        "avg_errors_day": round(sum(errors) / len(errors), 1),
        "total_api_errors": sum(errors),
    }


# ─────────────────── CRUD: Demo Bookings & Leads ───────────────────

LEADS_FILE = os.path.join(ADMIN_DATA_DIR, "leads.json")

def get_all_leads() -> list:
    _ensure_data_dir()
    if not os.path.exists(LEADS_FILE):
        # Seed default mock leads
        mock_leads = [
            {
                "id": "lead_9A38",
                "first_name": "Rajesh",
                "last_name": "Kumar",
                "email": "rajesh@tcs.com",
                "phone": "+91 99887 76655",
                "sector": "Information Technology",
                "rfps_per_year": "50-200",
                "status": "New",
                "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "source": "Demo Booking Form"
            },
            {
                "id": "lead_1B82",
                "first_name": "Sarah",
                "last_name": "Jenkins",
                "email": "sarah@hcl.com",
                "phone": "+1 415 889 0021",
                "sector": "SaaS Enterprise",
                "rfps_per_year": "More than 200",
                "status": "Contacted",
                "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
                "source": "pricing_scale"
            }
        ]
        _save_json(LEADS_FILE, mock_leads)
        return mock_leads
    return _load_json(LEADS_FILE)

def add_lead(first_name: str, last_name: str, email: str, phone: str = "", sector: str = "", rfps: str = "", source: str = "Demo Booking Form") -> bool:
    leads = get_all_leads()
    # Check if lead already exists
    for l in leads:
        if l["email"].lower() == email.lower():
            return False
            
    new_lead = {
        "id": f"lead_{random.randint(1000, 9999):X}",
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "sector": sector,
        "rfps_per_year": rfps,
        "status": "New",
        "created_at": datetime.now().isoformat(),
        "source": source
    }
    leads.append(new_lead)
    _save_json(LEADS_FILE, leads)
    return True

def update_lead_status(email: str, status: str) -> bool:
    leads = get_all_leads()
    for l in leads:
        if l["email"].lower() == email.lower():
            l["status"] = status
            _save_json(LEADS_FILE, leads)
            return True
    return False

def delete_lead(email: str) -> bool:
    leads = get_all_leads()
    initial_len = len(leads)
    leads = [l for l in leads if l["email"].lower() != email.lower()]
    if len(leads) == initial_len:
        return False
    _save_json(LEADS_FILE, leads)
    return True

def convert_lead_to_user(email: str) -> bool:
    """Converts a lead into a registered trial user inside users.json."""
    leads = get_all_leads()
    lead_to_convert = None
    for l in leads:
        if l["email"].lower() == email.lower():
            lead_to_convert = l
            break
            
    if not lead_to_convert:
        return False
        
    users = get_all_users()
    uname = email.split("@")[0].replace(".", "_")
    if uname in users:
        return False # user already exists
        
    now_str = datetime.now().strftime("%Y-%m-%d")
    users[uname] = {
        "username": uname,
        "name": f"{lead_to_convert['first_name']} {lead_to_convert['last_name']}",
        "email": lead_to_convert["email"],
        "company": lead_to_convert.get("sector", "Converted Lead"),
        "plan": "trial",
        "status": "trial",
        "is_admin": False,
        "created_at": now_str,
        "trial_expires_at": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "subscription_id": None,
        "responses_this_month": 0,
        "documents_count": 0,
        "batches_this_month": 0,
        "last_active": now_str,
        "monthly_amount": 0
    }
    _save_json(USERS_FILE, users)
    
    # Update lead status
    update_lead_status(email, "Converted")
    return True
