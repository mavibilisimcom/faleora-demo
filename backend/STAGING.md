# FALEORA Backend Staging

Required environment: DATABASE_URL should use PostgreSQL; CORS_ORIGINS should contain approved frontends; NOTIFICATION_MODE remains dry_run during pilot.

Deployment gate:
1. Provision PostgreSQL.
2. Store secrets in the hosting provider secret store.
3. Run Alembic migrations.
4. Run pytest.
5. Start uvicorn run:app.
6. Verify health/API smoke tests.
7. Keep notification providers in dry_run until test recipients are approved.
8. Enable backups, TLS, logs, metrics and error tracking.

Never commit real provider keys, passwords or production tokens.
