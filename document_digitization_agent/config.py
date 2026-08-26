"""
Configuration for Document Digitization & Extraction Agent MCP Server.
Loads settings from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "doc_digitization"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- AWS Textract ---
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    # --- Google Cloud Vision ---
    google_application_credentials: str = ""  # Path to service account JSON
    google_project_id: str = ""

    # --- OCR Provider Config ---
    # "textract" | "google_vision" | "auto" (textract first, fallback to google)
    ocr_provider: str = "auto"
    ocr_min_confidence: float = 0.6

    # --- External APIs ---
    notification_api_url: str = "https://api.notifications.internal"
    document_storage_url: str = "https://storage.internal/documents"
    database_write_api_url: str = "https://api.database.internal"

    # --- OCR Quality Thresholds ---
    min_ocr_confidence: float = 0.6
    high_confidence_threshold: float = 0.85
    low_confidence_threshold: float = 0.7

    # --- Extraction Limits ---
    max_document_size_mb: int = 50
    max_pages_per_document: int = 100
    extraction_timeout_seconds: int = 120

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
