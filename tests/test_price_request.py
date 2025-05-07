"""Модуль тестирует класс PriceRequest."""

import pytest

from alert_price.services.prices_request import PriceRequest

pytestmark = pytest.mark.asyncio


class TestPriceRequest:
    """Набор тестов для класса PriceRequest."""

    async def test_request_share_sber_success(
        self,
        price_request,
        mock_aioresponse,
        sber_response_data
    ):
        """Тест успешного получения котировки SBER.

        Args:
            price_request: Фикстура клиента PriceRequest
            mock_aioresponse: Фикстура мокирования HTTP-запросов
            sber_response_data: Фикстура с тестовыми данными SBER
        """
        mock_aioresponse.get(
            PriceRequest.SHARE_SBER_URL,
            payload=sber_response_data
        )

        price = await price_request.request_share_sber()
        assert price == 250.50

    async def test_request_share_sber_invalid_ticker(
        self,
        price_request,
        mock_aioresponse
    ):
        """Тест обработки некорректного тикера в ответе.

        Args:
            price_request: Фикстура клиента PriceRequest
            mock_aioresponse: Фикстура мокирования HTTP-запросов
        """
        mock_aioresponse.get(
            PriceRequest.SHARE_SBER_URL,
            payload={"marketdata": {"data": [["SBERR", 250.50]]}}
        )

        with pytest.raises(ValueError, match="Неверный тикер"):
            await price_request.request_share_sber()

    async def test_request_securities_success(
        self,
        price_request,
        mock_aioresponse,
        sber_response_data,
        securities_response_data
    ):
        """Тест успешного получения списка ценных бумаг.

        Args:
            price_request: Фикстура клиента PriceRequest
            mock_aioresponse: Фикстура мокирования HTTP-запросов
            sber_response_data: Фикстура с тестовыми данными SBER
            securities_response_data: Фикстура с тестовыми данными ценных бумаг
        """
        # Мокаем оба запроса
        mock_aioresponse.get(
            PriceRequest.SHARE_SBER_URL,
            payload=sber_response_data
        )
        mock_aioresponse.get(
            PriceRequest.SHARE_URL,
            payload=securities_response_data
        )

        result = await price_request.request_securities()
        assert "securities" in result
        assert len(result["securities"]["data"]) == 2

    async def test_request_securities_column_changes(
        self,
        price_request,
        mock_aioresponse,
        sber_response_data
    ):
        """Тест обработки изменений в структуре колонок данных.

        Проверяет реакцию системы на изменение набора колонок в ответе API.

        Args:
            price_request: Фикстура клиента PriceRequest
            mock_aioresponse: Фикстура мокирования HTTP-запросов
            sber_response_data: Фикстура с тестовыми данными SBER

        Ожидаемое поведение:
            Должен вызывать ValueError с сообщением об изменении структуры
            данных, если полученные колонки не соответствуют ожидаемому
            шаблону.
        """
        invalid_columns = {
            "securities": {
                "columns": ["SECID", "SHORTNAME"],  # неполный список
                "data": []
            }
        }

        mock_aioresponse.get(
            PriceRequest.SHARE_SBER_URL,
            payload=sber_response_data
        )
        mock_aioresponse.get(
            PriceRequest.SHARE_URL,
            payload=invalid_columns
        )

        with pytest.raises(ValueError, match="Изменения в списке параметров"):
            await price_request.request_securities()

    @pytest.mark.parametrize("status_code", [400, 500, 404])
    async def test_request_failures(
        self,
        price_request,
        mock_aioresponse,
        status_code
    ):
        """Тест обработки различных HTTP-ошибок.

        Args:
            price_request: Фикстура клиента PriceRequest
            mock_aioresponse: Фикстура мокирования HTTP-запросов
            status_code: Код статуса HTTP для тестирования (параметризация)
        """
        mock_aioresponse.get(
            PriceRequest.SHARE_SBER_URL,
            status=status_code
        )

        with pytest.raises(ValueError):
            await price_request.request_share_sber()
