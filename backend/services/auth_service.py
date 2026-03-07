import json
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
USERS_DB_PATH = BASE_DIR / "data" / "users.json"

SEED_USERS = [
    {
        "user_id": "u_admin_001",
        "name": "Admin User",
        "email": "admin@finesse.local",
        "password": "1234",
        "role": "admin",
        "department": None,
        "report_frequency_days": 7,
        "is_active": True,
    },
    {
        "user_id": "u_mgmt_001",
        "name": "Management User",
        "email": "management@finesse.local",
        "password": "1234",
        "role": "management",
        "department": None,
        "report_frequency_days": 7,
        "is_active": True,
    },
    {
        "user_id": "u_fin_001",
        "name": "Finance User",
        "email": "finance@finesse.local",
        "password": "1234",
        "role": "finance",
        "department": None,
        "report_frequency_days": 7,
        "is_active": True,
    },
    {
        "user_id": "u_emp_001",
        "name": "Employee User",
        "email": "employee@finesse.local",
        "password": "1234",
        "role": "employee",
        "department": "engineering",
        "report_frequency_days": 7,
        "is_active": True,
    },
]


def ensure_users_db() -> None:
    """Create JSON user database with seed users if it does not exist."""
    USERS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_DB_PATH.exists():
        USERS_DB_PATH.write_text(json.dumps(SEED_USERS, indent=2), encoding="utf-8")


def load_users() -> List[Dict]:
    ensure_users_db()
    raw = USERS_DB_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    return data if isinstance(data, list) else []


def get_user_by_email(email: str) -> Optional[Dict]:
    email_normalized = (email or "").strip().lower()
    for user in load_users():
        if str(user.get("email", "")).strip().lower() == email_normalized:
            return user
    return None


def get_user_by_id(user_id: str) -> Optional[Dict]:
    for user in load_users():
        if user.get("user_id") == user_id:
            return user
    return None


def sanitize_user(user: Dict) -> Dict:
    """Remove password before returning user info to handlers/clients."""
    return {
        "user_id": user.get("user_id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "department": user.get("department"),
        "report_frequency_days": int(user.get("report_frequency_days", 7) or 7),
        "is_active": bool(user.get("is_active", True)),
    }


def authenticate_user(email: str, password: str) -> Optional[Dict]:
    user = get_user_by_email(email)
    if not user:
        return None
    if not bool(user.get("is_active", True)):
        return None
    if str(user.get("password", "")) != str(password or ""):
        return None
    return user
