"""Unified configuration management for AI-Testing platform"""

import os
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/ai_testing",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    # Security
    secret_key: str = Field(
        default="change-me-in-production",
        env="SECRET_KEY"
    )
    allow_active_scan: bool = Field(
        default=False,
        env="ALLOW_ACTIVE_SCAN"
    )
    
    # Storage
    evidence_dir: str = Field(
        default="/tmp/evidence",
        env="EVIDENCE_DIR"
    )
    
    # API
    api_version: str = "v2"
    deprecate_v1: bool = Field(
        default=False,
        env="DEPRECATE_V1_API"
    )
    
    # AI/Brain
    openai_api_key: Optional[str] = Field(
        default=None,
        env="OPENAI_API_KEY"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        env="ANTHROPIC_API_KEY"
    )
    
    # Features
    enable_ui: bool = Field(
        default=True,
        env="ENABLE_UI"
    )
    enable_rbac: bool = Field(
        default=False,
        env="ENABLE_RBAC"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton instance
settings = Settings()
