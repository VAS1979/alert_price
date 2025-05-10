"""Модуль с фикстурами тестов."""
import pytest
from aioresponses import aioresponses
import pytest_asyncio

from alert_price.services.prices_request import PriceRequest

# Шаблон для проверки изменений типов и наименований столбцов таблицы акций
SHARES_COLUMN_TEMPLATE = [
        'SECID', 'BOARDID', 'SHORTNAME', 'PREVPRICE', 'LOTSIZE', 'FACEVALUE',
        'STATUS', 'BOARDNAME', 'DECIMALS', 'SECNAME', 'REMARKS', 'MARKETCODE',
        'INSTRID', 'SECTORID', 'MINSTEP', 'PREVWAPRICE', 'FACEUNIT',
        'PREVDATE', 'ISSUESIZE', 'ISIN', 'LATNAME', 'REGNUMBER',
        'PREVLEGALCLOSEPRICE', 'CURRENCYID', 'SECTYPE', 'LISTLEVEL',
        'SETTLEDATE']


@pytest.fixture
def mock_aioresponse():
    """Фикстура для мокирования HTTP-запросов через aioresponses.

    Returns:
        aioresponses: Мок-объект для перехвата HTTP-запросов
    """
    with aioresponses() as m:
        yield m


@pytest.fixture
def sber_response_data():
    """Фикстура с тестовыми данными для акции Сбербанка.

    Returns:
        dict: Мок-данные с котировкой SBER в формате MOEX API
    """
    return {"marketdata": {"data": [["SBER", 250.50]]}}


@pytest.fixture
def securities_response_data():
    """Фикстура с тестовыми данными для списка ценных бумаг.

    Returns:
        dict: Мок-данные с перечнем акций в формате MOEX API
    """
    return {
        "securities": {
            "columns": SHARES_COLUMN_TEMPLATE,
            "data": [
                ["SBER", "TQBR", "Сбербанк", 250.50, 10, 1],
                ["GAZP", "TQBR", "Газпром", 180.75, 10, 1]
            ]
        }
    }

# TODO:
# Установи в pyproject.toml переменеые настройки pytest 
# asyncio_mode и asyncio_default_fixture_loop_scope
# и асинхронные тесты и фикстуры не нужно будет маркировать
# подобными марками
@pytest_asyncio.fixture(scope="function")
async def price_request():
    """Асинхронная фикстура, предоставляющая экземпляр PriceRequest.

    Returns:
        PriceRequest: Инициализированный экземпляр клиента

    Note:
        Автоматически управляет созданием и закрытием сессии
    """
    pr = PriceRequest()
    # TODO:
    # Зачем вызываешь эти методы?
    # он для того и контестменеджер, чтоб делать
    # это одной строкой.
    # async with PriceRequest() as pr:
    #     yield pr
    
    #TODO:
    # оборачивать в try-except тут не надо
    # Если в процессе теста вылетит исключение,которого
    # ты не жлешь то эту ошибку ты устанешь искать
    # тк try закроется вызовом aexit без передачи 
    # выхлопа ошибки. todoшка выше гарантирует,
    # что любое исключение внутри контеста выведет
    # полный трейс ексепшена
    await pr.__aenter__()
    try:
        yield pr
    finally:
        await pr.__aexit__(None, None, None)
