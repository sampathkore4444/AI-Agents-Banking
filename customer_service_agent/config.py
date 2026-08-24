"""
Configuration for Customer Service & Support Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "cs"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    core_banking_api_url: str = "https://api.corebanking.internal"
    core_banking_api_key: str = ""
    dispute_management_api_url: str = "https://api.disputes.internal"
    crm_api_url: str = "https://api.crm.internal"
    ticketing_api_url: str = "https://api.tickets.internal"
    notification_api_url: str = "https://api.notifications.internal"
    translation_api_url: str = "https://api.translation.internal"

    # --- Supported Languages ---
    supported_languages: list[str] = ["en", "es", "fr", "de", "zh", "ar", "hi", "pt"]

    # --- Escalation ---
    escalation_email: str = "escalation@bank.com"
    escalation_slack_channel: str = "#cs-escalations"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
