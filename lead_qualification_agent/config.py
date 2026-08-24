"""
Configuration for Lead Qualification Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "lead_qual"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    crm_api_url: str = "https://api.salesforce.internal"
    lead_scoring_api_url: str = "https://api.leadscore.internal"
    calendar_api_url: str = "https://api.calendar.internal"
    notification_api_url: str = "https://api.notifications.internal"
    enrichment_api_url: str = "https://api.enrichment.internal"

    # --- Lead Qualification Parameters ---
    min_lead_score: int = 30
    auto_qualify_score: int = 80
    routing_threshold: int = 60
    max_qualification_attempts: int = 3
    lead_expiry_days: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
