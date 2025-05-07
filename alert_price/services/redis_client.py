"""Содержит функцию инициализации Redis."""

import logging
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


async def init_redis(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
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
        logger.info("Успешное подключение к Redis")
        return redis
    except Exception as e:
        logger.error("Ошибка подключения к Redis: %s", e)
        raise RuntimeError("Не удалось подключиться к Redis") from e
