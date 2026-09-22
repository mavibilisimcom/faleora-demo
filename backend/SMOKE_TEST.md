# Staging Smoke

1. GET /health -> status ok
2. GET /ready -> ready true
3. POST /api/auth/register (pilot test account)
4. POST /api/auth/login
5. Create/open cash shift
6. Create sale with modifier
7. Send kitchen
8. Partial + final payment
9. Verify closed sale
10. Verify recipe consumption is idempotent
11. Verify audit event
12. Close cash shift and reconcile
13. Create finance income/expense
14. Create expense document draft and approve
15. Disconnect client, queue offline event, reconnect and verify duplicate protection
16. Open venue WebSocket and verify ORDER_READY event

Pilot data must be isolated from production data.
