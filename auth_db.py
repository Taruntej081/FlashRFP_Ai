import sqlite3
from datetime import datetime, timedelta

# Create local database file
conn = sqlite3.connect('flashrfp_users.db', check_same_thread=False)
c = conn.cursor()

# Create table if not exists
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        trial_start_date TEXT,
        plan TEXT DEFAULT 'trial'
    )
''')
conn.commit()

def add_user(email):
    """Adds a new user and starts their 7-day trial if they do not exist."""
    try:
        c.execute("INSERT INTO users (email, trial_start_date, plan) VALUES (?, ?, ?)", 
                  (email, datetime.now().isoformat(), 'trial'))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # User already exists

def check_trial_status(email):
    """Returns (is_active, plan). is_active is True if trial is active or user paid."""
    c.execute("SELECT trial_start_date, plan FROM users WHERE email=?", (email,))
    row = c.fetchone()
    
    if not row:
        # Default to trial starting now if user not in db yet
        add_user(email)
        return True, "trial"
    
    start_date_str, plan = row
    if plan != 'trial':
        return True, plan  # Paid users are always active
        
    start_date = datetime.fromisoformat(start_date_str)
    expiry_date = start_date + timedelta(days=7)
    
    if datetime.now() > expiry_date:
        return False, 'trial_expired'
    else:
        return True, 'trial'

def upgrade_user_plan(email, new_plan):
    """Manually upgrades a user plan in the local SQLite db."""
    c.execute("UPDATE users SET plan=? WHERE email=?", (new_plan, email))
    conn.commit()

def get_trial_days_remaining(email):
    """Calculates remaining days in the 7-day trial. Returns 0 if expired or paid plan."""
    c.execute("SELECT trial_start_date, plan FROM users WHERE email=?", (email,))
    row = c.fetchone()
    if not row:
        return 7
    start_date_str, plan = row
    if plan != 'trial':
        return 0
    start_date = datetime.fromisoformat(start_date_str)
    expiry_date = start_date + timedelta(days=7)
    diff = expiry_date - datetime.now()
    remaining = diff.days + 1  # count starting day
    return max(0, remaining)

