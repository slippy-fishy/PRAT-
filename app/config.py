"""
Configuration settings for the PRAT application
"""

from typing import List, Union, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

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

    # Folder monitoring settings
    po_folder_path: str = Field(default="purchase_orders", description="Path to PO folder")
    invoice_folder_path: str = Field(default="invoices", description="Path to invoice folder")
    processed_folder_path: str = Field(default="processed", description="Path to processed files")
    enable_folder_watching: bool = Field(default=True, description="Enable automatic folder monitoring")
    scan_interval_seconds: int = Field(default=30, description="Folder scan interval in seconds")
    keep_deleted_pos: bool = Field(default=True, description="Keep deleted POs in database (mark as deleted)")
    
    # Database settings
    database_url: Optional[str] = Field(default=None, description="Database connection URL")
    database_host: str = Field(default="localhost", description="Database host")
    database_port: int = Field(default=5432, description="Database port")
    database_name: str = Field(default="prat", description="Database name")
    database_user: str = Field(default="prat_user", description="Database user")
    database_password: str = Field(default="", description="Database password")

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

    # Debug Mode
    debug: bool = Field(default=False, description="Enable debug mode")

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

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_database_url(cls, v, info):
        """Assemble database URL from components if not provided"""
        if v:
            return v
        
        # Build from components
        host = info.data.get("database_host", "localhost")
        port = info.data.get("database_port", 5432)
        name = info.data.get("database_name", "prat")
        user = info.data.get("database_user", "prat_user")
        password = info.data.get("database_password", "")
        
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"
        else:
            return f"postgresql://{user}@{host}:{port}/{name}"
    
    @field_validator("po_folder_path", "invoice_folder_path", "processed_folder_path")
    @classmethod
    def validate_folder_paths(cls, v):
        """Ensure folder paths are absolute or relative to project root"""
        if os.path.isabs(v):
            return v
        else:
            # Make relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(project_root, v)

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
