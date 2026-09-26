[English](README.md)

# takt

takt запускает бенчмарки pyperformance или ваши pyperf-скрипты.
Каждый результат он записывает сразу в одну или несколько SQL-БД.
Потом takt сравнивает результаты из этих БД и из файлов результатов.

## Установка

Только SQLite:

```bash
pip install takt
```

С поддержкой MariaDB:

```bash
pip install "takt[mariadb]"
```

## Быстрый старт

Запустить бенчмарк `nbody` и сохранить результат под именем `baseline <сегодняшняя дата UTC>`:

```bash
takt run -b nbody --fast --db sqlite:///bench.db --name "baseline {date}"
```

Сохранить уже готовый файл результата под именем `patched`:

```bash
takt import result.json --db sqlite:///bench.db --name patched
```

Сравнить два прогона:

```bash
takt compare "baseline 2026-09-25" patched --db sqlite:///bench.db
```

## Файл настроек

Положите `takt.toml` в текущий каталог, чтобы не повторять `--db`:

```toml
name_template = "nightly {date}"

[targets.local]
url = "sqlite:///bench.db"
```

С этим файлом `takt run -b nbody --fast` сохранит результат в `bench.db` под именем `nightly <дата>`.

## Совместимость

| takt | Python | pyperf | pyperformance |
|---|---|---|---|
| 0.1.0 | >=3.14 | >=2.10.0,<2.11 | >=1.14.0,<1.15 |

## Документация

Полная документация лежит в каталоге `docs`. Чтобы посмотреть её локально:

```bash
poetry run mkdocs serve
```

## Разработка

```bash
poetry run pytest
```

```bash
poetry run ruff check .
```

```bash
poetry run ruff format --check .
```

```bash
poetry run flake8 .
```

```bash
poetry run mypy
```

```bash
poetry run mkdocs build --strict
```

```bash
poetry build
```

Локальная сборка `TAKT_MYPYC=1 poetry build` копирует скомпилированные файлы `.so` в `src/takt`.
Python загружает их вместо файлов `.py`, поэтому ваши следующие правки не действуют, а `pytest` останавливается с ошибкой.
Удалите их:

```bash
find src/takt -name '*.so' -delete
```

## Автор

Шамиль Абдулаев, Python-разработчик, контрибьютор CPython и glibc: [ashm-dev.github.io](https://ashm-dev.github.io).
