# Модель данных

На этой странице описаны таблицы, которые takt создаёт в каждой целевой БД.
По ним можно строить свои SQL-запросы и дашборды по сохранённым результатам.

## Таблицы

Все таблицы начинаются с `takt_`, поэтому они не пересекаются с вашими таблицами в общей БД.
takt хранит только эти таблицы, исходный JSON-файл он не сохраняет.

```text
takt_suite            строка на каждый сохранённый результат
└─ takt_benchmark     строка на каждый бенчмарк результата
   └─ takt_worker_run строка на каждый запуск воркера pyperf в бенчмарке
      ├─ takt_measurement   строка на каждое значение замера или прогрева
      └─ takt_run_metadata  строка метаданных на каждый запуск воркера
takt_loaded_hash      хеши сохранённых результатов
takt_alembic_version  версия схемы
```

Ключи состоят из нескольких колонок, автоинкремента нет.
В каждой дочерней таблице есть `suite_hash`, поэтому все строки одного результата находятся по его хешу.
Все позиции считаются с 0 и идут в том же порядке, что в файле результата.

### takt_suite

Один сохранённый результат, то есть один JSON-файл pyperf.

| Колонка | Тип | NULL | Что хранит |
|---|---|---|---|
| `hash` | CHAR(64) | нет | первичный ключ; SHA-256 результата |
| `name` | VARCHAR(255) | да | имя прогона; NULL, если имя не задано |
| `format_version` | VARCHAR(16) | нет | версия формата файла pyperf: `1.0`, `5` или `6` |
| `source` | VARCHAR(16) | нет | `run` или `import`: какая команда сохранила результат |
| `result_date` | DATETIME | да | самая ранняя `date` среди запусков воркеров; местное время машины с бенчмарками, без часового пояса |
| `loaded_at` | DATETIME | нет | когда takt сохранил результат; UTC без часового пояса |

Индексы: `name`, `result_date`.

### takt_benchmark

Один бенчмарк внутри результата.

| Колонка | Тип | NULL | Что хранит |
|---|---|---|---|
| `suite_hash` | CHAR(64) | нет | часть первичного ключа; ссылка на `takt_suite.hash` |
| `benchmark_position` | INTEGER | нет | часть первичного ключа; позиция бенчмарка в файле |
| `name` | VARCHAR(255) | нет | имя бенчмарка, например `nbody` |

### takt_worker_run

Один запуск процесса-воркера pyperf: один элемент `runs` в файле результата.

| Колонка | Тип | NULL | Что хранит |
|---|---|---|---|
| `suite_hash` | CHAR(64) | нет | часть первичного ключа |
| `benchmark_position` | INTEGER | нет | часть первичного ключа |
| `run_position` | INTEGER | нет | часть первичного ключа; позиция запуска внутри бенчмарка |

`(suite_hash, benchmark_position)` ссылается на `takt_benchmark`.

### takt_measurement

Одно значение замера или одно значение прогрева.

| Колонка | Тип | NULL | Что хранит |
|---|---|---|---|
| `suite_hash` | CHAR(64) | нет | часть первичного ключа |
| `benchmark_position` | INTEGER | нет | часть первичного ключа |
| `run_position` | INTEGER | нет | часть первичного ключа |
| `kind` | VARCHAR(8) | нет | часть первичного ключа; `value` — замер, `warmup` — прогрев |
| `position` | INTEGER | нет | часть первичного ключа; позиция среди значений того же вида |
| `loops` | INTEGER | да | число итераций прогрева; NULL для `value` |
| `value` | DOUBLE | нет | значение в единицах бенчмарка (`unit` в метаданных) на одну итерацию |

`(suite_hash, benchmark_position, run_position)` ссылается на `takt_worker_run`.
У калибровочных запусков есть только строки `warmup`.

### takt_run_metadata

Метаданные одного запуска воркера.

| Колонка | Тип | NULL | Что хранит |
|---|---|---|---|
| `suite_hash` | CHAR(64) | нет | часть первичного ключа |
| `benchmark_position` | INTEGER | нет | часть первичного ключа |
| `run_position` | INTEGER | нет | часть первичного ключа |
| колонка на каждый известный ключ pyperf | см. ниже | да | значение ключа; NULL, если у запуска его нет |
| `custom` | JSON | да | все остальные ключи одним JSON-объектом; NULL, если их нет |

`(suite_hash, benchmark_position, run_position)` ссылается на `takt_worker_run`.

Колонка называется так же, как ключ pyperf:

| Тип | Колонки |
|---|---|
| BIGINT | `loops`, `inner_loops`, `calibrate_loops`, `recalibrate_loops`, `calibrate_warmups`, `recalibrate_warmups`, `mem_max_rss`, `command_max_rss`, `mem_peak_pagefile_usage`, `cpu_count`, `runnable_threads`, `timeit_duplicate` |
| DOUBLE | `duration`, `uptime`, `load_avg_1min` |
| JSON | `tags` (список строк) |
| TEXT | `name`, `unit`, `date`, `timer`, `description`, `python_version`, `python_implementation`, `python_executable`, `python_compiler`, `python_cflags`, `python_config_args`, `python_hash_seed`, `python_gc`, `cpu_affinity`, `cpu_config`, `cpu_freq`, `cpu_machine`, `cpu_model_name`, `cpu_temp`, `aslr`, `hostname`, `platform`, `boot_time`, `perf_version`, `performance_version`, `timeit_stmt`, `timeit_setup`, `timeit_teardown`, `commit_id`, `commit_branch`, `commit_date`, `patch_file`, `hooks` |

### takt_loaded_hash

Хеши всех сохранённых результатов.
По этой таблице takt быстро проверяет, есть ли результат в БД.

| Колонка | Тип | NULL | Что хранит |
|---|---|---|---|
| `hash` | CHAR(64) | нет | первичный ключ; то же значение, что `takt_suite.hash` |

### takt_alembic_version

Версия схемы этой БД.
takt сам читает и обновляет её, менять её не нужно.

## Правило метаданных

В файле pyperf ключ, который одинаков у всех запусков, записан один раз — на уровне бенчмарка или на уровне файла.
takt разворачивает это обратно: в каждой строке `takt_run_metadata` есть полный набор ключей своего запуска, включая ключи с верхних уровней.
Поэтому фильтровать можно по любому ключу, например `hostname` или `python_version`, без соединения с другими уровнями.

Ключ, которого нет в таблице выше, или ключ со значением неожиданного типа попадает в `custom`.
Например, ключи, добавленные через `pyperf.Runner(metadata=...)`, лежат в `custom`.

## Пример запроса

Среднее значение бенчмарка `nbody` по каждому прогону с именем `baseline`:

```sql
SELECT s.name, s.result_date, AVG(m.value) AS mean_seconds
FROM takt_suite s
JOIN takt_measurement m ON m.suite_hash = s.hash
JOIN takt_benchmark b ON b.suite_hash = m.suite_hash AND b.benchmark_position = m.benchmark_position
WHERE b.name = 'nbody' AND m.kind = 'value' AND s.name = 'baseline'
GROUP BY s.hash, s.name, s.result_date
ORDER BY s.result_date;
```
