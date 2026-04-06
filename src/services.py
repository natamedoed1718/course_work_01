import json
import logging
from functools import reduce
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

#  Анализ выгодных категорий кешбэка


def analyze_cashback(data: pd.DataFrame, year: int, month: int) -> str:
    """
    Функция анализирует выгодные категории кешбэка и возвращает JSON
    """
    logger.info("Анализ кешбэка за %d-%02d", year, month)

    # Фильтруем по дате
    filtered = data[(data["Дата операции"].dt.year == year) & (data["Дата операции"].dt.month == month)]

    # Оставляем только операции с кешбэком и расходами
    filtered = filtered[(filtered["Кэшбэк"] > 0) & (filtered["Сумма операции"] < 0)]

    # Группируем по категории и считаем сумму операций
    grouped = filtered.groupby("Категория")["Сумма операции"].sum().abs()

    # Считаем кешбэк: 1 рубль на каждые 100 рублей
    cashback_by_category = grouped.apply(lambda x: int(x // 100))

    result = cashback_by_category.to_dict()
    logger.info("Результат кешбэка: %s", result)
    return json.dumps(result, ensure_ascii=False, indent=4)


# Инвесткопилка


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """Рассчитывает сумму накоплений в инвесткопилке за месяц"""

    logger.info("Расчет инвесткопилки за %s с шагом %d", month, limit)

    # 1. Фильтр по месяцу
    filtered = list(filter(lambda t: t["Дата операции"].startswith(month), transactions))

    # 2. Только расходы
    expenses = list(filter(lambda t: t["Сумма операции"] < 0, filtered))

    # 3. Функция округления
    def calc_rounding(amount: float) -> float:
        amount = abs(amount)
        rounded = ((amount + limit - 1) // limit) * limit
        return rounded - amount

    # 4. Считаем накопления (functional style - это функция, которая сворачивает список в одно значение)
    total = reduce(lambda acc, t: acc + calc_rounding(t["Сумма операции"]), expenses, 0)

    total = round(total, 2)
    logger.info("Итого в инвесткопилке: %s", total)

    return total
import json
import logging
import pandas as pd

logger = logging.getLogger(__name__)

# 1. Анализ выгодных категорий кешбэка
def analyze_cashback(data: pd.DataFrame, year: int, month: int) -> str:
    """
    Функция анализирует выгодные категории кешбэка и возвращает JSON
    """
    logger.info("Анализ кешбэка за %d-%02d", year, month)

    # Фильтруем по дате
    filtered = data[
        (data["Дата операции"].dt.year == year) &
        (data["Дата операции"].dt.month == month)
    ]

    # Оставляем только операции с кешбэком и расходами
    filtered = filtered[
        (filtered["Кэшбэк"] > 0) &
        (filtered["Сумма операции"] < 0)
    ]

    # Группируем по категории и считаем сумму операций
    grouped = filtered.groupby("Категория")["Сумма операции"].sum().abs()

    # Считаем кешбэк: 1 рубль на каждые 100 рублей
    cashback_by_category = grouped.apply(lambda x: int(x // 100))

    result = cashback_by_category.to_dict()
    logger.info("Результат кешбэка: %s", result)
    return json.dumps(result, ensure_ascii=False, indent=4)
