from pydantic_settings import BaseSettings
from pydantic import AnyUrl

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://app:app@localhost:5432/ai_testing"
    dev_bypass_auth: bool = True
    require_mfa: bool = False
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
