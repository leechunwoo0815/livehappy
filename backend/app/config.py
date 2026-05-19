from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "LiveHappy"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = ""
    redis_url: str = "redis://localhost:6379/0"

    elasticsearch_hosts: list[str] = ["http://localhost:9200"]
    elasticsearch_enabled: bool = False

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    deepseek_api_key: str = ""
    deepseek_api_url: str = "https://api.deepseek.com/v1"
    ai_enabled: bool = False

    sentry_dsn: str = ""

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    cors_origins: str = "http://localhost:3001"
    allowed_origins: str = "http://localhost:3001"

    login_rate_limit: int = 10
    login_rate_window: int = 300

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @model_validator(mode="after")
    def validate_secrets(self):
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY must be set in environment")
        if not self.database_url:
            raise ValueError("DATABASE_URL must be set in environment")
        return self


settings = Settings()
