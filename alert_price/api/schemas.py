"Содержит модели Pydantic."

from pydantic import BaseModel


class TrackingParameters(BaseModel):
    """
    Модель для входных данных списка отслеживания.

    Атрибуты:
        ticker (str): Тикер акции.
        buy_price (str): Цена покупки акций.
        sell_price (str): Цена продажи акций.
    """
    ticker: str
    buy_price: str
    sell_price: str


class DeleteResponse(BaseModel):
    """Модель ответа на удаление акции"""
    success: bool
    message: str
