from decimal import Decimal
import pytest
from transaction_service import CheckoutInput,CheckoutError,validate_checkout
def test_checkout_exact_payment():
 x=validate_checkout(CheckoutInput(1,Decimal("100"),Decimal("100"),Decimal("35"),5))
 assert x["status"]=="closed" and x["gross_margin"]==Decimal("65.00")
def test_checkout_change():
 x=validate_checkout(CheckoutInput(2,Decimal("90"),Decimal("100"),Decimal("30")))
 assert x["change"]==Decimal("10.00")
def test_checkout_rejects_underpayment():
 with pytest.raises(CheckoutError):validate_checkout(CheckoutInput(3,Decimal("100"),Decimal("99.99"),Decimal("20")))
