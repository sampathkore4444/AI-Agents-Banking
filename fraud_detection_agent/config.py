"""
Configuration for Real-Time Transaction Fraud Detection Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "fraud"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    transaction_api_url: str = "https://api.transactions.internal"
    card_management_api_url: str = "https://api.cardmanagement.internal"
    alert_notification_api_url: str = "https://api.alerts.internal"
    velocity_check_api_url: str = "https://api.velocity.internal"
    device_fingerprint_api_url: str = "https://api.device.internal"
    account_api_url: str = "https://api.accounts.internal"
    case_management_api_url: str = "https://api.cases.internal"

    # --- Fraud Detection Parameters ---
    fraud_score_threshold_block: int = 85
    fraud_score_threshold_review: int = 60
    fraud_score_threshold_alert: int = 40
    velocity_limit_daily_transactions: int = 20
    velocity_limit_daily_amount: float = 50000.0
    velocity_limit_hourly_transactions: int = 5
    max_geo_distance_km: float = 500.0
    anomaly_threshold: float = 0.7

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
