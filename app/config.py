from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./dommoda.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # App
    app_title: str = "Dommoda API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Admin auth
    admin_login: str = "admin"
    admin_password: str = "changeme"
    jwt_secret: str = "changeme-set-in-env"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 24


settings = Settings()
