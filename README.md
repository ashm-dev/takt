[Русский](README.ru.md)

# takt

takt runs pyperformance benchmarks or your own pyperf scripts.
It writes every result to one or more SQL databases at once.
It then compares results from these databases and from result files.

## Installation

SQLite only:

```bash
pip install takt
```

With drivers for other databases (in v0: MariaDB):

```bash
pip install "takt[db]"
```

## Quick start

Run the `nbody` benchmark and store the result under the name `baseline <today's UTC date>`:

```bash
takt run -b nbody --fast --db sqlite:///bench.db --name "baseline {date}"
```

Store a result file you already have under the name `patched`:

```bash
takt import result.json --db sqlite:///bench.db --name patched
```

Compare the two runs:

```bash
takt compare "baseline 2026-09-25" patched --db sqlite:///bench.db
```

## Configuration file

Put `takt.toml` in the current directory to avoid repeating `--db`:

```toml
name_template = "nightly {date}"

[targets.local]
url = "sqlite:///bench.db"
```

With this file, `takt run -b nbody --fast` stores the result in `bench.db` under the name `nightly <date>`.

## Compatibility

| takt | Python | pyperf | pyperformance |
|---|---|---|---|
| 0.1.0 | >=3.14 | >=2.10.0,<2.11 | >=1.14.0,<1.15 |

## Documentation

The full documentation is in the `docs` directory. To read it locally:

```bash
poetry run mkdocs serve
```

## Development

```bash
poetry run pytest
```

```bash
poetry run ruff check src tests
```

```bash
poetry run flake8 src
```

```bash
poetry run mypy --strict src
```

```bash
poetry build
```
