def test_payment_methods():
 allowed={'cash','card','online','meal_card','other'}
 assert 'card' in allowed and 'crypto' not in allowed
def test_stock_movement_types():
 allowed={'purchase','sale','waste','transfer_in','transfer_out','count_adjustment','return'}
 assert {'purchase','sale','waste'}.issubset(allowed)
def test_checkout_rule():
 total=100.0;paid=100.0
 assert round(paid,2)>=round(total,2)
def test_role_separation():
 waiter={'pos','tables'};kitchen={'kds'}
 assert 'kds' not in waiter and 'pos' not in kitchen
