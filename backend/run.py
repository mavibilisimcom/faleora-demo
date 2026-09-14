from main import app, scheduler
from occasion_notifications import process_due_occasions, router as occasion_router
from notification_campaigns import process_scheduled_campaigns, router as campaign_router
from provider_dispatch import dispatch_notification
from providers_admin import router as provider_router
from venue_profiles import router as venue_profile_router
from marketplace import router as marketplace_router
from user_data import router as user_router

app.include_router(occasion_router)
app.include_router(campaign_router)
app.include_router(provider_router)
app.include_router(venue_profile_router)
app.include_router(marketplace_router)
app.include_router(user_router)

scheduler.add_job(lambda: process_due_occasions(dispatch_notification),'cron',hour=10,minute=0,id='occasion_notifications',replace_existing=True)
scheduler.add_job(lambda: process_scheduled_campaigns(dispatch_notification),'interval',minutes=5,id='scheduled_notification_campaigns',replace_existing=True)
