"""
Configuration for Sathapana Bank KYC Onboarding Agent.
Loads settings from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Institution ---
    bank_name: str = "Sathapana Bank PLC"
    regulator: str = "National Bank of Cambodia (NBC)"
    camfiu: str = "Cambodia Financial Intelligence Unit (CAMFIU)"

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # --- Vector store / embeddings ---
    data_dir: str = "./data"
    # Default model is cached locally (offline-safe). Switch to
    # paraphrase-multilingual-MiniLM-L12-v2 when Khmer embeddings are needed.
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_collection_prefix: str = "sathapana_kyc"

    # --- Database ---
    db_path: str = "./data/sathapana_kyc.db"

    # --- External API stubs (production points at live endpoints) ---
    nbc_bakong_api_url: str = "https://bakong-api.nbc.gov.kh"
    camfiu_reporting_url: str = "https://report.camfiu.gov.kh"
    sanctions_agency_url: str = "https://sanctions.nbc.gov.kh"

    # --- Cambodia-specific KYC rules ---
    ubo_default_threshold_pct: int = 25       # FATF-aligned baseline
    ubo_high_risk_threshold_pct: int = 10     # risk-based lower threshold (EDD)
    domestic_pep_requires_edd: bool = True
    duplicate_check_match_threshold: float = 0.85
    record_retention_years: int = 5

    # --- Risk thresholds ---
    auto_approve_max_risk_score: float = 0.30
    manual_review_min_risk_score: float = 0.30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()