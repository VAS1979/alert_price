"""
Содержит класс кеширования биржевых цен в Redis.

Обеспечивает:
- Сохранение текущих цен акций
- Автоматическое обновление по расписанию
- Валидацию данных перед кешированием
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
import logging
from redis.asyncio import Redis
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class PriceCache:
    """Кеш биржевых цен с MOEX."""

    def __init__(self, redis_client: Redis):
        """
        Args:
            redis_client: Асинхронный клиент Redis.
        """
        self.redis = redis_client
        self.cache_key = "moex:latest_prices"  # Ключ для хранения цен
        self.cache_ttl = 30  # Время актуальности цен в секундах

    async def save_prices(self, prices: Dict[str, float]) -> bool:
        """
        Сохраняет цены акций в кеш.

        Args:
            prices: Словарь {тикер: цена}

        Returns:
            bool: Успешно ли сохранено

        Raises:
            ValueError: Если передан пустой словарь цен
        """
        if not prices:
            raise ValueError("Нельзя сохранить пустые цены")

        try:
            # Атомарная запись + установка TTL
            async with self.redis.pipeline() as pipe:
                await pipe.hset(self.cache_key, mapping=prices)
                await pipe.expire(self.cache_key, self.cache_ttl)
                await pipe.execute()

            logger.debug("Сохранены цены для %s акций", len(prices))
            return True

        except Exception as e:
            logger.error("Ошибка сохранения цен: %s", e)
            return False

    async def get_prices(self) -> Dict[str, float]:
        """
        Получает текущие цены из кеша.

        Returns:
            Словарь {тикер: цена}.

        Raises:
            HTTPException: Если данные недоступны.
        """
        try:
            prices = await self.redis.hgetall(self.cache_key)
            if not prices:
                raise HTTPException(
                    status_code=503,
                    detail="Цены временно недоступны"
                )

            return {
                ticker.decode(): float(price.decode())
                for ticker, price in prices.items()
            }

        except Exception as e:
            logger.error("Ошибка при получении цены.")
            raise HTTPException(status_code=503,
                  detail="Ошибка доступа к данным.") from e

    async def get_last_update_time(self) -> Optional[datetime]:
        """Возвращает время последнего обновления цен."""
        ttl = await self.redis.ttl(self.cache_key)
        if ttl > 0:
            return datetime.now() - timedelta(seconds=self.cache_ttl - ttl)
        return None
