"""
Bootstrap del logging locale dell'applicazione.

Obiettivo:
- scrivere log applicativi in data/logs/
- evitare duplicazione handler su reload/import multipli
- lasciare intatti gli handler console configurati da uvicorn
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

DEFAULT_LOG_FILENAME = "fitmanager.log"
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_log_dir(data_dir: Path) -> Path:
    return data_dir / "logs"


def get_log_path(data_dir: Path) -> Path:
    return get_log_dir(data_dir) / DEFAULT_LOG_FILENAME


def _resolve_level(level_name: str) -> int:
    return getattr(logging, level_name.upper(), logging.INFO)


def _has_file_handler(logger: logging.Logger, log_path: Path) -> bool:
    target = str(log_path.resolve())
    for handler in logger.handlers:
        base_filename = getattr(handler, "baseFilename", None)
        if not base_filename:
            continue
        try:
            if str(Path(base_filename).resolve()) == target:
                return True
        except OSError:
            continue
    return False


def _attach_rotating_file_handler(
    logger: logging.Logger,
    log_path: Path,
    level: int,
    max_bytes: int,
    backup_count: int,
) -> None:
    if _has_file_handler(logger, log_path):
        return

    handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=True,
    )
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            fmt=DEFAULT_LOG_FORMAT,
            datefmt=DEFAULT_LOG_DATE_FORMAT,
        )
    )
    logger.addHandler(handler)


def _set_minimum_level(logger: logging.Logger, level: int) -> None:
    if logger.level == logging.NOTSET or logger.level > level:
        logger.setLevel(level)


def configure_app_logging(
    data_dir: Path,
    level_name: str = "INFO",
    max_bytes: int = 1_000_000,
    backup_count: int = 5,
) -> Path:
    """
    Configura il logging locale dell'app.

    Strategia:
    - aggiunge un RotatingFileHandler al root logger
    - se `uvicorn.error` non propaga al root, gli aggiunge lo stesso file handler
    - non tocca gli handler console gia presenti
    """
    log_dir = get_log_dir(data_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = get_log_path(data_dir)
    level = _resolve_level(level_name)

    root_logger = logging.getLogger()
    _set_minimum_level(root_logger, level)
    _attach_rotating_file_handler(
        root_logger,
        log_path=log_path,
        level=level,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )

    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    _set_minimum_level(uvicorn_error_logger, level)
    if not uvicorn_error_logger.propagate:
        _attach_rotating_file_handler(
            uvicorn_error_logger,
            log_path=log_path,
            level=level,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )

    return log_path
