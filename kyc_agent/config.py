"""
Configuration for KYC Onboarding Agent MCP Server.
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
    chroma_collection_prefix: str = "kyc"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs (real implementations would hit live endpoints) ---
    jumio_api_url: str = "https://api.jumio.com"
    jumio_api_key: str = ""
    ofac_api_url: str = "https://api.ofac.gov"
    core_banking_api_url: str = "https://api.corebanking.internal"
    core_banking_api_key: str = ""
    compliance_api_url: str = "https://api.compliance.internal"
    notification_api_url: str = "https://api.notifications.internal"

    # --- Risk Thresholds ---
    auto_approve_max_risk_score: float = 0.3
    manual_review_min_risk_score: float = 0.3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
