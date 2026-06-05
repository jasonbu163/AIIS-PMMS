from common.schema_base import ApiSchema


class DatabaseStatusOut(ApiSchema):
    schema_managed: bool
    current_revision: str | None
    target_revision: str
    upgrade_required: bool
    app_env: str
    database_dialect: str


class DatabaseMaintenanceResultOut(DatabaseStatusOut):
    created: list[str]
    updated: list[str]
    skipped: list[str]
    warnings: list[str]
