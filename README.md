[Русский](README.ru.md)

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/ashm-dev/takt/main/docs/assets/logo-dark.png">
    <img src="https://raw.githubusercontent.com/ashm-dev/takt/main/docs/assets/logo.png" alt="takt" width="400">
  </picture>
</p>

# takt

takt runs pyperformance benchmarks or your own pyperf scripts.
It writes every result to one or more SQL databases at once.
It then compares results from these databases and from result files.

## Installation

SQLite only:

```bash
pip install takt-py
```

With MariaDB support:

```bash
pip install "takt-py[mariadb]"
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

The full documentation is at [ashm-dev.github.io/takt](https://ashm-dev.github.io/takt/). Its sources are in the `docs` directory. To read it locally:

```bash
poetry run mkdocs serve
```

## Development

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

A local build with `TAKT_MYPYC=1 poetry build` copies compiled `.so` files into `src/takt`.
Python loads them instead of the `.py` files, so your later edits have no effect and `pytest` stops with an error.
Remove them:

```bash
find src/takt -name '*.so' -delete
```

## Author

Shamil Abdulaev, Python developer, CPython and glibc contributor: [ashm-dev.github.io](https://ashm-dev.github.io).
