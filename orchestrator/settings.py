# Destination: patches/v2.0.0/orchestrator/settings.py
# Rationale: Centralize all environment variables and configuration
# Single source of truth for all settings across the application

import os
from typing import Optional, List
from pathlib import Path
from pydantic import BaseSettings, Field, validator
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic BaseSettings for validation and type conversion.
    """
    
    # Application
    app_name: str = "AI Testing Orchestrator"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8080, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Database
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    db_url: Optional[str] = Field(default=None, env="DB_URL")
    db_dsn: Optional[str] = Field(default=None, env="DB_DSN")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="orchestrator", env="POSTGRES_DB")
    
    # Redis
    redis_url: Optional[str] = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # OPA (Policy Engine)
    opa_url: str = Field(default="http://localhost:8181", env="OPA_URL")
    opa_enabled: bool = Field(default=False, env="OPA_ENABLED")
    opa_decision_path: str = Field(default="/v1/data/orchestrator/authz/allow", env="OPA_DECISION_PATH")
    
    # Storage
    evidence_dir: str = Field(default="/evidence", env="EVIDENCE_DIR")
    upload_max_size: int = Field(default=100 * 1024 * 1024, env="UPLOAD_MAX_SIZE")  # 100MB
    artifacts_retention_days: int = Field(default=90, env="ARTIFACTS_RETENTION_DAYS")
    
    # Security
    secret_key: str = Field(default="change-me-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # AI/Brain Providers
    brain_provider: str = Field(default="heuristic", env="BRAIN_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=2000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-opus-20240229", env="ANTHROPIC_MODEL")
    anthropic_max_tokens: int = Field(default=4000, env="ANTHROPIC_MAX_TOKENS")
    
    # Reporter Service
    reporter_url: Optional[str] = Field(default=None, env="REPORTER_URL")
    reporter_timeout: int = Field(default=30, env="REPORTER_TIMEOUT")
    enable_pdf_reports: bool = Field(default=False, env="ENABLE_PDF_REPORTS")
    
    # Agent Configuration
    orch_url: str = Field(default="http://localhost:8080", env="ORCH_URL")
    agent_heartbeat_interval: int = Field(default=30, env="AGENT_HEARTBEAT_INTERVAL")
    agent_lease_duration: int = Field(default=300, env="AGENT_LEASE_DURATION")
    agent_max_retries: int = Field(default=3, env="AGENT_MAX_RETRIES")
    
    # Testing/Scanning Limits
    allow_active_scan: bool = Field(default=False, env="ALLOW_ACTIVE_SCAN")
    allow_exploitation: bool = Field(default=False, env="ALLOW_EXPLOITATION")
    max_parallel_jobs: int = Field(default=10, env="MAX_PARALLEL_JOBS")
    job_timeout_seconds: int = Field(default=3600, env="JOB_TIMEOUT_SECONDS")
    
    # Quotas
    enable_quotas: bool = Field(default=True, env="ENABLE_QUOTAS")
    default_tenant_quota: int = Field(default=100, env="DEFAULT_TENANT_QUOTA")
    default_user_quota: int = Field(default=10, env="DEFAULT_USER_QUOTA")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # UI Configuration
    ui_enabled: bool = Field(default=True, env="UI_ENABLED")
    ui_path: str = Field(default="/ui", env="UI_PATH")
    serve_static: bool = Field(default=True, env="SERVE_STATIC")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("database_url", always=True)
    def construct_database_url(cls, v, values):
        """Construct database URL from components if not directly provided."""
        if v:
            # Handle postgres:// to postgresql:// conversion
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql://", 1)
            return v
        
        # Try alternative environment variables
        for alt in ["db_url", "db_dsn"]:
            if alt in values and values[alt]:
                url = values[alt]
                if url.startswith("postgres://"):
                    return url.replace("postgres://", "postgresql://", 1)
                return url
        
        # Construct from components
        user = values.get("postgres_user", "postgres")
        password = values.get("postgres_password", "postgres")
        host = values.get("postgres_host", "localhost")
        port = values.get("postgres_port", 5432)
        db = values.get("postgres_db", "orchestrator")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    @validator("redis_url", always=True)
    def construct_redis_url(cls, v, values):
        """Construct Redis URL from components if not directly provided."""
        if v:
            return v
        
        host = values.get("redis_host", "localhost")
        port = values.get("redis_port", 6379)
        db = values.get("redis_db", 0)
        
        return f"redis://{host}:{port}/{db}"
    
    @property
    def evidence_path(self) -> Path:
        """Get evidence directory as Path object."""
        return Path(self.evidence_dir)
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ("development", "dev")
    
    @property
    def brain_enabled(self) -> bool:
        """Check if any AI brain provider is configured."""
        return bool(self.openai_api_key or self.anthropic_api_key)
    
    @property
    def pdf_enabled(self) -> bool:
        """Check if PDF report generation is available."""
        return self.enable_pdf_reports and bool(self.reporter_url)
    
    def get_database_url(self, async_driver: bool = False) -> str:
        """
        Get database URL with optional async driver.
        
        Args:
            async_driver: If True, return URL for async driver (asyncpg)
        
        Returns:
            Database URL string
        """
        url = self.database_url
        if async_driver and url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Create a global settings instance
settings = get_settings()

# Export commonly used settings
DATABASE_URL = settings.database_url
REDIS_URL = settings.redis_url
OPA_URL = settings.opa_url
EVIDENCE_DIR = settings.evidence_dir
ORCH_URL = settings.orch_url
SECRET_KEY = settings.secret_key