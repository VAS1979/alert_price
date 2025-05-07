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
                 "TQBR/securities.json?iss.meta=off")

    # Шаблон для проверки изменений типов и наименований столбцов таблицы акций
    SHARES_COLUMN_TEMPLATE = [
        'SECID', 'BOARDID', 'SHORTNAME', 'PREVPRICE', 'LOTSIZE', 'FACEVALUE',
        'STATUS', 'BOARDNAME', 'DECIMALS', 'SECNAME', 'REMARKS', 'MARKETCODE',
        'INSTRID', 'SECTORID', 'MINSTEP', 'PREVWAPRICE', 'FACEUNIT',
        'PREVDATE', 'ISSUESIZE', 'ISIN', 'LATNAME', 'REGNUMBER',
        'PREVLEGALCLOSEPRICE', 'CURRENCYID', 'SECTYPE', 'LISTLEVEL',
        'SETTLEDATE']

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

        if not isinstance(sber_price, (float)) or sber_price is None:
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

        # Проверка на отсутствие изменений в списке параметров акций
        securities_columns = content['securities']['columns']
        if securities_columns != self.SHARES_COLUMN_TEMPLATE:
            logger.error("Обнаружены изменения в списке параметров акций.")
            raise ValueError("Изменения в списке параметров акций.")

        logger.info("Котировки всех акций MOEX успешно получены.")
        self.content = content

    async def generates_quotes_dictionary(self):
        """
        Формирует словарь котировок.

        Returns:
            quotes_dict: Словарь(тикер: цена).
        """

        share_list = self.content['securities']['data']
        quotes_dict = {}

        for share in share_list:
            quotes_dict.update({share[0]: share[3]})

        return quotes_dict
