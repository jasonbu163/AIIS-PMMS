from __future__ import annotations

from common.log import logger, setup_logger
from settings import get_settings


def test_setup_logger_writes_process_logs_to_configured_local_dir(
    tmp_path,
    monkeypatch,
) -> None:
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    get_settings.cache_clear()

    setup_logger(process_name="test-api")
    logger.info("local log smoke")
    logger.error("local error smoke")
    logger.complete()

    assert (log_dir / "test-api.log").exists()
    assert (log_dir / "test-api-error.log").exists()


async def test_api_request_is_logged(client) -> None:
    records: list[str] = []
    sink_id = logger.add(lambda message: records.append(str(message)), format="{message}")

    try:
        response = await client.get("/health")
    finally:
        logger.remove(sink_id)

    assert response.status_code == 200
    assert any(
        "api_request" in record
        and "method=GET" in record
        and "path=/health" in record
        and "status=200" in record
        for record in records
    )
