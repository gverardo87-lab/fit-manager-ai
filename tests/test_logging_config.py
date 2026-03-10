import logging

from api.logging_config import configure_app_logging


def test_configure_app_logging_uses_data_logs_and_is_idempotent(tmp_path):
    log_path = tmp_path / "logs" / "fitmanager.log"
    root_logger = logging.getLogger()

    before_handlers = list(root_logger.handlers)

    try:
        first_path = configure_app_logging(
            tmp_path,
            level_name="INFO",
            max_bytes=4096,
            backup_count=2,
        )
        second_path = configure_app_logging(
            tmp_path,
            level_name="INFO",
            max_bytes=4096,
            backup_count=2,
        )

        assert first_path == log_path
        assert second_path == log_path

        target_handlers = [
            handler
            for handler in root_logger.handlers
            if getattr(handler, "baseFilename", None) == str(log_path)
        ]
        assert len(target_handlers) == 1

        logging.getLogger("fitmanager.test").info("Logging bootstrap test")
        target_handlers[0].flush()

        assert log_path.exists()
        assert "Logging bootstrap test" in log_path.read_text(encoding="utf-8")
    finally:
        for handler in list(root_logger.handlers):
            if handler in before_handlers:
                continue
            root_logger.removeHandler(handler)
            handler.close()
