"""
Configuration settings for the PRAT application
"""

from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str

    # AI/LLM Configuration
    openai_api_key: str
    anthropic_api_key: str = ""
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000

    # OCR Configuration
    ocr_service_key: str = ""
    tesseract_cmd: str = "/usr/local/bin/tesseract"

    # Business Rules
    auto_approve_threshold: float = 1000.00
    require_manual_review_threshold: float = 5000.00
    max_overage_percentage: float = 10.0
    max_tax_rate: float = 0.15

    # File Storage
    upload_dir: str = "uploads"
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: Union[str, List[str]] = "pdf,png,jpg,jpeg,tiff"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = "PRAT - Pay Request Approval Tool"
    backend_cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    # External Services
    po_api_url: str = "https://api.company.com/purchase-orders"
    vendor_api_url: str = "https://api.company.com/vendors"

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def assemble_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
