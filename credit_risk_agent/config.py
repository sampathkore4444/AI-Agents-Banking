"""
Configuration for Credit Risk Monitoring Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "risk"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    credit_monitoring_api_url: str = "https://api.creditmonitor.internal"
    financial_statement_api_url: str = "https://api.financials.internal"
    market_data_api_url: str = "https://api.marketdata.internal"
    rating_agency_api_url: str = "https://api.ratings.internal"
    portfolio_api_url: str = "https://api.portfolio.internal"
    alert_api_url: str = "https://api.alerts.internal"

    # --- Risk Thresholds ---
    watchlist_deterioration_threshold: float = 0.15  # 15% decline triggers alert
    critical_alert_threshold: float = 0.25  # 25% decline = critical
    portfolio_concentration_limit: float = 0.10  # 10% max single-name exposure
    regulatory_capital_ratio_min: float = 0.08  # 8% Basel III minimum

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
