"""Модуль запуска проекта"""
from logging import getLogger

from uvicorn import run

from alert_price.api.app import app
from alert_price.utils.logger import setup_logging


logger = getLogger(__name__)

def run_server():
    """Выполнить запуск проекта с помощью uvcorn сервера"""
    setup_logging()
    logger.info("Запуск сервера Uvicorn")
    run(app, host="127.0.0.1", port=8088)
