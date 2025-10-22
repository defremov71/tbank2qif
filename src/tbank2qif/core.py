# EN: Core logic — read TCS CSV, apply categories, write outputs.
# RU: Основная логика — чтение CSV TCS, применение категорий, запись результатов.

from __future__ import annotations
from pathlib import Path
import pandas as pd

from .writers import write_qif, write_quicken_csv

# EN/RU: Original TCS Russian column names used in exports.
RU_DATE = "Дата операции"
RU_AMOUNT = "Сумма платежа"
RU_CATEGORY = "Категория"
RU_DESC = "Описание"

def _read_tcs_csv(path: Path, *, delimiter: str, date_format: str, encoding: str) -> pd.DataFrame:
    """
    EN: Read TCS CSV with typical encodings; normalize amount (decimal comma) and date.
    RU: Читаем CSV TCS с типичными кодировками; нормализуем сумму (десятичная запятая) и дату.
    """
    # EN: Try UTF-8 with BOM, cp1251, then UTF-8.
    # RU: Пробуем UTF-8 с BOM, затем cp1251, затем UTF-8.
    df = None
    for enc in ("utf-8-sig", "cp1251", "utf-8"):
        try:
            df = pd.read_csv(path, sep=delimiter, encoding=encoding, encoding=enc)
            break
        except Exception:
            df = None
    if df is None:
        raise ValueError(f"Unable to read CSV: {path}")

    # EN: Normalize amount: remove spaces, replace comma with dot, parse to float.
    # RU: Нормализуем сумму: убираем пробелы, заменяем запятую на точку, приводим к float.
    if RU_AMOUNT in df.columns:
        df["Amount"] = (
            df[RU_AMOUNT]
            .astype(str)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )
    else:
        df["Amount"] = pd.to_numeric(df.get("Amount"), errors="coerce")

    # EN: Normalize date to dd/mm/YYYY string (Quicken-friendly).
    # RU: Приводим дату к строке dd/mm/YYYY (совместимо с Quicken).
    if RU_DATE in df.columns:
        df["Date"] = pd.to_datetime(df[RU_DATE], format=date_format, errors="coerce").dt.strftime("%d/%m/%Y")
    else:
        df["Date"] = pd.to_datetime(df.get("Date"), errors="coerce").dt.strftime("%d/%m/%Y")

    # EN: Payee/Memo from TCS `Описание` if present.
    # RU: Поля Payee/Memo берём из TCS `Описание`, если есть.
    if RU_DESC in df.columns:
        df["Payee"] = df[RU_DESC].astype(str)
        df["Memo"] = df[RU_DESC].astype(str)
    else:
        df["Payee"] = df.get("Payee", "")
        df["Memo"] = df.get("Memo", "")

    # EN: Category default from TCS `Категория`.
    # RU: Категорию по умолчанию берём из `Категория`.
    if RU_CATEGORY in df.columns:
        df["Category"] = df[RU_CATEGORY].astype(str)
    else:
        df["Category"] = df.get("Category", "")

    return df

def _apply_categories(df: pd.DataFrame, categories_csv: Path | None) -> pd.DataFrame:
    """
    EN: Optional substring-based mapping from categories CSV.
    RU: Опциональное сопоставление по подстроке из файла категорий.
    """
    if not categories_csv or not categories_csv.exists():
        return df
    cats = pd.read_csv(categories_csv)
    if not {"key","target"}.issubset(cats.columns):
        # EN/RU: Ignore malformed categories file.
        return df
    cats["key"] = cats["key"].astype(str).str.lower()
    cats["target"] = cats["target"].astype(str)
    pairs = list(zip(cats["key"], cats["target"]))

    def map_cat(text: str, default: str) -> str:
        tl = str(text).lower()
        for k, tgt in pairs:
            if k and k in tl:
                return tgt
        return default

    df["Category"] = [map_cat(m, c) for m, c in zip(df["Memo"], df["Category"])]
    return df

def convert(*, input_csv: Path, categories_csv: Path | None, out_dir: Path, date_format: str, delimiter: str, encoding: str = 'utf-8') -> None:
    """
    EN: Main entry — read, map categories, write QIF/CSV.
    RU: Главная функция — читаем, назначаем категории, записываем QIF/CSV.
    """
    df = _read_tcs_csv(input_csv, delimiter=delimiter, date_format=date_format, encoding=encoding)
    df = _apply_categories(df, categories_csv)
    cols = [c for c in ["Date", "Amount", "Payee", "Memo", "Category"] if c in df.columns]
    out = df[cols].copy()
    write_quicken_csv(out, out_dir / "quicken.csv")
    write_qif(out, out_dir / "import.qif")

def build_quicken_df(*, input_csv: Path, categories_csv: Path | None, date_format: str, delimiter: str, encoding: str):
    """
    Read, map, and return a normalized DataFrame with columns for Quicken.
    """
    df = _read_tcs_csv(input_csv, delimiter=delimiter, date_format=date_format, encoding=encoding)
    df = _apply_categories(df, categories_csv)
    cols = [c for c in ["Date", "Amount", "Payee", "Memo", "Category"] if c in df.columns]
    return df[cols].copy()
