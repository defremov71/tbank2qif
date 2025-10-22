# EN: Output writers for CSV and QIF formats.
# RU: Запись результатов в CSV и QIF.

from pathlib import Path
import pandas as pd

def write_quicken_csv(df: pd.DataFrame, path: Path) -> None:
    """EN: Write CSV for Quicken import. RU: Запись CSV для импорта в Quicken."""
    df.to_csv(path, index=False)

def write_qif(df: pd.DataFrame, path: Path) -> None:
    """EN: Write a minimal QIF file. RU: Запись минимального QIF-файла."""
    with path.open("w", encoding="utf-8") as f:
        f.write("!Type:Bank\n")
        for _, r in df.iterrows():
            date = r.get("Date", "")
            amount = r.get("Amount", "")
            payee = r.get("Payee", "")
            memo = r.get("Memo", "")
            category = r.get("Category", "")
            # EN: QIF record structure. RU: Структура записи QIF.
            f.write(f"D{date}\n")     # EN: Date / RU: Дата
            f.write(f"T{amount}\n")   # EN: Amount / RU: Сумма
            if payee: f.write(f"P{payee}\n")  # EN: Payee / RU: Получатель
            if memo: f.write(f"M{memo}\n")    # EN: Memo / RU: Примечание
            if category: f.write(f"L{category}\n")  # EN: Category / RU: Категория
            f.write("^\n")            # EN: End of transaction / RU: Конец операции

def write_qif_append(df: pd.DataFrame, path: Path) -> None:
    """
    Append QIF transactions to an existing or new QIF file. Writes header if file absent/empty.
    """
    header_needed = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8") as f:
        if header_needed:
            f.write("!Type:Bank\n")
        for _, r in df.iterrows():
            date = r.get("Date", "")
            amount = r.get("Amount", "")
            payee = r.get("Payee", "")
            memo = r.get("Memo", "")
            category = r.get("Category", "")
            if date: f.write(f"D{date}\n")
            if amount != "": f.write(f"T{amount}\n")
            if payee: f.write(f"P{payee}\n")
            if memo: f.write(f"M{memo}\n")
            if category: f.write(f"L{category}\n")
            f.write("^\n")
