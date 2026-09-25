[Русская версия](README.ru.md)

# takt

takt runs pyperformance and pyperf benchmarks and stores the results in SQL databases.

## Installation

SQLite only:

    pip install takt

SQLite and MariaDB:

    pip install "takt[db]"

## Commands

- `takt run` runs benchmarks and stores the result.
- `takt import` stores an existing pyperf JSON result.
- `takt compare` compares results from files and databases.

## Requirements

Python 3.14 or newer.
