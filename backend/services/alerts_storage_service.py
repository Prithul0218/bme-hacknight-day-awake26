"""Alerts storage service for quick dropdown alerts."""

import json
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
        return {"alerts": {}, "triggers": []}

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
