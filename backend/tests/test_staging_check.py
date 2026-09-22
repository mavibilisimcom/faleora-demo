import os
from staging_check import evaluate
def test_default_environment_is_not_production_ready(monkeypatch):
 for k in ["DATABASE_URL","AUTH_SECRET","FRONTEND_ORIGINS","APP_ENV"]:monkeypatch.delenv(k,raising=False)
 assert evaluate()["ready"] is False
def test_good_staging_environment(monkeypatch):
 monkeypatch.setenv("DATABASE_URL","postgresql+psycopg://u:p@db/faleora")
 monkeypatch.setenv("AUTH_SECRET","x"*40)
 monkeypatch.setenv("FRONTEND_ORIGINS","https://staging.example.test")
 monkeypatch.setenv("APP_ENV","staging")
 assert evaluate()["ready"] is True
