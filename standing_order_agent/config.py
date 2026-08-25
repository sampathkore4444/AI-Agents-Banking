"""
Configuration for Standing Order & Bill Payment Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "standing_order"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    recurring_payment_api_url: str = "https://api.recurring.internal"
    biller_directory_api_url: str = "https://api.billers.internal"
    calendar_api_url: str = "https://api.calendar.internal"
    core_banking_api_url: str = "https://api.core-banking.internal"
    notification_api_url: str = "https://api.notifications.internal"

    # --- Standing Order Parameters ---
    # Frequency limits
    min_frequency_days: int = 1
    max_frequency_days: int = 365
    max_active_standing_orders: int = 50
    max_daily_payment_amount: float = 100000.0
    max_single_payment_amount: float = 50000.0

    # Amount thresholds
    amount_threshold_review: float = 10000.0
    amount_threshold_approval: float = 25000.0
    amount_threshold_block: float = 100000.0

    # Biller limits
    max_biller_search_results: int = 20
    biller_verification_timeout_seconds: int = 30

    # Calendar
    advance_reminder_days: list[int] = [3, 1, 0]
    schedule_change_window_hours: int = 24

    # Retry settings
    max_retry_attempts: int = 3
    retry_interval_hours: int = 24

    # Supported frequencies
    supported_frequencies: list[str] = [
        "once", "daily", "weekly", "biweekly", "monthly",
        "quarterly", "semi-annual", "annual", "custom",
    ]

    # Payment methods
    supported_payment_methods: list[str] = [
        "ach_debit", "ach_credit", "wire", "rtp", "check", "zelle",
    ]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
