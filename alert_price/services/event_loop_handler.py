"""Модуль содержит функцию, вызывающую событийный цикл."""

import logging
import asyncio

from alert_price.services.price_cache import PriceCache
from alert_price.services.prices_request import PriceRequest
logger = logging.getLogger(__name__)


# Обработчик принудительной остановки приложения остановки приложения.
stop_event = asyncio.Event()


async def handles_event_loop(price_cache: PriceCache):
    """Вызывает событийный цикл."""

    try:
        while not stop_event.is_set():
            async with PriceRequest() as pr:
                await pr.request_securities()
                prices = await pr.generates_quotes_dictionary()

                if prices:
                    success = await price_cache.save_prices(prices)
                    if success:
                        logger.info("Цены в кэше Redis обновлены.")
                    else:
                        logger.warning("Не удалось сохранить цены в кеш.")
                else:
                    logger.error("MOEX вернул пустой список цен.")
            await asyncio.sleep(30)
    except asyncio.CancelledError:
        logger.info("Параллельная задача была остановлена.")
