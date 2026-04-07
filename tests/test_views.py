import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import get_events, main

# фикстура DataFrame


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2020-05-01", "2020-05-02"]),
            "Дата платежа": ["01.05.2020", "02.05.2020"],
            "Номер карты": ["*1234", "*5678"],
            "Сумма операции": [-100, 200],
            "Категория": ["Супермаркеты", "Пополнение"],
            "Описание": ["Магазин", "Зарплата"],
        }
    )


# main()


@patch("src.views.get_stock")
@patch("src.views.get_currency")
@patch("src.views.get_top_transactions")
@patch("src.views.get_card_with_spend")
@patch("src.views.get_time_for_greeting")
@patch("src.views.get_path_and_period")
@patch("src.views.get_data_time")
def test_main(
    mock_get_data_time, mock_get_path, mock_greeting, mock_cards, mock_top, mock_currency, mock_stock, sample_df
):
    # Mocks
    mock_get_data_time.return_value = ["01.05.2020 00:00:00", "20.05.2020 00:00:00"]
    mock_get_path.return_value = sample_df
    mock_greeting.return_value = "Добрый день"
    mock_cards.return_value = [{"last_digits": "1234", "total_spent": 100, "cashback": 1}]
    mock_top.return_value = [
        {"date": "01.05.2020", "amount": 100, "category": "Супермаркеты", "description": "Магазин"}
    ]
    mock_currency.return_value = [{"currency": "USD", "rate": 70}]
    mock_stock.return_value = [{"stock": "AAPL", "price": 150}]

    result = main("2020-05-20 10:00:00")

    # проверяем что это JSON-строка
    data = json.loads(result)

    assert data["greeting"] == "Добрый день"
    assert "cards" in data
    assert "top_transactions" in data
    assert "currency_rates" in data
    assert "stocks_prices" in data


# get_events()


@patch("src.views.get_stock")
@patch("src.views.get_currency")
@patch("src.views.transfers_and_cash")
@patch("src.views.top_categories")
@patch("src.views.get_path_and_period")
@patch("src.views.get_period_range")
def test_get_events(mock_period, mock_path, mock_top, mock_transfers, mock_currency, mock_stock, sample_df):
    # Mocks
    from datetime import datetime

    mock_period.return_value = (datetime(2020, 5, 1), datetime(2020, 5, 20))
    mock_path.return_value = sample_df

    mock_top.return_value = [{"category": "Супермаркеты", "amount": 100}]
    mock_transfers.return_value = [{"category": "Переводы", "amount": 50}]
    mock_currency.return_value = [{"currency": "USD", "rate": 70}]
    mock_stock.return_value = [{"stock": "AAPL", "price": 150}]

    result = get_events("2020-05-20 10:00:00")

    # проверки
    assert "expenses" in result
    assert "income" in result
    assert "currency_rates" in result
    assert "stock_prices" in result

    assert isinstance(result["expenses"]["total_amount"], int)
    assert isinstance(result["income"]["total_amount"], int)
