from functools import lru_cache
from pathlib import Path
import sys

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_site_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_packaged_resource_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parent


def get_project_root() -> Path:
    if getattr(sys, "frozen", False):
        return get_packaged_resource_root()
    return get_site_runtime_root().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_site_runtime_root() / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "AIIS-PMMS Backend"
    api_prefix: str = "/api/v1"
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    database_url: str = ""
    db_dialect: str = "mssql"
    db_host: str = "127.0.0.1"
    db_port: int = 1433
    db_name: str = "AIIS_PMMS"
    db_user: str = "sa"
    db_password: str = ""
    db_driver: str = "ODBC Driver 17 for SQL Server"
    db_trust_server_certificate: bool = True
    sqlite_database: str = "./pmms-dev.db"
    storage_dir: str = "storage"

    jwt_secret_key: str = Field(default="change-me")
    jwt_access_token_minutes: int = 60
    jwt_refresh_token_days: int = 7

    bootstrap_root_username: str = "root"
    bootstrap_root_password: str = "#789@root"

    enable_maintenance_api: bool = False
    maintenance_token: str = ""

    @property
    def async_database_url(self) -> str:
        from database.url_builder import build_async_database_url

        return build_async_database_url()


@lru_cache
def get_settings() -> Settings:
    return Settings()
