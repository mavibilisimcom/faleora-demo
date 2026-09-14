from main import app, scheduler, send_notification
from occasion_notifications import process_due_occasions, router as occasion_router
from notification_campaigns import process_scheduled_campaigns, router as campaign_router

app.include_router(occasion_router)
app.include_router(campaign_router)

scheduler.add_job(
    lambda: process_due_occasions(send_notification),
    "cron",
    hour=10,
    minute=0,
    id="occasion_notifications",
    replace_existing=True,
)

scheduler.add_job(
    lambda: process_scheduled_campaigns(send_notification),
    "interval",
    minutes=5,
    id="scheduled_notification_campaigns",
    replace_existing=True,
)
