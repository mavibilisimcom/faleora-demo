# PostgreSQL Backup / Restore Drill

Staging pilot öncesinde gerçek ortamda uygulanır.

## Backup
pg_dump --format=custom --no-owner --file=faleora-staging.dump "$DATABASE_URL"

## Verify
pg_restore --list faleora-staging.dump

## Restore drill
Boş bir doğrulama veritabanına restore edilir:
createdb faleora_restore_check
pg_restore --no-owner --dbname="$RESTORE_DATABASE_URL" faleora-staging.dump

Ardından /health, /ready ve pilot smoke akışı çalıştırılır. Restore denenmeden backup özelliği "hazır" sayılmaz.
