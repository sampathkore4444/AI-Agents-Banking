"""
Configuration for Anti-Money Laundering (AML) Alert Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "aml"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    transaction_monitoring_api_url: str = "https://api.transaction-monitoring.internal"
    sanctions_screening_api_url: str = "https://api.sanctions-screening.internal"
    pep_database_api_url: str = "https://api.pep-database.internal"
    regulatory_reporting_api_url: str = "https://api.regulatory-reporting.internal"
    sar_filing_api_url: str = "https://api.sar-filing.internal"
    ctr_filing_api_url: str = "https://api.ctr-filing.internal"
    beneficial_ownership_api_url: str = "https://api.beneficial-ownership.internal"
    case_management_api_url: str = "https://api.case-management.internal"

    # --- AML Parameters ---
    sar_threshold_amount: float = 5000.0
    ctr_threshold_amount: float = 10000.0
    ctr_aggregation_days: int = 15
    suspicious_pattern_window_days: int = 90
    pep_risk_threshold: float = 0.7
    structuring_threshold_amount: float = 10000.0
    structuring_max_transactions: int = 3
    structuring_window_hours: int = 24
    high_risk_country_risk_score: float = 0.8

    # --- Filing Deadlines ---
    sar_filing_deadline_days: int = 30
    ctr_filing_deadline_days: int = 15
    ctr_aggregation_deadline_days: int = 15

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
