import logging
from pathlib import Path
from typing import Any, Dict

from app.core.settings import get_settings

settings = get_settings()


def setup_logging() -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.LOG_LEVEL)

    # Try to create logs directory and test write permissions
    logs_dir = Path("logs")
    file_logging_available = True
    try:
        logs_dir.mkdir(exist_ok=True)
        # Test if we can write to the logs directory
        test_file = logs_dir / "test_write.tmp"
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError):
        file_logging_available = False
        print("Warning: Cannot write to logs directory. File logging disabled.")

    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "rich.logging.RichHandler",
                "formatter": "default",
            },
            "file": {
                "level": log_level,
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": logs_dir / "isms.log",
                "maxBytes": 10485760,  # 10 MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "app": {
                "handlers": (
                    ["console"]
                    if settings.ENV_MODE == "development" or not file_logging_available
                    else ["console", "file"]
                ),
                "level": log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": (
                    ["console"]
                    if settings.ENV_MODE == "development" or not file_logging_available
                    else ["console", "file"]
                ),
                "level": log_level,
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": (
                    ["console"]
                    if settings.ENV_MODE == "development" or not file_logging_available
                    else ["console", "file"]
                ),
                "level": logging.WARNING,
                "propagate": False,
            },
        },
        "root": {
            "handlers": (
                ["console"]
                if settings.ENV_MODE == "development" or not file_logging_available
                else ["console", "file"]
            ),
            "level": log_level,
        },
    }

    # Apply configuration
    from logging.config import dictConfig

    try:
        dictConfig(logging_config)
    except Exception as e:
        # Fallback to basic console logging if configuration fails
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()],
        )
        print(
            f"Warning: Failed to configure logging: {e}. Using basic console logging."
        )

    # Log startup message
    logger = logging.getLogger("app")
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} in {settings.ENV_MODE} mode"
    )
