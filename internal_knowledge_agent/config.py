"""
Configuration for Internal Knowledge Base Agent MCP Server.
Loads settings from environment variables.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_prefix: str = "knowledge_base"
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- Document Management API ---
    doc_management_api_url: str = "https://api.docmanagement.internal"
    doc_management_api_key: str = ""

    # --- Ticketing System (ServiceNow) ---
    servicenow_api_url: str = "https://your-instance.service-now.com"
    servicenow_api_user: str = ""
    servicenow_api_password: str = ""

    # --- HR System (Workday) ---
    hr_api_url: str = "https://api.hr.internal"
    hr_api_key: str = ""

    # --- ITSM (IT Service Management) ---
    itsm_api_url: str = "https://api.itsm.internal"
    itsm_api_key: str = ""

    # --- Notification Service ---
    notification_api_url: str = "https://api.notifications.internal"

    # --- Search Configuration ---
    search_min_score: float = 0.5
    max_search_results: int = 10
    context_max_tokens: int = 4000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
