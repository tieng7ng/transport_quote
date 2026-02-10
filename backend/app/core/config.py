from pydantic import Field, field_validator
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
    redis_password: str | None = Field(None, env="REDIS_PASSWORD")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v == "change_this_to_a_secure_random_string_in_production":
            raise ValueError("You must change the default SECRET_KEY in production!")
        return v
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    allowed_email_domains: str = Field("transport-quote.com", env="ALLOWED_EMAIL_DOMAINS")  # Comma separated in env
    allowed_origins: str = Field("*", env="ALLOWED_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        if isinstance(self.allowed_origins, str):
            return [i.strip() for i in self.allowed_origins.split(",") if i.strip()]
        return ["*"]

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
