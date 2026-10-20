from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="expense-split-api")
    app_env: Literal["development", "staging", "production"] = Field(default="development")
    app_debug: bool = Field(default=True)
    app_port: int = Field(default=8000)

    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="expense_split")
    jwt_secret: str = Field(default="change-this-development-secret-please")

    hf_category_model: str = Field(default="facebook/bart-large-mnli")
    hf_embeddings_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")

    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
