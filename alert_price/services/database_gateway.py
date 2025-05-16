"""Модуль для работы с SQLite базой данных."""

import logging
from pathlib import Path
import aiosqlite

from alert_price.api.schemas import TrackingParameters

logger = logging.getLogger(__name__)


class DatabaseGateway:
    """Класс для работы с SQLite базой данных."""

    def __init__(self):
        """Инициализирует параметры подключения к бд."""
        self.conn = None
        self.db_path = self._get_db_path()

    async def __aenter__(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self.conn.execute("PRAGMA foreign_keys = ON")
        return self

    async def __aexit__(self, *args):
        try:
            await self.conn.close()
        except Exception as e:
            logger.error("Ошибка при закрытии соединения: %s", e)
            raise

    @staticmethod
    def _get_db_path() -> Path:
        """Возвращает путь к файлу базы данных."""
        path_dir = Path.cwd() / "database"
        path_dir.mkdir(parents=True, exist_ok=True)
        return path_dir / "alert_price.db"

    @staticmethod
    async def _table_exists(cursor: aiosqlite.Cursor, table_name: str) -> bool:
        """Проверяет существование таблицы в базе данных."""
        try:
            await cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return await cursor.fetchone() is not None
        except aiosqlite.Error as e:
            logger.error("Ошибка проверки существования таблицы: %s", e)
            raise

    @staticmethod
    async def _clear_table(cursor: aiosqlite.Cursor, table_name: str) -> None:
        """Очищает таблицу, если она существует."""
        if await DatabaseGateway._table_exists(cursor, table_name):
            await cursor.execute(f"DELETE FROM {table_name}")
            await cursor.execute(
                    f"DELETE FROM sqlite_sequence WHERE name='{table_name}'"
            )

    async def create_tracking_parameters_table(self) -> None:
        """Создает пустую таблицу tracking_parameters в базе данных.

        Raises:
            sqlite3.Error: При ошибках работы с БД.
        """
        table_name = "tracking_parameters"

        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    buy_price TEXT NOT NULL,
                    sell_price TEXT NOT NULL,
                    UNIQUE(ticker) ON CONFLICT REPLACE
                )
                """)
                await self.conn.commit()
                logger.info("Таблица %s создана (или уже существовала)",
                            table_name)

        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error("Ошибка при создании таблицы %s: %s", table_name, e)
            raise

    async def save_share(self, parameters: TrackingParameters) -> Path:
        """Сохраняет выбранный тикер с ценами в базу данных.

        Args:
            parameters: Параметры отслеживания цены выбранной акции.

        Returns:
            Путь к базе данных.

        Raises:
            ValueError: Если таблица не существует.
            sqlite3.Error: При ошибках работы с БД.
        """
        if not parameters:
            raise ValueError("Данные для сохранения отсутствуют.")

        table_name = "tracking_parameters"

        try:
            async with self.conn.cursor() as cursor:
                await self.conn.execute("BEGIN TRANSACTION")

                await cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    buy_price TEXT NOT NULL,
                    sell_price TEXT NOT NULL,
                    UNIQUE(ticker) ON CONFLICT REPLACE
                )
                """)

                await cursor.execute(
                    f"""INSERT INTO {table_name}
                    (ticker, buy_price, sell_price)
                    VALUES (?, ?, ?)""",
                    (
                        str(parameters.ticker),
                        str(parameters.buy_price),
                        str(parameters.sell_price),
                    )
                )
                await self.conn.commit()
                logger.info("Параметры акции %s сохранены в %s",
                            parameters.ticker, table_name)

        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error("Ошибка сохранения новой записи: %s", e)
            raise

        return self._get_db_path()

    async def delete_share(self, ticker: str) -> bool:
        """Удаляет акцию из базы данных по тикеру.

        Args:
            ticker: Тикер акции для удаления.

        Returns:
            bool: True если удаление прошло успешно, False
                если записи не существовало.

        Raises:
            sqlite3.Error: При ошибках работы с БД.
        """
        table_name = "tracking_parameters"

        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute(
                    f"DELETE FROM {table_name} WHERE ticker = ?",
                    (ticker,)
                )
                deleted_count = cursor.rowcount
                await self.conn.commit()

                if deleted_count > 0:
                    logger.info("Акция %s удалена из базы данных", ticker)
                    return True
                logger.warning("Акция %s не найдена в базе", ticker)
                return False

        except aiosqlite.Error as e:
            await self.conn.rollback()
            logger.error("Ошибка удаления акции %s: %s", ticker, e)
            raise

    async def get_all_tracked_stocks(self) -> list:
        """Получает все отслеживаемые акции из базы данных.

        Returns:
            List[TrackingParameters]: Список объектов TrackingParameters
            с данными акций.

        Raises:
            sqlite3.Error: При ошибках работы с БД.
        """
        table_name = "tracking_parameters"
        stocks = []

        try:
            async with self.conn.cursor() as cursor:
                await cursor.execute(f"SELECT * FROM {table_name}")
                rows = await cursor.fetchall()

                # структура таблицы: id, ticker, buy_price, sell_price
                for row in rows:
                    stock = TrackingParameters(
                        ticker=row[1],
                        buy_price=row[2],
                        sell_price=row[3]
                    )
                    stocks.append(stock)

                logger.info("Успешно получены %d акций из базы данных",
                            len(stocks))
                return stocks

        except aiosqlite.Error as e:
            logger.error("Ошибка при получении списка акций: %s", e)
            raise
