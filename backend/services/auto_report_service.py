import asyncio
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from backend.services.auth_service import load_users

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DB_PATH = BASE_DIR / "data" / "auto_reports.json"

_scheduler_task: Optional[asyncio.Task] = None


ROLE_AUDIENCE_HINTS = {
    "engineering": "Infrastructure costs, tooling spend, and R&D burn trend",
    "sales": "Revenue momentum, pipeline signals, and commission-impacting metrics",
    "marketing": "Campaign efficiency, CAC signals, and spend allocation",
    "hr": "Payroll trend, hiring burn, and benefits pressure points",
    "operations": "Vendor spend health, procurement signals, and process costs",
    "executive": "Top-line trajectory, risk posture, and strategic KPIs",
    "finance": "Cash runway, variance movements, and liquidity watchpoints",
    "management": "Cross-team spend posture and execution risk overview",
    "admin": "Platform-wide control summary and governance posture",
    "employee": "Business health snapshot relevant to your team",
}


def _utc_now() -> datetime:
    return datetime.utcnow()


def ensure_reports_db() -> None:
    REPORTS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not REPORTS_DB_PATH.exists():
        REPORTS_DB_PATH.write_text("[]", encoding="utf-8")


def _load_reports() -> List[Dict]:
    ensure_reports_db()
    raw = REPORTS_DB_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    return data if isinstance(data, list) else []


def _save_reports(reports: List[Dict]) -> None:
    REPORTS_DB_PATH.write_text(json.dumps(reports, indent=2), encoding="utf-8")


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def _get_frequency_days(user: Dict) -> int:
    try:
        value = int(user.get("report_frequency_days", 7))
    except (TypeError, ValueError):
        value = 7
    return max(1, value)


def _get_audience_key(user: Dict) -> str:
    department = user.get("department")
    if department:
        return str(department)
    return str(user.get("role", "employee"))


def _build_report_for_user(user: Dict, generated_at: datetime, total_docs: int) -> Dict:
    frequency_days = _get_frequency_days(user)
    audience_key = _get_audience_key(user)
    hint = ROLE_AUDIENCE_HINTS.get(audience_key, ROLE_AUDIENCE_HINTS["employee"])

    title = f"Auto Report: {audience_key.title()} Update ({generated_at.strftime('%b %d, %Y')})"
    summary = (
        f"Generated automatically for {user.get('name')} ({audience_key}). "
        f"Focus: {hint}. Current tracked docs: {total_docs}."
    )

    highlights = [
        f"Cadence set to every {frequency_days} day(s)",
        f"Audience context: {audience_key}",
        f"Document baseline at generation time: {total_docs}",
    ]

    return {
        "report_id": str(uuid.uuid4()),
        "user_id": user.get("user_id"),
        "user_name": user.get("name"),
        "audience": audience_key,
        "title": title,
        "summary": summary,
        "highlights": highlights,
        "generated_at": generated_at.isoformat(),
        "next_due_at": (generated_at + timedelta(days=frequency_days)).isoformat(),
        "frequency_days": frequency_days,
    }


def _is_due_for_user(existing_reports: List[Dict], user: Dict, now: datetime) -> bool:
    user_reports = [r for r in existing_reports if r.get("user_id") == user.get("user_id")]
    if not user_reports:
        return True

    latest = max(user_reports, key=lambda r: r.get("generated_at", ""))
    next_due_raw = latest.get("next_due_at")
    if not next_due_raw:
        return True

    try:
        return _parse_iso(next_due_raw) <= now
    except ValueError:
        return True


def _get_current_document_count() -> int:
    # Import lazily to avoid import cycles at startup.
    try:
        from backend.routers import reports as reports_router

        return len(getattr(reports_router, "file_metadata_store", {}))
    except Exception:
        return 0


def run_generation_cycle() -> int:
    users = [u for u in load_users() if bool(u.get("is_active", True))]
    reports = _load_reports()
    now = _utc_now()
    created = 0
    total_docs = _get_current_document_count()

    for user in users:
        if _is_due_for_user(reports, user, now):
            reports.append(_build_report_for_user(user, now, total_docs))
            created += 1

    if created > 0:
        _save_reports(reports)

    return created


async def _scheduler_loop(interval_seconds: int) -> None:
    while True:
        try:
            created = run_generation_cycle()
            if created:
                print(f"[auto-reports] generated {created} report(s)")
        except Exception as exc:
            print(f"[auto-reports] scheduler error: {exc}")

        await asyncio.sleep(interval_seconds)


def start_scheduler(interval_seconds: int = 3600) -> None:
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        return

    ensure_reports_db()
    run_generation_cycle()
    _scheduler_task = asyncio.create_task(_scheduler_loop(interval_seconds))


def stop_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()
    _scheduler_task = None


def get_reports_for_user(user: Dict) -> List[Dict]:
    reports = _load_reports()
    role = str(user.get("role", "")).lower()

    if role == "admin":
        visible = reports
    else:
        visible = [r for r in reports if r.get("user_id") == user.get("user_id")]

    return sorted(visible, key=lambda r: r.get("generated_at", ""), reverse=True)
