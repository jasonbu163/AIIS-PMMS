from __future__ import annotations

import time

import pyodbc

from settings import get_settings


def _quote_sql_server_identifier(value: str) -> str:
    return f"[{value.replace(']', ']]')}]"


def _build_master_connection_string() -> str:
    settings = get_settings()
    trust = "yes" if settings.db_trust_server_certificate else "no"
    return (
        f"DRIVER={{{settings.db_driver}}};"
        f"SERVER={settings.db_host},{settings.db_port};"
        "DATABASE=master;"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        "Encrypt=yes;"
        f"TrustServerCertificate={trust};"
    )


def ensure_database() -> None:
    settings = get_settings()
    if settings.db_dialect == "sqlite" or settings.database_url:
        return

    connection_string = _build_master_connection_string()
    database_name = _quote_sql_server_identifier(settings.db_name)
    last_error: Exception | None = None

    for _ in range(30):
        try:
            with pyodbc.connect(connection_string, autocommit=True, timeout=5) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    f"IF DB_ID(?) IS NULL CREATE DATABASE {database_name}",
                    settings.db_name,
                )
                return
        except pyodbc.Error as exc:
            last_error = exc
            time.sleep(2)

    raise RuntimeError("database initialization failed") from last_error


if __name__ == "__main__":
    ensure_database()
