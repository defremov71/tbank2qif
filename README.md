# 🧾 tbank2qif — конвертер отчётов по операциям Т-Банка в формат Quicken (QIF)

`tbank2qif` — это лёгкая Python-утилита, которая преобразует CSV-отчёты операций из Т-Банка в формат **QIF**, совместимый с Quicken.  
Подходит для личного финансового учёта и автоматизации импорта транзакций.

### 🚀 Возможности

- 🧩 Применение пользовательских категорий (`--categories`)
- ⚙️ Выбор кодировки (`--encoding utf-8`, `cp1251` и др.) и транслитерация операций
- ✅ Встроенные автотесты (`pytest`) и GitHub Actions CI

### 📄 Примеры
Примеры входных и категорийных файлов находятся в папке [`examples/`](./examples).

---

> Разработано для пользователей Т-Банка, для экспорта операций для учёта в Quicken в формате .qif.

## Установка (dev)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Запуск

### Одиночный файл → в каталог data/Input/ (создаст в data/Output `import.qif` и `quicken.csv`)
```bash
tbank2qif -i ./data/Input/operations.csv --out-dir ./data/Output
```

### Одиночный файл c явным QIF-именем
```bash
tbank2qif -i ./data/Input/operations.csv -o ./data/Output/operations.qif
```


### Доп. параметры
- `--categories examples/category.sample.csv` — CSV с правилами категорий (опционально)
- `--date-format` (по умолчанию "%d.%m.%Y %H:%M:%S")
- `--delimiter` (по умолчанию `;`)
- `-v/--verbose`

## Структура
```
src/tbank2qif/
  core.py     # чтение, маппинг категорий, запись результатов
  writers.py  # функции записи CSV и QIF
  cli.py      # CLI основной модуль программы
  __main__.py # запуск как модуля
data/Input/   # входные CSV
data/Output/  # результаты
examples/     # примеры CSV
```

## Примечание по категориям
В `core.py` предусмотрена функция применения CSV категорий. См. `examples/category.sample.csv` для формата.

## Дополнительно
- `--encoding utf-8` — можно задать кодировку входного CSV (например, cp1251).
- В репозитории есть **pytest**-тесты (`tests/`) и **GitHub Actions** для CI (`.github/workflows/ci.yml`).
