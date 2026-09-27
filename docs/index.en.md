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

takt needs Python 3.14 or newer.

## Quick start

Run the `nbody` benchmark and store the result in a SQLite file under the name `baseline <today's UTC date>`:

```bash
takt run -b nbody --fast --db sqlite:///bench.db --name "baseline {date}"
```

Store a result file you already have, for example a run of a patched Python, under the name `patched`:

```bash
takt import result.json --db sqlite:///bench.db --name patched
```

Compare the two runs by name:

```bash
takt compare "baseline 2026-09-25" patched --db sqlite:///bench.db
```

## Compatibility

| takt | Python | pyperf | pyperformance |
|---|---|---|---|
| 0.1.0 | >=3.14 | >=2.10.0,<2.11 | >=1.14.0,<1.15 |

## Next steps

- [Configuration](configuration.md): target databases, `takt.toml`, environment variables and run names.
- [Commands](commands.md): `takt run`, `takt import`, `takt compare` and exit codes.
- [Data model](data-model.md): the tables takt creates, for your own SQL queries.
- [API](api.md): the same commands as a Python library.

## Author

Shamil Abdulaev, Python developer, CPython and glibc contributor: [ashm-dev.github.io](https://ashm-dev.github.io).
