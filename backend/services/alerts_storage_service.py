"""Alerts storage service for quick dropdown alerts."""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ALERTS_DB_PATH = DATA_DIR / "alerts.json"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_alerts_database() -> Dict:
    ensure_data_dir()
    if not ALERTS_DB_PATH.exists():
        db = {"alerts": {}, "triggers": []}
        _populate_sample_triggers(db)
        save_alerts_database(db)
        return db

    try:
        with open(ALERTS_DB_PATH, "r") as f:
            data = json.load(f)
            data.setdefault("alerts", {})
            data.setdefault("triggers", [])
            return data
    except Exception as e:
        print(f"⚠️ Failed to load alerts database: {e}")
        return {"alerts": {}, "triggers": []}


def save_alerts_database(data: Dict) -> None:
    ensure_data_dir()
    try:
        with open(ALERTS_DB_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ Failed to save alerts database: {e}")


def create_alert(alert_payload: Dict) -> Dict:
    data = load_alerts_database()
    alert_id = alert_payload["alert_id"]
    data["alerts"][alert_id] = alert_payload
    save_alerts_database(data)
    return alert_payload


def list_alerts_for_user(user_id: str, role: str) -> List[Dict]:
    data = load_alerts_database()
    alerts = list(data.get("alerts", {}).values())

    # Admin can inspect all alerts; everyone else sees only theirs.
    if role == "admin":
        visible = alerts
    else:
        visible = [a for a in alerts if a.get("created_by") == user_id]

    visible.sort(key=lambda a: a.get("created_at", ""), reverse=True)
    return visible


def get_alert(alert_id: str) -> Optional[Dict]:
    data = load_alerts_database()
    return data.get("alerts", {}).get(alert_id)


def update_alert_status(alert_id: str, status: str) -> Optional[Dict]:
    data = load_alerts_database()
    alert = data.get("alerts", {}).get(alert_id)
    if not alert:
        return None

    alert["status"] = status
    alert["updated_at"] = datetime.now().isoformat()
    data["alerts"][alert_id] = alert
    save_alerts_database(data)
    return alert


def delete_alert(alert_id: str) -> bool:
    data = load_alerts_database()
    if alert_id not in data.get("alerts", {}):
        return False

    del data["alerts"][alert_id]
    save_alerts_database(data)
    return True


def list_recent_triggers(user_id: str, role: str) -> List[Dict]:
    data = load_alerts_database()
    triggers = data.get("triggers", [])

    if role == "admin":
        visible = triggers
    else:
        visible = [t for t in triggers if t.get("created_by") == user_id]

    visible.sort(key=lambda t: t.get("triggered_at", ""), reverse=True)
    return visible[:20]


def create_triggered_alert(
    alert_name: str,
    severity: str,
    message: str,
    metric: str,
    threshold_value: float,
    actual_value: float,
    created_by: str,
    alert_id: Optional[str] = None
) -> Dict:
    """Create a triggered alert in history"""
    data = load_alerts_database()
    
    trigger_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    trigger_payload = {
        "trigger_id": trigger_id,
        "alert_id": alert_id,
        "alert_name": alert_name,
        "severity": severity,
        "message": message,
        "metric": metric,
        "threshold_value": threshold_value,
        "actual_value": actual_value,
        "triggered_at": now,
        "created_by": created_by,
        "acknowledged": False,
        "acknowledged_by": None,
        "acknowledged_at": None
    }
    
    data.setdefault("triggers", [])
    data["triggers"].append(trigger_payload)
    save_alerts_database(data)
    
    return trigger_payload


def list_triggered_alerts(user_id: str, role: str) -> List[Dict]:
    """List all triggered alerts with sorting: high priority first, then by date"""
    data = load_alerts_database()
    triggers = data.get("triggers", [])
    
    # Filter by role
    if role == "admin" or role == "management":
        visible = triggers
    else:
        visible = [t for t in triggers if t.get("created_by") == user_id]
    
    # Sort: high priority first, then by date (newest first)
    severity_priority = {"high": 0, "medium": 1, "low": 2}
    
    visible.sort(
        key=lambda t: (
            severity_priority.get(t.get("severity", "medium"), 1),
            -datetime.fromisoformat(t.get("triggered_at", "1970-01-01T00:00:00")).timestamp()
        )
    )
    
    return visible


def acknowledge_triggered_alert(trigger_id: str, user_id: str) -> Optional[Dict]:
    """Mark a triggered alert as acknowledged"""
    data = load_alerts_database()
    triggers = data.get("triggers", [])
    
    for trigger in triggers:
        if trigger.get("trigger_id") == trigger_id:
            trigger["acknowledged"] = True
            trigger["acknowledged_by"] = user_id
            trigger["acknowledged_at"] = datetime.now().isoformat()
            save_alerts_database(data)
            return trigger
    
    return None


def _populate_sample_triggers(db: Dict) -> None:
    """Add sample triggered alerts for demonstration purposes"""
    from datetime import timedelta
    
    now = datetime.now()
    
    sample_triggers = [
        {
            "trigger_id": str(uuid.uuid4()),
            "alert_id": None,
            "alert_name": "Revenue Drop Alert",
            "severity": "high",
            "message": "Monthly revenue has dropped by 15% below the threshold",
            "metric": "revenue",
            "threshold_value": 1000000.0,
            "actual_value": 850000.0,
            "triggered_at": (now - timedelta(hours=2)).isoformat(),
            "created_by": "alice",
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None
        },
        {
            "trigger_id": str(uuid.uuid4()),
            "alert_id": None,
            "alert_name": "Operating Expense Spike",
            "severity": "high",
            "message": "Operating expenses exceeded threshold by 22%",
            "metric": "operating_expense",
            "threshold_value": 500000.0,
            "actual_value": 610000.0,
            "triggered_at": (now - timedelta(hours=5)).isoformat(),
            "created_by": "bob",
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None
        },
        {
            "trigger_id": str(uuid.uuid4()),
            "alert_id": None,
            "alert_name": "Budget Variance Warning",
            "severity": "medium",
            "message": "Marketing department budget variance is at 8%",
            "metric": "budget_variance_percent",
            "threshold_value": 5.0,
            "actual_value": 8.2,
            "triggered_at": (now - timedelta(days=1, hours=3)).isoformat(),
            "created_by": "charlie",
            "acknowledged": True,
            "acknowledged_by": "charlie",
            "acknowledged_at": (now - timedelta(days=1, hours=1)).isoformat()
        },
        {
            "trigger_id": str(uuid.uuid4()),
            "alert_id": None,
            "alert_name": "Low Cash Balance",
            "severity": "medium",
            "message": "Cash balance fell below $200k threshold",
            "metric": "cash_balance",
            "threshold_value": 200000.0,
            "actual_value": 185000.0,
            "triggered_at": (now - timedelta(days=2)).isoformat(),
            "created_by": "alice",
            "acknowledged": False,
            "acknowledged_by": None,
            "acknowledged_at": None
        },
        {
            "trigger_id": str(uuid.uuid4()),
            "alert_id": None,
            "alert_name": "Department Spend Notice",
            "severity": "low",
            "message": "IT department spending is approaching monthly limit",
            "metric": "department_spend",
            "threshold_value": 50000.0,
            "actual_value": 48500.0,
            "triggered_at": (now - timedelta(days=3)).isoformat(),
            "created_by": "bob",
            "acknowledged": True,
            "acknowledged_by": "admin",
            "acknowledged_at": (now - timedelta(days=2, hours=20)).isoformat()
        }
    ]
    
    db["triggers"] = sample_triggers
