"""Маршруты FastAPI."""

import logging
import aiosqlite
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from alert_price.api.depends import get_price_cache
from alert_price.api.schemas import TrackingParameters, DeleteResponse
from alert_price.services.database_gateway import DatabaseGateway
from alert_price.services.price_cache import PriceCache

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="alert_price/templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Возвращает HTML-страницу для ввода данных.
    """
    return templates.TemplateResponse(name="index.html",
                                      context={"request": request})


@router.get("/api/prices", response_model=None)
async def get_prices(price_cache: PriceCache = Depends(get_price_cache)):
    """
    Возвращает кешированные цены акций с MOEX.
    response_model=None отключает автоматическую валидацию ответа
    """
    try:
        prices = await price_cache.get_prices()
        last_update = await price_cache.get_last_update_time()
        return {
            "prices": prices,
            "last_updated": last_update.isoformat() if last_update else None
        }
    except Exception as e:
        raise HTTPException(503, detail=str(e)) from e


@router.post("/api/stock-alerts")
async def create_stock_alert(
    ticker: str = Form(...),
    buy_price: str = Form(...),
    sell_price: str = Form(...)
):
    """
    Добавляет запись в бд.

    Args:
        ticker: тикер акции.
        buy_price: цена покупки.
        sell_price: цена продажи.
    """
    parameters = TrackingParameters(
        ticker=ticker,
        buy_price=buy_price,
        sell_price=sell_price
    )
    print(parameters)

    async with DatabaseGateway() as gateway:
        results = await gateway.save_share(parameters)
    if not results:
        return {"success": False, "error": "Нет данных для записи."}

    return {"success": True}


@router.delete("/api/stock-alerts/{ticker}")
async def delete_stock_alert(ticker: str) -> DeleteResponse:
    """
    Удаляет акцию из системы отслеживания по её тикеру.

    Args:
        ticker: Тикер акции для удаления (например: AAPL, GOOGL).
    """
    try:
        async with DatabaseGateway() as gateway:
            success = await gateway.delete_share(ticker)

            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Акция с тикером {ticker} не найдена"
                )

            return DeleteResponse(
                success=True,
                message=f"Акция {ticker} успешно удалена"
            )

    except aiosqlite.Error as e:
        logger.error("Database error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при удалении акции"
        ) from e


@router.get("/api/tracked-stocks")
async def get_tracked_stocks():
    """Возвращает отслеживаемые акции из базы данных."""
    async with DatabaseGateway() as gateway:
        stocks = await gateway.get_all_tracked_stocks()
    return [{
        "ticker": stock.ticker,
        "buy_price": stock.buy_price,
        "sell_price": stock.sell_price
    } for stock in stocks]
