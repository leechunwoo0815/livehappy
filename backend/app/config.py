from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "LiveHappy"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = "postgresql+asyncpg://stayhub:stayhub123@localhost:5432/stayhub"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"

    elasticsearch_hosts: list[str] = ["http://localhost:9200"]
    elasticsearch_enabled: bool = False

    jwt_secret_key: str = "stayhub-dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    deepseek_api_key: str = ""
    deepseek_api_url: str = "https://api.deepseek.com/v1"
    ai_enabled: bool = False

    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
