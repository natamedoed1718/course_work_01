import json
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def report_to_file(filename: Optional[str] = None) -> Callable:
    """Декоратор для записи отчета в файл"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            # имя файла
            if filename:
                file_name = filename
            else:
                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"report_{func.__name__}_{now}.json"

            try:
                if isinstance(result, pd.DataFrame):
                    data = result.to_dict(orient="records")
                else:
                    data = result

                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

                logger.info("Отчет сохранен в %s", file_name)

            except Exception as e:
                logger.exception("Ошибка записи отчета: %s", e)

            return result

        return wrapper

    return decorator


@report_to_file()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """Траты по категории за последние 3 месяца"""

    if date:
        end_date = pd.to_datetime(date)
    else:
        end_date = pd.Timestamp.now()

    start_date = end_date - pd.DateOffset(months=3)

    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    filtered = df[
        (df["Дата операции"] >= start_date)
        & (df["Дата операции"] <= end_date)
        & (df["Категория"] == category)
        & (df["Сумма операции"] < 0)
    ]

    result = filtered[["Дата операции", "Сумма операции"]]
    return result


@report_to_file()
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """Средние траты по дням недели за 3 месяца"""

    if date:
        end_date = pd.to_datetime(date)
    else:
        end_date = pd.Timestamp.now()

    start_date = end_date - pd.DateOffset(months=3)

    df = transactions.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    filtered = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date) & (df["Сумма операции"] < 0)]

    filtered["weekday"] = filtered["Дата операции"].dt.day_name()

    result = filtered.groupby("weekday")["Сумма операции"].mean().abs().round(2).reset_index()

    return result
