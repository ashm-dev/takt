# Configuration

## Target databases

A target is a database where takt stores results.
It is set with a SQLAlchemy URL.

Supported databases:

| Database | URL | v0 |
|---|---|---|
| SQLite | `sqlite:///path.db` | supported, needs nothing extra |
| MariaDB | `mariadb+pymysql://user:password@host:3306/db` | supported, needs `pip install "takt[db]"`; `mariadb://…` also works |
| MySQL | | later |
| PostgreSQL | | later |
| DuckDB | | later |
| ClickHouse | | later |

A URL of any other database is an error, and takt reports it before any benchmark runs.

## Where targets come from

takt takes targets from the first source that is set, in this order:

| Priority | Source | Example |
|---|---|---|
| 1 | Flags `--db`, `--target` | `--db sqlite:///a.db --target maria_ci` |
| 2 | Environment variable `TAKT_DB` | `TAKT_DB="sqlite:///a.db mariadb+pymysql://u:p@h/bench"` |
| 3 | `takt.toml` | see below |

- A source with a higher priority fully replaces the sources below it; they are not merged.
- Without flags and without `TAKT_DB`, takt uses all targets from `takt.toml`.
- `--db` and `--target` in one command add up.
- The same URL is written only once.
- `takt compare` with files only needs no targets at all.

## takt.toml

takt reads `takt.toml` from the current directory.
`--config PATH` points to another file; it does not change the priority above.

```toml
name_template = "nightly {date}"

[targets.local]
url = "sqlite:///bench.db"

[targets.archive]
url = "sqlite:////var/lib/bench/archive.db"

[targets.maria_ci]
url = "mariadb+pymysql://user:password@db-host:3306/bench"
```

- Every `[targets.<name>]` table is one target with one key `url`.
- A target name may contain Latin letters, digits, `_` and `-`.
- `name_template` is the default run name (see the "Run name" section below).
- Any other key is an error.

`--target NAME` picks targets from `takt.toml` by name.
For example, `takt import result.json --target local --target maria_ci` writes to two of the three targets above.

## Environment variables

| Variable | What it does |
|---|---|
| `TAKT_DB` | Default targets: one or more URLs separated by spaces |
| `TAKT_NAME` | Default run name or name template |
| `XDG_CACHE_HOME` | Where the schema version cache lives |

An empty value counts as not set.

## Run name

A run name is a label for a stored result.
You use it later in `takt compare`.

takt takes the name from the first source that is set:

| Priority | Source |
|---|---|
| 1 | `--name` |
| 2 | `TAKT_NAME` |
| 3 | `name_template` in `takt.toml` |

The value is a template. takt replaces these placeholders:

| Placeholder | Value | Example |
|---|---|---|
| `{date}` | UTC date | `2026-09-25` |
| `{datetime}` | UTC date and time | `2026-09-25T13-46-01Z` |
| `{path}` | Result file name without `.json` / `.json.gz` | `takt-20260925T134601Z` |
| `{python_version}` | Python version from the result, otherwise `unknown` | `3.14.0 (64-bit)` |
| `{hostname}` | Host name from the result, otherwise `unknown` | `bench-host` |
| `{hash}` | First 12 characters of the result hash | `3fa2b1c4d5e6` |

- Text without placeholders is used as is: `--name "default 01.01.01"`.
- `{{` and `}}` give literal braces.
- The character `:` is not allowed in a name, because `compare` uses it in `name:N`.
- These are errors too: an empty name, a name longer than 255 characters, an unknown placeholder, `{date:%Y}` and `{date!r}`.
- takt checks the template text before any benchmark runs. This finds an empty name, `:` in the text, an unknown placeholder, `{date:%Y}` and `{date!r}`.
- The 255-character limit, and a `:` that comes from a value such as `{hostname}`, `{python_version}` or `{path}`, are checked only on the final name, after takt has read the result. With `takt run` this happens after the benchmarks: takt writes nothing to the databases, exits with code 2 and keeps the result file. Load that file with `takt import` and another `--name`.
- The name is optional. A run without a name can be found only by its hash.
- The name is not unique: several runs can have the same name.
- Importing the same result again with another name does not change the stored name.

## Schema cache

takt creates and updates its tables in every target on `run` and `import`.
On SQLite a schema update runs in one transaction: if it fails, the database keeps its old tables, and the next `run` or `import` tries the update again.
To skip the schema check next time, takt remembers the schema version of every target in a local cache.

- Location: `$XDG_CACHE_HOME/takt/`, by default `~/.cache/takt/`.
- Content: the schema version for every target. takt stores a hash of the URL, not the URL, so passwords do not get into the cache.
- You can delete the cache at any time. takt then checks the schema of every target again and recreates the cache.
