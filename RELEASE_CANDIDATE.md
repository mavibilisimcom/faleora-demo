# FALEORA Release Candidate Demo

## Product architecture
Consumer App + Hospitality OS + Venue/Table/Screen + Grow + Intelligence + Enterprise.

## Repository-ready foundations
POS/orders, KDS, venue tables/service requests, stock movement ledger, versioned recipes, modifiers, payments ledger, cash shifts, audit events, RBAC authorization model, reservations/waitlist, purchasing/suppliers, workforce scheduling, screen network, notification campaigns, venue profiles, readers/rewards/circles, user profile/consent/archive, operations events/checklists and checkout finalization.

## Engineering foundations
Dockerfile, PostgreSQL driver, Alembic scaffold, pytest, GitHub Actions CI, environment-driven database configuration, staging checklist and health endpoints.

## External production gates
Real identity provider/authentication, provisioned PostgreSQL staging database, consolidated schema migrations, payment sandbox/production credentials, SMTP/SMS/WhatsApp/Push credentials, object/media storage, monitoring/error tracking, automated backups/restore test, TLS/domain, native iOS/Android builds and store accounts.

## Truth rule
A demo page is not production readiness. A backend foundation is not a deployed service. Production is declared only after staging integration, security and concurrency tests pass with real external providers.
