"""
Configuration for Payment Fraud Prevention Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "payment_fraud"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    payment_processing_api_url: str = "https://api.payments.internal"
    beneficiary_verification_api_url: str = "https://api.beneficiary.internal"
    sanctions_screening_api_url: str = "https://api.sanctions.internal"
    velocity_check_api_url: str = "https://api.velocity.internal"
    case_management_api_url: str = "https://api.cases.internal"
    core_banking_api_url: str = "https://api.core-banking.internal"

    # --- Payment Fraud Parameters ---
    # Wire transfer thresholds
    wire_threshold_review: float = 25000.0
    wire_threshold_block: float = 100000.0
    wire_threshold_sar: float = 5000.0

    # ACH thresholds
    ach_threshold_review: float = 10000.0
    ach_threshold_block: float = 50000.0

    # Check thresholds
    check_threshold_review: float = 5000.0
    check_threshold_block: float = 25000.0

    # Real-time payment thresholds
    rtp_threshold_review: float = 10000.0
    rtp_threshold_block: float = 25000.0

    # Velocity limits
    velocity_limit_daily_wires: int = 3
    velocity_limit_daily_wire_amount: float = 100000.0
    velocity_limit_daily_ach: int = 10
    velocity_limit_daily_ach_amount: float = 50000.0
    velocity_limit_hourly_payments: int = 5

    # Beneficiary verification
    beneficiary_mismatch_threshold: float = 0.7
    new_beneficiary_alert_days: int = 30

    # Fraud scoring
    fraud_score_threshold_block: int = 85
    fraud_score_threshold_review: int = 60
    fraud_score_threshold_alert: int = 40

    # International payments
    high_risk_countries: list[str] = ["IR", "KP", "SY", "CU", "VE", "MM", "AF", "IQ", "LY", "SO", "SD", "YE", "SS"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
