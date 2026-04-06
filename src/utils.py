import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import requests
from typing import Any
from pandas import DataFrame

from src.config import API_KEY, URL_CURRENCY, URL_STOCK

# Настройка базового логгера
# Создаём папку logs, если её нет
logs_dir = os.path.join(os.path.dirname(__file__), "../logs")
os.makedirs(logs_dir, exist_ok=True)

# Путь к файлу логов
log_file = os.path.join(logs_dir, "example.log")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=log_file,
    filemode="a",  # добавление к существующему файлу
)
logger = logging.getLogger(__name__)


def get_time_for_greeting() -> str:
    """
    Функция возвращает «Доброе утро» / «Добрый день» / «Добрый вечер»
    /«Доброй ночи» в зависимости от текущего времени.
    """

    # текущий час достаточно для того, чтобы узнать текущее всё

    hour = datetime.now().hour
    logger.debug("Текущий час: %d", hour)
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_data_time(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """Функция форматирует дату и время"""

    # создаем объект строки в объект datetime для удобного сравнения
    logger.info("Форматирование даты: %s", date_time)
    dt = datetime.strptime(date_time, date_format)
    start_of_month = dt.replace(day=1, hour=0, minute=0, second=0)
    logger.debug("Начало месяца: %s", start_of_month)
    return [start_of_month.strftime("%d.%m.%Y %H:%M:%S"), dt.strftime("%d.%m.%Y %H:%M:%S")]


def get_path_and_period(path_to_file: str, period_date: list) -> DataFrame:
    """
    Функция принимает путь к Excel файлу, список дат начала и конца,
    и возвращает таблицу в заданном периоде
    """
    logger.info("Чтение файла Excel: %s", path_to_file)
    df = pd.read_excel(path_to_file)
    # перевести в объект datetime, так как строки мы сравнивать не можем
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    # хочу взять из списка period_date первый элемент для сравнения
    start_date = datetime.strptime(period_date[0], "%d.%m.%Y %H:%M:%S")
    end_date = datetime.strptime(period_date[1], "%d.%m.%Y %H:%M:%S")

    # выражение идёт от большего к меньшему, так как в выводе просят от 20 до 1 числа
    filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

    # сортировать фильтр датафрейм
    sorted_df = filtered_df.sort_values(by="Дата операции", ascending=True)
    logger.debug("Отфильтровано %d строк", len(sorted_df))
    return sorted_df


def get_card_with_spend(sorted_df: pd.DataFrame) -> list[dict]:
    """
    Функция принимает DataFrame и возвращает список карт с расходами
    """
    logger.info("Начало вычисления расходов по картам")

    card_spent_transactions = []
    card_sorted = sorted_df[sorted_df["Сумма операции"] < 0]

    grouped = card_sorted.groupby("Номер карты")["Сумма операции"].sum()
    logger.debug("Группировка по картам завершена: %s", grouped.to_dict())

    for card, total in grouped.items():
        total_spent = abs(round(total, 2))
        cashback = round(total_spent / 100, 2)
        card_spent_transactions.append(
            {"last_digits": str(card)[-4:], "total_spent": total_spent, "cashback": cashback}
        )
        logger.info("Карта %s: расходы %s, кэшбэк %s", str(card)[-4:], total_spent, cashback)

    logger.info("Вычисление расходов по картам завершено")
    return card_spent_transactions


def get_top_transactions(sorted_df: pd.DataFrame, get_top: int) -> list[dict]:
    sorted_pay_df = sorted_df.sort_values(by="Сумма операции", ascending=False)
    top_transactions = sorted_pay_df.head(get_top)

    result = []
    for _, row in top_transactions.iterrows():
        result.append(
            {
                "date": pd.to_datetime(row["Дата операции"], dayfirst=True).strftime("%d.%m.%Y"),
                "amount": round(row["Сумма операции"], 2),
                "category": row["Категория"],
                "description": row["Описание"],
            }
        )
    return result


def get_currency(path_to_json: str) -> list[dict]:
    logger.info("Получение курсов валют из файла %s", path_to_json)
    currency_rates = []
    try:
        with open(path_to_json, "r", encoding="utf-8") as json_file:
            settings = json.load(json_file)
            currencies = settings["user_currencies"]
            logger.debug("Запрошены валюты: %s", currencies)

        for currency in currencies:
            params = {"amount": str(1), "from": f"{currency}", "to": "RUB"}
            headers = {"apikey": f"{API_KEY}"}
            response = requests.get(URL_CURRENCY, headers=headers, params=params)

            if response.status_code == 200:
                result = response.json()
                rate = round(result["result"], 2)
                currency_rates.append({"currency": currency, "rate": rate})
                logger.info("Курс %s: %s", currency, rate)
            else:
                logger.error("Ошибка при запросе курса %s: статус %s", currency, response.status_code)
    except FileNotFoundError:
        logger.error("Файл %s не найден", path_to_json)
    except Exception as e:
        logger.exception("Ошибка при получении курсов валют: %s", e)

    return currency_rates


def get_stock(path_to_json: str) -> list[dict]:
    """Возвращает цены акций из JSON и API"""
    logger.info("Получение цен акций из файла %s", path_to_json)
    stock_rates = []
    try:
        with open(path_to_json, "r", encoding="utf-8") as f:
            settings = json.load(f)
            stocks = settings["user_stocks"]
            logger.debug("Запрошены акции: %s", stocks)

        for stock in stocks:
            params = {"function": "GLOBAL_QUOTE", "symbol": stock, "apikey": API_KEY}
            response = requests.get(URL_STOCK, params=params)
            if response.status_code == 200:
                price = response.json().get("Global Quote", {}).get("05. price")
                price = round(float(price), 2) if price else 0.0
                stock_rates.append({"stock": stock, "price": price})
                logger.info("Акция %s: %s", stock, price)
            else:
                logger.error("Ошибка запроса акции %s: статус %s", stock, response.status_code)
    except FileNotFoundError:
        logger.error("Файл %s не найден", path_to_json)
    except Exception as e:
        logger.exception("Ошибка при получении цен акций: %s", e)
    return stock_rates


# События
def get_period_range(date_time: str, period: str = "M") -> tuple[datetime, datetime]:
    """Возвращает начало и конец периода для анализа транзакций на основе переданной даты"""
    logger.info("Вычисление периода для %s с типом %s", date_time, period)
    dt = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")  # Преобразуем строку "" в объект datetime

    # делаем арифметику с датами
    if period == "W":  # неделя
        start = dt - timedelta(days=dt.weekday())  # понедельник
    elif period == "M":  # месяц
        start = dt.replace(day=1)
    elif period == "Y":  # год
        start = dt.replace(month=1, day=1)
    elif period == "ALL":
        start = datetime.min
    else:
        start = dt.replace(day=1)

    end = dt
    logger.debug("Период: %s — %s", start, end)
    return start, end


def top_categories(df: pd.DataFrame, top_n: int = 7) -> List[Dict[str, int]]:
    """Функция возвращает топ-N категорий по сумме операций и объединяет остальные в "Остальное" """
    logger.info("Вычисление топ-%d категорий", top_n)
    grouped = df.groupby("Категория")["Сумма операции"].sum()  # группируем по категории и суммируем суммы операций
    grouped = grouped.abs().sort_values(ascending=False)  # по убыванию, положительные
    top = grouped.head(top_n).reset_index()  # берём топ-N категорий
    others = grouped[top_n:].sum()

    # формируем список словарей для JSON
    result = [{"category": row["Категория"], "amount": int(round(row["Сумма операции"]))} for _, row in top.iterrows()]
    if others > 0:
        result.append({"category": "Остальное", "amount": int(round(others))})
    logger.debug("Топ категории: %s", result)
    return result


def transfers_and_cash(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Возвращает суммы операций по категориям 'Наличные' и 'Переводы'"""
    logger.info("Вычисление сумм по категориям 'Наличные' и 'Переводы'")
    filtered = df[df["Категория"].isin(["Наличные", "Переводы"])]
    grouped = filtered.groupby("Категория")["Сумма операции"].sum().abs().sort_values(ascending=False)
    result = [{"category": cat, "amount": int(round(amount))} for cat, amount in grouped.items()]
    logger.debug("Суммы по категориям: %s", result)
    return result
