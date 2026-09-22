from __future__ import annotations
import os
from urllib.parse import urlparse
def evaluate():
 db=os.getenv("DATABASE_URL","")
 secret=os.getenv("AUTH_SECRET","")
 origins=os.getenv("FRONTEND_ORIGINS","")
 env=os.getenv("APP_ENV","development")
 checks={
  "app_env_not_development":env not in {"","development"},
  "postgresql":db.startswith("postgresql"),
  "auth_secret":len(secret)>=32 and "replace" not in secret.lower() and "change-me" not in secret.lower(),
  "cors_explicit":bool(origins) and "*" not in origins,
  "notification_safe":os.getenv("NOTIFICATION_MODE","dry_run") in {"dry_run","live"},
 }
 return {"ready":all(checks.values()),"checks":checks}
if __name__=="__main__":
 import json;print(json.dumps(evaluate(),indent=2))
