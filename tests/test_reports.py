import pandas as pd
import pytest
from pathlib import Path
from src.reports import report_to_file
from pandas import DataFrame

from src.reports import spending_by_category, spending_by_weekday


@pytest.fixture
def sample_df() -> pd.DataFrame:
    data = {
        "Дата операции": pd.to_datetime(
            [
                "2021-02-01",
                "2021-03-10",
                "2021-04-05",
                "2021-04-10",
                "2021-04-15",
            ]
        ),
        "Сумма операции": [-100, -200, -300, -400, 500],
        "Категория": [
            "Супермаркеты",
            "Фастфуд",
            "Супермаркеты",
            "Развлечения",
            "Пополнение",
        ],
    }
    return pd.DataFrame(data)


def test_spending_by_category(sample_df: pd.DataFrame) -> None:
    result = spending_by_category(sample_df, "Супермаркеты", "2021-04-30")

    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert "Сумма операции" in result.columns


def test_spending_by_category_empty(sample_df: pd.DataFrame) -> None:
    result = spending_by_category(sample_df, "Авто", "2021-04-30")

    assert isinstance(result, pd.DataFrame)
    assert result.empty


@pytest.mark.parametrize(
    "category, expected_empty",
    [
        ("Супермаркеты", False),
        ("Неизвестно", True),
    ],
)
def test_spending_by_category_parametrized(sample_df: pd.DataFrame, category: str, expected_empty: bool) -> None:
    result = spending_by_category(sample_df, category, "2021-04-30")

    assert isinstance(result, pd.DataFrame)
    assert result.empty == expected_empty


def test_spending_by_weekday(sample_df: pd.DataFrame) -> None:
    result = spending_by_weekday(sample_df, "2021-04-30")

    assert isinstance(result, pd.DataFrame)
    assert "weekday" in result.columns
    assert "Сумма операции" in result.columns


def test_spending_by_weekday_empty() -> None:
    df = pd.DataFrame(columns=["Дата операции", "Сумма операции"])

    result = spending_by_weekday(df, "2021-04-30")

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_report_file_created(
    tmp_path: Path,
    sample_df: pd.DataFrame,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path = tmp_path / "report.json"



    @report_to_file(str(file_path))
    def test_func(df:DataFrame) -> DataFrame:
        return df

    test_func(sample_df)

    assert file_path.exists()
