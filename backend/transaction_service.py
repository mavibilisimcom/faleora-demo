from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal,ROUND_HALF_UP
class CheckoutError(ValueError):pass
def money(v):return Decimal(str(v)).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)
@dataclass(frozen=True)
class CheckoutInput:
 order_id:int
 order_total:Decimal
 paid_total:Decimal
 stock_cost:Decimal
 reward:int=0
def validate_checkout(x:CheckoutInput):
 if x.order_id<1:raise CheckoutError("Geçersiz adisyon")
 if money(x.order_total)<0 or money(x.paid_total)<0 or money(x.stock_cost)<0:raise CheckoutError("Negatif tutar")
 if money(x.paid_total)<money(x.order_total):raise CheckoutError("Ödeme tamamlanmadı")
 return {"order_id":x.order_id,"status":"closed","order_total":money(x.order_total),"paid_total":money(x.paid_total),"change":money(x.paid_total-x.order_total),"stock_cost":money(x.stock_cost),"gross_margin":money(x.order_total-x.stock_cost),"reward":max(0,x.reward)}
