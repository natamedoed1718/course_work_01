import pandas as pd

from src.services import analyze_cashback, investment_bank
from src.views import get_events, main

if __name__ == "__main__":
    df = pd.read_excel("../data/operations.xlsx", engine="openpyxl")
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    transactions = df.to_dict(orient="records")

    # Главная
    print(main("2021-11-24 12:00:00"))
    # События
    print(get_events("2018-04-17 12:00:00"))

    # Выгодные категории повышенного кешбэка
    result = analyze_cashback(df, 2018, 4)
    print(result)
    # Инвестиции(копилка)
    result = investment_bank("2021-04", transactions, 50)
    print(result)
