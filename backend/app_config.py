import os
from pydantic_settings import BaseSettings,SettingsConfigDict
class AppConfig(BaseSettings):
 app_env:str="development"
 database_url:str="sqlite:///./faleora.db"
 frontend_origins:str="https://mavibilisimcom.github.io"
 auth_mode:str="development"
 auth_secret:str="change-me-in-staging"
 model_config=SettingsConfigDict(env_file=".env",extra="ignore")
config=AppConfig()
