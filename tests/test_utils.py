from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from pandas import DataFrame

from src.utils import (get_card_with_spend, get_currency, get_data_time, get_path_and_period, get_stock,
                       get_time_for_greeting, get_top_transactions, top_categories, transfers_and_cash)


@pytest.fixture
def sample_df() -> DataFrame:
    data = {
        "Дата операции": ["2022-01-10", "2022-01-15", "2022-01-20", "2022-01-25"],
        "Дата платежа": ["2022-01-10", "2022-01-15", "2022-01-20", "2022-01-25"],
        "Номер карты": ["1111****1111", "2222****2222", "1111****1111", "3333****3333"],
        "Сумма операции": [-1500, -2500, 3000, -500],
        "Сумма операции с округлением": [-1500, -2500, 3000, -500],
        "Кэшбэк": [0, 0, 0, 0],
        "Категория": ["Супермаркеты", "Фастфуд", "Пополнение_BANK007", "Наличные"],
        "Описание": ["Покупка", "Бургер", "Пополнение", "Снятие"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    df["Дата платежа"] = pd.to_datetime(df["Дата платежа"])
    return pd.DataFrame(data)


# get_card_with_spend
def test_get_card_with_spend(sample_df: DataFrame) -> None:
    result: List[Dict[str, Any]] = get_card_with_spend(sample_df)
    assert isinstance(result, list)
    assert all("last_digits" in r and "total_spent" in r and "cashback" in r for r in result)



# get_top_transactions
def test_get_top_transactions(sample_df: DataFrame) -> None:
    top: List[Dict[str, Any]] = get_top_transactions(sample_df, 2)
    assert len(top) == 2
    assert all("date" in t and "amount" in t and "category" in t for t in top)



# top_categories
@pytest.mark.parametrize("top_n, expected_len", [(2, 3), (5, 3)])
def test_top_categories(sample_df: DataFrame, top_n: int, expected_len: int) -> None:
    expenses_df: DataFrame = sample_df[sample_df["Сумма операции"] < 0]
    result: List[Dict] = top_categories(expenses_df, top_n)
    assert isinstance(result, list)
    assert len(result) == expected_len
    assert "category" in result[0] and "amount" in result[0]


# transfers_and_cash
def test_transfers_and_cash(sample_df: DataFrame) -> None:
    result: List[Dict[str, Any]] = transfers_and_cash(sample_df)
    assert isinstance(result, list)
    assert all("category" in r and "amount" in r for r in result)
    assert all(r["category"] in ["Наличные", "Переводы"] for r in result)


# get_currency (mock)
@patch("src.utils.requests.get")
def test_get_currency(mock_get: MagicMock, tmp_path: Path) -> None:
    # создаем временный user_settings.json
    json_file = tmp_path / "user_settings.json"
    json_file.write_text('{"user_currencies": ["USD"], "user_stocks": ["AAPL"]}', encoding="utf-8")

    # создаем Mock ответа API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": 73.5}
    mock_get.return_value = mock_response

    rates = get_currency(str(json_file))
    assert isinstance(rates, list)
    assert rates[0]["currency"] == "USD"
    assert rates[0]["rate"] == 73.5


# get_stock (mock)
@patch("src.utils.requests.get")
def test_get_stock(mock_get: MagicMock, tmp_path: Path) -> None:
    # создаем временный user_settings.json
    json_file = tmp_path / "user_settings.json"
    json_file.write_text('{"user_currencies": ["USD"], "user_stocks": ["AAPL"]}', encoding="utf-8")

    # создаем мок-ответ
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"Global Quote": {"05. price": "150.12"}}

    # говорим requests.get возвращать мок-ответ
    mock_get.return_value = mock_response

    stocks = get_stock(str(json_file))
    assert isinstance(stocks, list)
    assert stocks[0]["stock"] == "AAPL"
    assert stocks[0]["price"] == 150.12


def test_get_time_for_greeting_morning() -> None:
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 8
        mock_datetime.now.return_value = mock_datetime.now.return_value
        greeting = get_time_for_greeting()
        assert greeting == "Доброе утро"


def test_get_time_for_greeting_evening() -> None:
    with patch("src.utils.datetime") as mock_datetime:
        mock_datetime.now.return_value.hour = 20
        mock_datetime.now.return_value = mock_datetime.now.return_value
        greeting = get_time_for_greeting()
        assert greeting == "Добрый вечер"


def test_get_data_time() -> None:
    date_str = "2024-04-04 15:30:00"
    result = get_data_time(date_str)
    assert result[0].endswith("00:00:00")  # начало месяца
    assert result[1].startswith("04.04.2024")  # сама дата


def test_get_path_and_period(tmp_path: Path) -> None:
    # создаем фиктивный Excel файл
    df = pd.DataFrame(
        {
            "Дата операции": ["04.04.2024 10:00:00", "05.04.2024 12:00:00"],
            "Сумма операции": [100, 200],
            "Категория": ["Продукты", "Развлечения"],
        }
    )
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)

    period = ["04.04.2024 00:00:00", "05.04.2024 23:59:59"]
    sorted_df = get_path_and_period(str(file_path), period)
    assert len(sorted_df) == 2
    assert sorted_df["Сумма операции"].iloc[0] == 100
