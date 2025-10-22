# tbank2qif

Конвертер CSV-отчётов Тинькофф Банка в форматы **QIF** (и вспомогательный CSV для Quicken). 
Поддерживает одиночный файл и пакетную обработку каталога. Есть карта категорий (опционально).

## Установка (dev)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## Запуск

### Одиночный файл → в каталог (создаст `import.qif` и `quicken.csv`)
```bash
tbank2qif -i ./data/Input/operations.csv --out-dir ./data/Output
```

### Одиночный файл c явным QIF-именем
```bash
tbank2qif -i ./data/Input/operations.csv -o ./data/Output/operations.qif
```

### Пакетная обработка всех CSV
```bash
tbank2qif --input-dir ./data/Input --output-dir ./data/Output
# для каждого файла создаст подпапку с import.qif и quicken.csv
```

### Доп. параметры
- `--categories examples/category.sample.csv` — CSV с правилами категорий (опционально)
- `--date-format` (по умолчанию `%d.%m.%Y`)
- `--delimiter` (по умолчанию `;`)
- `-v/--verbose`

## Структура
```
src/tbank2qif/
  core.py     # чтение, маппинг категорий, запись результатов
  writers.py  # функции записи CSV и QIF
  cli.py      # CLI с одиночным и пакетным режимами
  __main__.py # запуск как модуля
data/Input/   # входные CSV
data/Output/  # результаты
examples/     # примеры CSV
```

## Примечание по категориям
В `core.py` предусмотрена функция применения CSV категорий. См. `examples/category.sample.csv` для формата.

## Дополнительно
- `--encoding utf-8` — можно задать кодировку входного CSV (например, cp1251).
- `--combined` (в пакетном режиме) — формирует общий файл **combined.qif** в `--output-dir`.
- В репозитории есть **pytest**-тесты (`tests/`) и **GitHub Actions** для CI (`.github/workflows/ci.yml`).
