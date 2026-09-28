from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "CyberRAG"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # ── GapGPT ─────────────────────────────────────────────────────────────
    gapgpt_base_url: str = "https://api.gapgpt.app/v1"
    gapgpt_api_key: str = ""
    gapgpt_model: str = "gpt-4o"
    gapgpt_timeout: float = 15.0

    # ── OpenRouter ─────────────────────────────────────────────────────────
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"
    openrouter_timeout: float = 15.0

    # ── Hugging Face ───────────────────────────────────────────────────────
    hf_base_url: str = "https://router.huggingface.co/v1"
    hf_api_key: str = ""
    hf_model: str = "Qwen/Qwen3-14B"
    hf_timeout: float = 30.0

    # ── RAG ────────────────────────────────────────────────────────────────
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    top_k: int = 5
    candidate_k: int = 15
    similarity_threshold: float = 0.35

    admin_token: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )


settings = Settings()

RAW_DIR = BASE_DIR / "data" / "raw"
INDEX_DIR = BASE_DIR / "data" / "index"