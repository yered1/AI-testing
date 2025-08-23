# File: AI-testing/orchestrator/settings.py

- Size: 422 bytes
- Kind: text
- SHA256: 4b2c7178711a81a7302a64fa7ba8c73eac377a08adac5d23368c59f364e7504d

## Python Imports

```
pydantic_settings
```

## Head (first 60 lines)

```
from pydantic_settings import BaseSettings

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
```

