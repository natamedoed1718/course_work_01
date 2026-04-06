import pandas as pd


from src.views import get_events, main


if __name__ == "__main__":
    df = pd.read_excel("../data/operations.xlsx", engine="openpyxl")
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    transactions = df.to_dict(orient="records")


    # Главная
    print(main("2021-11-24 12:00:00"))
    # События
    print(get_events("2018-04-17 12:00:00"))


