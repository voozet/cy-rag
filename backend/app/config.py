import json
from pathlib import Path
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "CyberRAG"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_models: List[str] = [
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mistral-small-34b-instruct-2501:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "google/gemma-2-9b-it:free",
    ]
    openrouter_timeout: float = 15.0

    hf_base_url: str = "https://router.huggingface.co/v1"
    hf_api_key: str = ""
    hf_model: str = "Qwen/Qwen3-14B"
    hf_timeout: float = 30.0

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    top_k: int = 5
    candidate_k: int = 15
    similarity_threshold: float = 0.35
    admin_token: str = ""

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    @field_validator("openrouter_models", mode="before")
    @classmethod
    def parse_models(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [m.strip().strip("'\"") for m in v.split(",") if m.strip()]
        return v


settings = Settings()
RAW_DIR = BASE_DIR / "data" / "raw"
INDEX_DIR = BASE_DIR / "data" / "index"