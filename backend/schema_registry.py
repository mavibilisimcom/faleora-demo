"""Alembic için mevcut FALEORA modül metadata kayıtları.
Yeni domain konsolidasyonu tamamlanana kadar migration autogenerate tüm mevcut tabloları görür.
"""
from sqlalchemy import MetaData
from main import Base as main_base
from auth import B as auth_base
from pos_core import B as pos_base
from operations import B as ops_base
from commercial_core import B as commercial_base
from menu_engine import B as menu_base
from payments_core import B as payment_base
from checkout_orchestrator import B as checkout_base
from reservations import B as reservation_base
from purchasing import B as purchasing_base
from workforce import B as workforce_base
from offline_sync import B as sync_base
from sales_engine import B as sales_base
from pilot_core import B as pilot_base
from cash_reconciliation import B as cash_base
from pilot_transaction import B as tx_base
from finance_core import B as finance_base
from expense_documents import B as document_base
metadata=MetaData()
for base in [main_base,auth_base,pos_base,ops_base,commercial_base,menu_base,payment_base,checkout_base,reservation_base,purchasing_base,workforce_base,sync_base,sales_base,pilot_base,cash_base,tx_base,finance_base,document_base]:
 for table in base.metadata.tables.values():
  table.to_metadata(metadata)
