import json
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./dommoda.db"

    # CORS — kept as str to avoid pydantic_settings auto JSON decode on list[str]
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    def get_cors_origins(self) -> list[str]:
        v = self.cors_origins.strip()
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return [o.strip() for o in v.split(",") if o.strip()]

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
