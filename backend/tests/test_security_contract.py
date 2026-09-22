from staging_check import evaluate
def test_readiness_rejects_weak_secret(monkeypatch):
 monkeypatch.setenv("APP_ENV","staging");monkeypatch.setenv("DATABASE_URL","postgresql+psycopg://u:p@db/x");monkeypatch.setenv("AUTH_SECRET","short");monkeypatch.setenv("FRONTEND_ORIGINS","https://x.test")
 assert evaluate()["ready"] is False
def test_readiness_rejects_wildcard_cors(monkeypatch):
 monkeypatch.setenv("APP_ENV","staging");monkeypatch.setenv("DATABASE_URL","postgresql+psycopg://u:p@db/x");monkeypatch.setenv("AUTH_SECRET","x"*40);monkeypatch.setenv("FRONTEND_ORIGINS","*")
 assert evaluate()["ready"] is False
