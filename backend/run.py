from main import app, scheduler
from occasion_notifications import process_due_occasions, router as occasion_router
from notification_campaigns import process_scheduled_campaigns, router as campaign_router
from provider_dispatch import dispatch_notification
from providers_admin import router as provider_router
from venue_profiles import router as venue_profile_router
from marketplace import router as marketplace_router
from user_data import router as user_router
from screen_network import router as screen_router
from venue_os import router as venue_os_router
from pos_core import router as pos_router
from operations import router as operations_router
from commercial_core import router as commercial_core_router
from access_control import router as access_router
from menu_engine import router as menu_engine_router
from payments_core import router as payments_router
from checkout_orchestrator import router as checkout_router
from reservations import router as reservations_router
from purchasing import router as purchasing_router
from workforce import router as workforce_router
from health import router as health_router
from auth import router as auth_router
from offline_sync import router as offline_sync_router
from sales_engine import router as sales_router
from pilot_core import router as pilot_router
from cash_reconciliation import router as cash_reconciliation_router
from pilot_transaction import router as pilot_transaction_router
from realtime import router as realtime_router
from finance_core import router as finance_router
from expense_documents import router as documents_router
from e_document_connector import router as e_document_router
from observability import request_context_middleware

app.middleware("http")(request_context_middleware)

app.include_router(occasion_router)
app.include_router(campaign_router)
app.include_router(provider_router)
app.include_router(venue_profile_router)
app.include_router(marketplace_router)
app.include_router(user_router)
app.include_router(screen_router)
app.include_router(venue_os_router)
app.include_router(pos_router)
app.include_router(operations_router)
app.include_router(commercial_core_router)
app.include_router(access_router)
app.include_router(menu_engine_router)
app.include_router(payments_router)
app.include_router(checkout_router)
app.include_router(reservations_router)
app.include_router(purchasing_router)
app.include_router(workforce_router)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(offline_sync_router)
app.include_router(sales_router)
app.include_router(pilot_router)
app.include_router(cash_reconciliation_router)
app.include_router(pilot_transaction_router)
app.include_router(realtime_router)
app.include_router(finance_router)
app.include_router(documents_router)
app.include_router(e_document_router)

scheduler.add_job(lambda: process_due_occasions(dispatch_notification),"cron",hour=10,minute=0,id="occasion_notifications",replace_existing=True)
scheduler.add_job(lambda: process_scheduled_campaigns(dispatch_notification),"interval",minutes=5,id="scheduled_notification_campaigns",replace_existing=True)
