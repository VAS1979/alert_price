"""Модуль содержит класс, для запроса котировок акции MOEX."""

import logging
import aiohttp

logger = logging.getLogger(__name__)


class PriceRequest:
    """Класс запрашивает котировки акций MOEX."""

    # Адрес запроса по акции SBER (для тестирования работы MOEX)
    SHARE_SBER_URL = ("http://iss.moex.com/iss/engines/stock/markets/shares/"
                      "boards/TQBR/securities/SBER.json?iss.meta=off&iss."
                      "only=marketdata&marketdata.columns=SECID,LAST")

    # Адрес запроса к MOEX по всем акциям
    SHARE_URL = ("http://iss.moex.com/iss/engines/stock/markets/shares/boards/"
                 "TQBR/securities.json?iss.meta=off&iss.only=marketdata"
                 "&marketdata.columns=SECID,LAST")

    def __init__(self):
        self.session = None
        self.content = {}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def request_share_sber(self):
        """
        Запрашивает котировки SBER и возвращает цену,
        тестовый запрос на проверку работы биржи.
        """
        # Проверка подключения и запроса к API
        try:
            async with self.session.get(self.SHARE_SBER_URL, timeout=5) as res:
                res.raise_for_status()  # Проверка HTTP-ошибок (404, 500...)
                content = await res.json(content_type=None)
        except aiohttp.ClientError as e:
            logger.error("Ошибка подключения к MOEX: %s", e)
            raise ValueError("request_share_sber. Не удалось получить "
                             "данные с MOEX.") from e

        # Проверка структуры ответа
        try:
            market_data = content["marketdata"]["data"]
            if not market_data:
                raise ValueError("Нет данных в ответе MOEX.")

            sber_ticker, sber_price = market_data[0][0], market_data[0][1]
        except (KeyError, IndexError, TypeError) as e:
            logger.error("Неверный формат ответа MOEX: %s", e)
            raise ValueError("Некорректные данные от MOEX.") from e

        # Проверка корректности тикера и цены
        if sber_ticker != "SBER":
            logger.error("Получен неверный тикер: %s (ожидался SBER)",
                         sber_ticker)
            raise ValueError("Неверный тикер в ответе MOEX.")

        if not isinstance(sber_price, (float, int)) or sber_price is None:
            logger.error("Некорректная цена: %s", sber_price)
            raise ValueError("MOEX вернул некорректную цену.")

        logger.info("Котировка SBER успешно получена: %s", sber_price)
        return sber_price

    async def request_securities(self):
        """ Формирует запрос к MOEX на получение котировок по всем акциям."""
        # Проверка доступности MOEX
        await self.request_share_sber()

        # Проверка подключения и запроса к API
        try:
            async with self.session.get(self.SHARE_URL, timeout=5) as response:
                response.raise_for_status()
                content = await response.json(content_type=None)
        except aiohttp.ClientError as e:
            logger.error("Ошибка подключения к MOEX: %s", e)
            raise ValueError("Не удалось получить данные с MOEX.") from e

        logger.info("Котировки всех акций MOEX успешно получены.")
        self.content = content

    async def generates_quotes_dictionary(self) -> dict[str, float]:
        """
        Формирует словарь котировок из предварительно валидированных данных.

        Returns:
            Словарь {тикер: цена} с валидными котировками

        Raises:
            RuntimeError: Если не найдено ни одной валидной котировки
        """
        quotes_dict = {}
        error_count = 0
        market_data = self.content["marketdata"]["data"]

        for share in market_data:
            # Проверка структуры записи
            if len(share) < 2:
                error_count += 1
                continue

            ticker, price = share[0], share[1]

            # Проверка тикера
            if not isinstance(ticker, str) or not ticker.strip():
                error_count += 1
                continue

            # Обработка цены
            try:
                float_price = float(price)
            except (TypeError, ValueError):
                error_count += 1
                continue

            # Проверка валидности цены
            if float_price <= 0:
                error_count += 1
                continue

            quotes_dict[ticker] = float_price

        # Логирование результатов
        if error_count:
            logger.warning("Пропущено записей с ошибками: %s", error_count)

        if not quotes_dict:
            logger.error("Не обнаружено ни одной валидной котировки")
            raise RuntimeError("Все полученные котировки содержат ошибки")

        logger.info("Успешно обработано котировок: %s", len(quotes_dict))
        return quotes_dict
