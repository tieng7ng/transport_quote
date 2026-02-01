from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration de l'application."""

    # Application
    app_name: str = "Transport Quote API"
    debug: bool = False

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/transport_quote"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # File Upload
    upload_dir: str = "./uploads"
    max_upload_size: int = 50 * 1024 * 1024  # 50 MB

    # Partner Configs
    partner_configs_dir: str = "./configs/partners"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
