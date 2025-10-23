# EN: Core logic — read TBank CSV, apply categories, write outputs.
# RU: Основная логика — чтение CSV ТБанка, применение категорий и переформатирование, запись результатов.

from __future__ import annotations
from pathlib import Path
import pandas as pd

from .writers import write_qif, write_quicken_csv

# Original column names used in exports. Используемые в экспортируемых файлах оригинальные названия колонок.
RU_DATE = "Дата операции"
RU_AMOUNT = "Сумма платежа"
RU_CATEGORY = "Категория"
RU_DESC = "Описание"

def _read_tbank_csv(path: Path, *, delimiter: str, date_format: str, encoding: str = None) -> pd.DataFrame:
    """
    EN: Read CSV with typical encodings; normalize amount (decimal comma) and date.
    RU: Читаем CSV с типичными кодировками; нормализуем сумму (десятичная запятая) и дату.
    """
    # EN: Try UTF-8 with BOM, cp1251, then UTF-8.
    # RU: Пробуем UTF-8 с BOM, затем cp1251, затем UTF-8.
    df = None
    if encoding:# EN: If encoding specified, use it.
        try:
            df = pd.read_csv(path, sep=delimiter, encoding=encoding)
        except Exception as e:
            print(f"Failed to read CSV with encoding {encoding}: {e}")
            df = None
    else:# EN: Try common encodings if no encoding specified.
        for enc in ("utf-8-sig", "cp1251", "utf-8"):
            try:
                df = pd.read_csv(path, sep=delimiter, encoding=enc)
                break
            except Exception as e:
                # Optionally log the exception if needed for debugging
                print(f"Failed to read CSV with encoding {enc}: {e}")
                df = None
            if df is None:
                raise ValueError(f"Unable to read CSV: {path}")
    
    df = df[df['Статус'] != 'FAILED']  # Keep rows where 'Статус' is not 'FAILED'
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

    # EN: Category default from `Категория`.
    # RU: Категорию по умолчанию берём из `Категория`.
    if RU_CATEGORY in df.columns:
        df["Category"] = df[RU_CATEGORY].astype(str)
    else:
        df["Category"] = df.get("Category", "")
    return df

def _apply_categories(df: pd.DataFrame, categories_csv: Path, output_csv: Path = 'data/Output/new_categories.csv') -> pd.DataFrame:
    """
    EN: Optional substring-based mapping from categories CSV.
    RU: Опциональное сопоставление по подстроке из файла категорий.
    """
    if not categories_csv or not categories_csv.exists():
        return df
    
    try:
        cats = pd.read_csv(categories_csv)
    except Exception as e:
        # Log the exception or handle it appropriately
        return df
    
    if not {"key", "target"}.issubset(cats.columns):
        # Log a warning about the malformed categories file
        print("Categories CSV is missing required columns 'key' and 'target'.")
        return df
    
    # Apply category mapping
    df = df.merge(cats[['key', 'target']], left_on='Категория', right_on='key', how='left')
 
     # Find unique categories in operations that are not in categories
    new_categories = set(df["Category"].unique()) - set(df["key"].unique())

    # Create a DataFrame for new categories and save it to a CSV file
    if new_categories:
        print(f"New {len(new_categories)} categories in the csv report:")
        for category in new_categories:
            print(category)
    else:
        print("No new categories, ok.")
    new_cats_df = pd.DataFrame({"new_category": list(new_categories)})
    new_cats_df.to_csv(output_csv, index=False)       
    
    df["Category"] = df["target"]
    df = df["Date Amount Payee Memo Категория Category".split()]# Keep only relevant columns

    return df

def convert(*, input_csv: Path, categories_csv: Path | None, out_dir: Path, date_format: str, delimiter: str, encoding: str = None) -> None:
    """
    EN: Main entry — read, map categories, write QIF/CSV.
    RU: Главная функция — читаем, назначаем категории, записываем QIF/CSV.
    """
    df = _read_tbank_csv(input_csv, delimiter=delimiter, date_format=date_format, encoding=encoding)
    df = _apply_categories(df, categories_csv)
    cols = [c for c in ["Date", "Amount", "Payee", "Memo", "Category"] if c in df.columns]
    
    out = df[cols].copy()
    write_quicken_csv(out, out_dir / "quicken.csv")
    # QIF needs transliterated fields, not Cyrillic
    out["Memo"] = out["Memo"].apply(transliterate_russian)
    out["Payee"] = out["Payee"].apply(transliterate_russian)
    out["Date"] = pd.to_datetime(out["Date"], format="%d/%m/%Y", errors="coerce").dt.strftime("%m/%d/%Y")
    write_qif(out, out_dir / "import.qif")

def build_quicken_df(*, input_csv: Path, categories_csv: Path | None, date_format: str, delimiter: str, encoding: str):
    """
    Read, map, and return a normalized DataFrame with columns for Quicken.
    Читаем, назначаем категории и возвращаем нормализованный DataFrame с колонками для Quicken.
    """
    df = _read_tbank_csv(input_csv, delimiter=delimiter, date_format=date_format, encoding=encoding)
    df = _apply_categories(df, categories_csv)
    df["Memo"] = df["Memo"].apply(transliterate_russian)
    df["Payee"] = df["Payee"].apply(transliterate_russian)
    cols = [c for c in ["Date", "Amount", "Payee", "Memo", "Category"] if c in df.columns]
    return df[cols].copy()

def transliterate_russian(text):
    russian_to_english = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'zh', 
        'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 
        'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e','ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo', 'Ж': 'Zh',
        'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
        'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts',
        'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch', 'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu','Я': 'Ya' 
    }
    return ''.join([russian_to_english.get(char, char) for char in text])