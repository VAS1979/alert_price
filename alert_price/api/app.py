"""Точка входа в приложение."""

from pathlib import Path

import asyncio
import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from alert_price.api.routers import router
from alert_price.services.price_cache import PriceCache
from alert_price.services.redis_client import init_redis
from alert_price.utils.logger import setup_logging
from alert_price.services.event_loop_handler import (
    handles_event_loop,
    stop_event,
)

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """ Запускает фоновые задачи """

    task = None
    try:
        logger.info("Запуск цикла сопрограмм\n")
        redis = await init_redis()
        price_cache = PriceCache(redis)

        task = asyncio.create_task(handles_event_loop(price_cache))
        yield
    finally:
        stop_event.set()
        task.cancel()
        await redis.close()
        await task

app = FastAPI(
    lifespan=lifespan,
    title="Alert Price",
    description="API для оповещения о достижении заданной цены акций.",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request,
                                       exc: RequestValidationError):
    """
    Обработчик ошибок валидации запросов.
    Логирует ошибку и возвращает ответ с деталями ошибки.
    """
    logger.error("Ошибка валидации: %s", exc)
    return JSONResponse(
        status_code=422,
        content={"detail": "Ошибка валидации запроса", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Глобальный обработчик исключений.
    Логирует неожиданные ошибки и возвращает сообщение об ошибке.
    """
    logger.exception("Произошла непредвиденная ошибка: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Произошла непредвиденная ошибка на сервере"},
    )

