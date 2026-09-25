# takt

takt запускает бенчмарки pyperformance или ваши pyperf-скрипты.
Каждый результат он записывает сразу в одну или несколько SQL-БД.
Потом takt сравнивает результаты из этих БД и из файлов результатов.

## Установка

Только SQLite:

```bash
pip install takt
```

С драйверами других БД (в v0 — MariaDB):

```bash
pip install "takt[db]"
```

Нужен Python 3.14 или новее.

## Быстрый старт

Запустить бенчмарк `nbody` и сохранить результат в файл SQLite под именем `baseline <сегодняшняя дата UTC>`:

```bash
takt run -b nbody --fast --db sqlite:///bench.db --name "baseline {date}"
```

Сохранить уже готовый файл результата, например прогон Python с патчем, под именем `patched`:

```bash
takt import result.json --db sqlite:///bench.db --name patched
```

Сравнить два прогона по имени:

```bash
takt compare "baseline 2026-09-25" patched --db sqlite:///bench.db
```

## Что читать дальше

- [Настройка](configuration.md): целевые БД, `takt.toml`, переменные окружения и имена прогонов.
- [Команды](commands.md): `takt run`, `takt import`, `takt compare` и коды выхода.
- [Модель данных](data-model.md): таблицы, которые создаёт takt, для своих SQL-запросов.
- [API](api.md): те же команды в виде Python-библиотеки.
