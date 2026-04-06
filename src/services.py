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









