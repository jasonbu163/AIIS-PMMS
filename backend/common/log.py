from pathlib import Path

from loguru import logger

from settings import get_settings, get_site_runtime_root


_configured_processes: set[str] = set()


def setup_logger(process_name: str = "api") -> None:
    if process_name in _configured_processes:
        return

    settings = get_settings()
    log_dir = Path(settings.log_dir)
    if not log_dir.is_absolute():
        log_dir = get_site_runtime_root() / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_dir / f"{process_name}.log",
        level="INFO",
        rotation="10 MB",
        retention="14 days",
        enqueue=True,
    )
    logger.add(
        log_dir / f"{process_name}-error.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        enqueue=True,
    )
    _configured_processes.add(process_name)
