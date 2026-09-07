"""
Configuration for Sathapana Bank KYC Onboarding Agent.
Loads settings from environment variables / .env.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Institution ---
    bank_name: str = "Sathapana Bank PLC"
    regulator: str = "National Bank of Cambodia (NBC)"
    camfiu: str = "Cambodia Financial Intelligence Unit (CAMFIU)"

    # --- Runtime environment ---
    kyc_env: str = "development"  # development | staging | production

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
    vector_backend: str = "numpy"  # numpy (reference) | chromadb (needs package)
    reranker_enabled: bool = False
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rag_top_k: int = 5

    # --- Database ---
    db_path: str = "./data/sathapana_kyc.db"

    # --- Provider adapters (point-of-wiring to real vendors) ---
    # Each is "stub" (deterministic, offline) or "http" (live API).
    sanctions_provider: str = "stub"
    identity_provider: str = "stub"
    ocr_provider: str = "stub"
    notification_provider: str = "stub"
    bakong_provider: str = "stub"
    camfiu_provider: str = "stub"

    # Vendor endpoints / credentials (via .env, never committed)
    nbc_bakong_api_url: str = "https://bakong-api.nbc.gov.kh"
    sanctions_api_url: str = ""
    sanctions_api_token: str = ""
    identity_api_url: str = ""
    identity_api_token: str = ""
    ocr_api_url: str = ""
    ocr_api_token: str = ""
    notification_api_url: str = ""
    notification_api_token: str = ""
    camfiu_api_url: str = ""
    camfiu_api_token: str = ""
    camfiu_reporting_url: str = "https://report.camfiu.gov.kh"

    # Vendor call behaviour
    vendor_timeout_seconds: float = 10.0
    vendor_max_retries: int = 2

    # --- Crypto / secrets (bootstrap via security.crypto; keys from .env) ---
    kyc_encryption_key: str = ""
    tokenization_key: str = ""
    hash_chain_salt: str = ""

    # --- MCP server ---
    mcp_transport: str = "stdio"  # stdio | tcp
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000
    mcp_tls_cert: str = ""      # path to PEM cert (TCP transport only)
    mcp_tls_key: str = ""       # path to PEM key  (TCP transport only)
    mcp_auth_token: str = ""    # if set, every request must carry it
    mcp_rate_limit_rpm: int = 600
    mcp_max_payload_bytes: int = 262144  # 256 KiB

    # --- Approval / HITL workflow ---
    approval_sla_seconds: int = 300
    default_officer_id: str = "MLRO-001"

    # --- Cambodia-specific KYC rules ---
    ubo_default_threshold_pct: int = 25       # FATF-aligned baseline
    ubo_high_risk_threshold_pct: int = 10     # risk-based lower threshold (EDD)
    domestic_pep_requires_edd: bool = True
    duplicate_check_match_threshold: float = 0.85
    record_retention_years: int = 5

    # --- Risk thresholds ---
    auto_approve_max_risk_score: float = 0.30
    manual_review_min_risk_score: float = 0.30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()