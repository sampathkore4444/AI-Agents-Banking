"""
Configuration for Loan Collections Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "collections"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    account_management_api_url: str = "https://api.accounts.internal"
    payment_scheduling_api_url: str = "https://api.payments.internal"
    notification_api_url: str = "https://api.notifications.internal"
    payment_gateway_api_url: str = "https://api.gateway.payments.internal"

    # --- Collections Parameters ---
    fdcpa_contact_hour_start: int = 8   # 8 AM
    fdcpa_contact_hour_end: int = 21    # 9 PM
    max_daily_contact_attempts: int = 3
    max_weekly_contact_attempts: int = 7
    escalation_days_threshold: int = 30
    hardship_min_income_ratio: float = 0.5

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
