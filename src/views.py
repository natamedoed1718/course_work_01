import json

from src.utils import (get_card_with_spend, get_currency, get_data_time, get_path_and_period, get_period_range,
                       get_stock, get_time_for_greeting, get_top_transactions, top_categories, transfers_and_cash)


# Страница "Главная"
def main(date_time: str) -> str:
    """Главную функция, принимающая на вход строку с датой и временем в формате
    YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ со следующими данными
    """
    # Делаем срез всего Excel file на определенный диапазон
    time_period = get_data_time(date_time)
    sorted_df = get_path_and_period(
        "../data/operations.xlsx", time_period
    )  # эта функция должна обрезать эксель файл по периоду, который в time_period

    # 1. Приветствие
    greeting = get_time_for_greeting()

    # 2. По каждой карте
    cards = get_card_with_spend(sorted_df)  # это DataFrame должен взять последние цифры номера карты

    # 3. Топ-5 транзакций по сумме платежа
    top_transactions = get_top_transactions(sorted_df, 5)  # получить топ 5 транзакций

    # 4. Курс валют
    currency_rates = get_currency("../user_settings.json")

    # 5. Стоимость акций из S&P500
    stocks_prices = get_stock("../user_settings.json")

    data = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stocks_prices": stocks_prices,
    }

    return json.dumps(data, ensure_ascii=False, indent=4)  # dumps потому что работаем со строками


# Страница "События"
def get_events(date_time: str, period: str = "M") -> dict:
    """
    Главная функция для страницы 'События'.
    Возвращает JSON с расходами, доходами, курсами валют и акциями.
    """
    # 1. Определяем диапазон дат для анализа, используем функцию get_path_and_period
    start, end = get_period_range(date_time, period)
    period_date = [start.strftime("%d.%m.%Y %H:%M:%S"), end.strftime("%d.%m.%Y %H:%M:%S")]

    # 2. Загружаем Excel-файл с операциями
    df = get_path_and_period("../data/operations.xlsx", period_date)

    # 3. Фильтруем данные по выбранному диапазону
    filtered_df = df[(df["Дата операции"] >= start) & (df["Дата операции"] <= end)]

    # 4. Разделяем расходы и поступления
    # Расходы — сумма операций < 0, доходы — сумма операций > 0
    expenses_df = filtered_df[filtered_df["Сумма операции"] < 0]
    income_df = filtered_df[filtered_df["Сумма операции"] > 0]

    # 5. Считаем общие суммы и топ-7 категорий расходов
    expenses_main = top_categories(expenses_df)  # топ-7 категорий + Остальное
    income_main = top_categories(income_df)  # топ-7 категорий доходов + Остальное

    # 6. Считаем суммы по категориям "Переводы и наличные"
    expenses_transfers = transfers_and_cash(expenses_df)

    # 7. Общие суммы по расходам и доходам
    total_expenses = int(round(expenses_df["Сумма операции"].abs().sum()))
    total_income = int(round(income_df["Сумма операции"].sum()))

    # 8. Получаем курсы валют и стоимость акций из JSON настроек
    currency_rates = get_currency("../user_settings.json")
    stock_prices = get_stock("../user_settings.json")

    result = {
        "expenses": {"total_amount": total_expenses, "main": expenses_main, "transfers_and_cash": expenses_transfers},
        "income": {"total_amount": total_income, "main": income_main},
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }

    return json.dumps(result, ensure_ascii=False, indent=4)
