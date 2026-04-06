import json
from typing import Any, List, Dict
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import get_events, main


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


@patch("src.views.get_stock")
@patch("src.views.get_currency")
@patch("src.views.get_top_transactions")
@patch("src.views.get_card_with_spend")
@patch("src.views.get_time_for_greeting")
@patch("src.views.get_path_and_period")
@patch("src.views.get_data_time")
def test_main(
    mock_get_data_time: Any,
    mock_get_path: Any,
    mock_greeting: Any,
    mock_cards: Any,
    mock_top: Any,
    mock_currency: Any,
    mock_stock: Any,
    sample_df: pd.DataFrame
) -> None:
    mock_get_data_time.return_value = ["01.05.2020 00:00:00", "20.05.2020 00:00:00"]
    mock_get_path.return_value = sample_df
    mock_greeting.return_value = "Добрый день"
    mock_cards.return_value = [{"last_digits": "1234", "total_spent": 100, "cashback": 1}]
    mock_top.return_value = [{"date": "01.05.2020", "amount": 100, "category": "Супермаркеты", "description": "Магазин"}]
    mock_currency.return_value = [{"currency": "USD", "rate": 70}]
    mock_stock.return_value = [{"stock": "AAPL", "price": 150}]

    result = main("2020-05-20 10:00:00")
    data = json.loads(result)

    assert data["greeting"] == "Добрый день"
    assert "cards" in data
    assert "top_transactions" in data
    assert "currency_rates" in data
    assert "stocks_prices" in data
