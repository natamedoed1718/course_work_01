import json
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.services import analyze_cashback, investment_bank

#  тестовый DataFrame для кешбэка


@pytest.fixture
def cashback_df() -> pd.DataFrame:
    data = {
        "Дата операции": pd.to_datetime(["2018-04-01", "2018-04-05", "2018-04-10", "2018-05-01"]),
        "Сумма операции": [-1200, -2500, -500, -3000],
        "Кэшбэк": [12, 25, 5, 30],
        "Категория": ["Супермаркеты", "Фастфуд", "Супермаркеты", "Фастфуд"],
    }
    return pd.DataFrame(data)


# Тест analyze_cashback


def test_analyze_cashback(cashback_df: pd.DataFrame) -> None:
    result_json = analyze_cashback(cashback_df, 2018, 4)
    result = json.loads(result_json)

    # проверяем, что категории есть и сумма кешбэка корректная
    assert "Супермаркеты" in result
    assert "Фастфуд" in result
    # проверяем значение кешбэка по правилам (1 рубль на каждые 100 рублей)
    assert result["Супермаркеты"] == (1200 + 500) // 100
    assert result["Фастфуд"] == 2500 // 100


# тестовые транзакции для инвесткопилки


@pytest.fixture
def transactions() -> List[Dict[str, Any]]:
    return [
        {"Дата операции": pd.Timestamp("2021-04-01"), "Сумма операции": -1712},
        {"Дата операции": pd.Timestamp("2021-04-15"), "Сумма операции": -245},
        {"Дата операции": pd.Timestamp("2021-04-20"), "Сумма операции": 500},  # доход, не учитываем
        {"Дата операции": pd.Timestamp("2021-05-01"), "Сумма операции": -130},  # другой месяц
    ]


# Параметризованный тест investment_bank


@pytest.mark.parametrize(
    "limit, expected",
    [
        (50, 38 + 5),  # округление 1712->1750 (38), 245->250 (5)
        (100, 88 + 55),  # округление 1712->1800 (88), 245->300 (55)
    ],
)
def test_investment_bank(transactions: List[Dict[str, Any]], limit: int, expected: float) -> None:
    total = investment_bank("2021-04", transactions, limit)
    assert total == expected


# Тест: нет расходов за месяц


def test_investment_bank_no_expenses(transactions: List[Dict[str, Any]]) -> None:
    total = investment_bank("2021-04", transactions, 50)
    assert total == 43.0
