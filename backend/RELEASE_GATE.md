# Release Gate

## Repo gate
- Backend CI: green
- PostgreSQL CI smoke: green
- Auth tests: green
- Checkout/sales tests: green
- Offline idempotency: green
- Realtime WebSocket: green
- Recipe/stock consumption: green
- Cash reconciliation: green
- Finance/documents: green
- Readiness logic: green

## Staging gate
- Real PostgreSQL
- Alembic migration review + upgrade
- HTTPS
- Secret manager
- Backup/restore drill
- Monitoring
- Full pilot smoke

## Provider gate
- Payment sandbox
- E-document integrator
- Messaging providers
- Media storage

## Release rule
Repo gate geçmesi staging veya production yayınının geçtiği anlamına gelmez. Staging ve provider gate'leri ayrıca kanıtlanmalıdır.
