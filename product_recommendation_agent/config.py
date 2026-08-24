"""
Configuration for Product Recommendation Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "product_rec"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    product_catalog_api_url: str = "https://api.productcatalog.internal"
    customer_360_api_url: str = "https://api.customer360.internal"
    crm_api_url: str = "https://api.crm.internal"
    notification_api_url: str = "https://api.notifications.internal"
    offer_management_api_url: str = "https://api.offers.internal"
    campaign_api_url: str = "https://api.campaigns.internal"

    # --- Recommendation Parameters ---
    min_relevance_score: float = 0.6
    max_recommendations: int = 10
    cross_sell_threshold: float = 0.7
    upsell_threshold: float = 0.65
    min_customer_lifetime_value: float = 1000.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
