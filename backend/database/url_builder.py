from urllib.parse import quote_plus


def build_async_database_url() -> str:
    from settings import get_settings

    settings = get_settings()
    if settings.database_url:
        return settings.database_url
    if settings.db_dialect == "sqlite":
        if settings.sqlite_database == ":memory:":
            return "sqlite+aiosqlite:///:memory:"
        return f"sqlite+aiosqlite:///{settings.sqlite_database}"
    driver = quote_plus(settings.db_driver)
    password = quote_plus(settings.db_password)
    trust_server_certificate = "yes" if settings.db_trust_server_certificate else "no"
    return (
        f"mssql+aioodbc://{settings.db_user}:{password}@"
        f"{settings.db_host}:{settings.db_port}/{settings.db_name}"
        f"?driver={driver}&TrustServerCertificate={trust_server_certificate}"
    )


def build_sync_database_url() -> str:
    from settings import get_settings

    settings = get_settings()
    if settings.database_url:
        return settings.database_url.replace("+aioodbc", "+pyodbc")
    if settings.db_dialect == "sqlite":
        if settings.sqlite_database == ":memory:":
            return "sqlite:///:memory:"
        return f"sqlite:///{settings.sqlite_database}"
    driver = quote_plus(settings.db_driver)
    password = quote_plus(settings.db_password)
    trust_server_certificate = "yes" if settings.db_trust_server_certificate else "no"
    return (
        f"mssql+pyodbc://{settings.db_user}:{password}@"
        f"{settings.db_host}:{settings.db_port}/{settings.db_name}"
        f"?driver={driver}&TrustServerCertificate={trust_server_certificate}"
    )
