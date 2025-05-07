"""Модуль логирования."""

import logging
from pathlib import Path


def setup_logging():
    """Настройка глобального логирования."""
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(str(log_file), encoding='utf-8')
        ])

    # Отключаем логирование для pygls.protocol.json_rpc
    pygls_logger = logging.getLogger("pygls.protocol.json_rpc")
    pygls_logger.setLevel(logging.ERROR)
