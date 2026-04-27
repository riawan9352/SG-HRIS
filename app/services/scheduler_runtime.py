from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import SessionLocal
from app.services.workload_scheduler import run_due_workload_schedules

scheduler = BackgroundScheduler(timezone="Asia/Makassar")


def _scheduled_workload_job() -> None:
    db = SessionLocal()
    try:
        run_due_workload_schedules(db)
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        _scheduled_workload_job,
        trigger="interval",
        minutes=60,
        id="workload_due_refresh",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
