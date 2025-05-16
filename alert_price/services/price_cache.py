"""
Модуль для кеширования биржевых цен с постоянным хранением данных.

Основные особенности:
- Сохраняет старые значения ключей, если они не были обновлены
- Не удаляет данные автоматически по таймауту
- Гарантирует доступность последних полученных цен
"""

from typing import Dict, Optional
from datetime import datetime
import logging
from redis.asyncio import Redis
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class PriceCache:
    """Кеш биржевых цен с персистентным хранением данных.

    Особенности работы:
    - При обновлении изменяются только переданные значения
    - Непереданные ключи сохраняют свои значения
    - Данные не имеют срока годности (хранятся до явного удаления)
    """

    def __init__(self, redis_client: Redis):
        """Инициализация кеша.

        Args:
            redis_client: Асинхронный клиент Redis для хранения данных
        """
        self.redis = redis_client
        self.cache_key = "moex:latest_prices"  # Ключ для хранения цен

    async def save_prices(self, prices: Dict[str, float]) -> bool:
        """
        Безопасное сохранение цен с использованием Redis Pipeline.

        Сохраняет только переданные значения, остальные данные без изменений.
        Использует атомарную операцию через контекстный менеджер.

        Args:
            prices: Словарь {тикер: цена} для обновления

        Returns:
            bool: True если сохранение успешно, False при ошибке
        """
        if not isinstance(prices, dict):
            logger.error("Ожидается словарь цен")
            return False

        if not prices:
            logger.debug("Пустой словарь цен - обновление не требуется")
            return True

        try:
            async with self.redis.pipeline() as pipe:
                # Атомарная операция с частичным обновлением:
                await pipe.hset(self.cache_key, mapping=prices)
                await pipe.execute()  # Фиксация изменений

            logger.debug("Обновлено %s тикеров", len(prices))
            return True

        except Exception as e:
            logger.error("Ошибка сохранения в Redis: %s", str(e))
            return False

    async def get_prices(self) -> Dict[str, float]:
        """Получает все текущие цены из кеша.

        Returns:
            Dict[str, float]: Словарь всех доступных цен {тикер: цена}

        Raises:
            HTTPException: Если в кеше нет данных (код 503)
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
        """Возвращает время последнего обновления любого тикера.

        Note:
            Возвращает текущее время, так как данные
            всегда считаются актуальными.

        Returns:
            Optional[datetime]: Всегда возвращает текущее время
        """
        exists = await self.redis.exists(self.cache_key)
        return datetime.now() if exists else None

    async def clear_cache(self) -> None:
        """Полностью очищает кеш цен."""
        await self.redis.delete(self.cache_key)
        logger.info("Кеш цен полностью очищен")
