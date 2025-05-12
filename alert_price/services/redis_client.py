"""Содержит функцию инициализации Redis."""

import logging
import os
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


async def init_redis(
    host: str = None,
    port: int = None,
    db: int = None,
    password: str = None
) -> Redis:
    """
    Инициализирует и возвращает асинхронный клиент Redis.

    Args:
        host: Хост Redis сервера.
        port: Порт Redis сервера.
        db: Номер базы данных.
        password: Пароль (если требуется).

    Returns:
        Redis: Асинхронный клиент Redis

    Raises:
        RuntimeError: Если подключение не удалось.
    """
    host = host or os.environ.get("REDIS_HOST", "localhost")
    port = int(port or os.environ.get("REDIS_PORT", 6379))
    db = int(db or os.environ.get("REDIS_DB", 0))
    password = password or os.environ.get("REDIS_PASSWORD", None)

    try:
        redis = Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=False
        )
        # Проверяем подключение
        await redis.ping()
        logger.info("Успешное подключение к Redis: %s:%s db=%s",
                    host, port, db)
        return redis
    except Exception as e:
        logger.error("Ошибка подключения к Redis: %s", e)
        raise RuntimeError("Не удалось подключиться к Redis") from e
