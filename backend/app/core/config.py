from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration de l'application."""

    # Application
    app_name: str = "Transport Quote API"
    debug: bool = False

    # Database
    database_url: str = Field(..., env="DATABASE_URL")

    # Redis
    redis_host: str = Field("localhost", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    allowed_origins: str = Field("*", env="ALLOWED_ORIGINS")

    # File Upload
    upload_dir: str = Field("./uploads", env="UPLOAD_DIR")
    max_upload_size: int = 50 * 1024 * 1024  # 50 MB

    # Partner Configs
    partner_configs_dir: str = Field("./configs/partners", env="PARTNER_CONFIGS_DIR")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


@lru_cache()
def get_settings() -> Settings:
    return Settings()
