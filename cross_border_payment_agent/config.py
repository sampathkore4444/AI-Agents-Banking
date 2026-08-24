"""
Configuration for Cross-Border Payment Assistant Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "xborder"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    fx_rate_api_url: str = "https://api.fxrates.internal"
    swift_gpi_api_url: str = "https://api.swiftgpi.internal"
    correspondent_bank_api_url: str = "https://api.correspondent.internal"
    sanctions_api_url: str = "https://api.sanctions.internal"
    notification_api_url: str = "https://api.notifications.internal"

    # --- Cross-Border Parameters ---
    default_markdown_pct: float = 0.02
    max_wire_amount_usd: float = 1000000.00
    swiss_ffa_threshold: float = 100000.00
    ofac_screening_required: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
