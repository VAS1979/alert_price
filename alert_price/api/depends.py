"""Модуль для управления зависимостями (Dependency Injection) приложения.

Содержит функции-провайдеры для создания и внедрения зависимостей,
связанных с кешированием цен и работой с Redis.

Основные зависимости:
- get_price_cache: Создает и возвращает экземпляр кеша цен
"""

from alert_price.services.redis_client import init_redis
from alert_price.services.price_cache import PriceCache


async def get_price_cache() -> PriceCache:
    """Создает и возвращает экземпляр кеша цен.

    Инициализирует подключение к Redis и создает на его основе
    экземпляр PriceCache для работы с кешем биржевых цен.

    Returns:
        PriceCache: Экземпляр кеша цен, связанный с Redis

    Example:
        >>> cache = await get_price_cache()
        >>> prices = await cache.get_prices()

    Note:
        Автоматически управляет подключением к Redis. Не требует
        ручного закрытия соединения при использовании через FastAPI Depends.
    """
    redis = await init_redis()
    return PriceCache(redis)
