[English version](README.md)

# takt

takt запускает бенчмарки pyperformance и pyperf и сохраняет результаты в SQL-базы данных.

## Установка

Только SQLite:

    pip install takt

SQLite и MariaDB:

    pip install "takt[db]"

## Команды

- `takt run` запускает бенчмарки и сохраняет результат.
- `takt import` сохраняет готовый JSON-результат pyperf.
- `takt compare` сравнивает результаты из файлов и баз данных.

## Требования

Python 3.14 или новее.
