"""
Configuration for Payment Reconciliation Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "recon"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    payment_gateway_api_url: str = "https://api.payments.internal"
    ledger_api_url: str = "https://api.ledger.internal"
    bank_statement_api_url: str = "https://api.bankstatements.internal"
    accounting_system_api_url: str = "https://api.accounting.internal"
    notification_api_url: str = "https://api.notifications.internal"

    # --- Reconciliation Parameters ---
    auto_match_threshold: float = 0.95
    fuzzy_match_threshold: float = 0.75
    amount_tolerance_pct: float = 0.01
    max_discrepancy_amount: float = 10000.00
    reconciliation_period_days: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
