"""
Configuration for Financial Statement Analysis Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "financial_statement"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    financial_data_api_url: str = "https://api.financial-data.internal"
    industry_benchmark_api_url: str = "https://api.benchmarks.internal"
    market_data_api_url: str = "https://api.market-data.internal"
    sec_edgar_api_url: str = "https://efts.sec.gov/LATEST"
    notification_api_url: str = "https://api.notifications.internal"

    # --- Analysis Parameters ---
    # Ratio thresholds
    current_ratio_healthy: float = 1.5
    current_ratio_warning: float = 1.0
    debt_to_equity_warning: float = 2.0
    debt_to_equity_critical: float = 3.0
    interest_coverage_warning: float = 2.0
    interest_coverage_critical: float = 1.0
    altman_zscore_distress: float = 1.8
    altman_zscore_gray: float = 3.0

    # Data quality
    min_periods_for_trend: int = 2
    max_years_lookback: int = 5
    statement_completeness_threshold: float = 0.8

    # Industry codes (NAICS)
    supported_industries: list[str] = [
        "11", "21", "22", "23", "31-33", "42", "44-45", "48-49",
        "51", "52", "53", "54", "55", "56", "61", "62", "71", "72", "81",
    ]

    # Output
    max_peers_comparison: int = 10
    trend_periods_default: int = 4
    benchmark_percentile_threshold: float = 0.75

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
