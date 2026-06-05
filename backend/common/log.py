from loguru import logger


def setup_logger(process_name: str = "api") -> None:
    logger.add(
        f"logs/{process_name}.log",
        level="INFO",
        rotation="10 MB",
        retention="14 days",
        enqueue=True,
    )
    logger.add(
        f"logs/{process_name}-error.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        enqueue=True,
    )
