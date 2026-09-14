from main import app, scheduler, send_notification
from occasion_notifications import process_due_occasions, router as occasion_router

app.include_router(occasion_router)
scheduler.add_job(
    lambda: process_due_occasions(send_notification),
    "cron",
    hour=10,
    minute=0,
    id="occasion_notifications",
    replace_existing=True,
)
