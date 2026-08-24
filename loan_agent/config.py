"""
Configuration for Loan Application Processing Agent MCP Server.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "loan"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- External API Stubs ---
    credit_bureau_api_url: str = "https://api.creditbureau.com"
    credit_bureau_api_key: str = ""
    income_verification_api_url: str = "https://api.incomeverify.com"
    document_verification_api_url: str = "https://api.docverify.com"
    application_management_api_url: str = "https://api.loanmanagement.internal"
    notification_api_url: str = "https://api.notifications.internal"
    payment_gateway_api_url: str = "https://api.payments.internal"

    # --- Loan Parameters ---
    min_credit_score: int = 580
    max_dti_ratio: float = 0.43
    max_ltv_ratio: float = 0.95

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
