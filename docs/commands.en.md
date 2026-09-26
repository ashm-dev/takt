# Commands

takt has three commands: `takt run`, `takt import` and `takt compare`.
`takt --version` prints `takt <version>`.

## takt run

`takt run` runs benchmarks and stores the result in every selected database.

### Two modes

takt looks at the first argument after `run`:

- If it is a path to a `.py` file, takt treats it as a pyperf script (a script built on `pyperf.Runner`). takt runs it with the same Python that takt itself runs on.
- Otherwise takt runs `pyperformance run`.

pyperformance mode:

```bash
takt run -b nbody,json_dumps --fast --target local
```

pyperf script mode:

```bash
takt run bench_sort.py --values 5 --db sqlite:///bench.db
```

### Flags

takt reads only its own flags. Every other flag goes to pyperformance or to the pyperf script unchanged, without a `--` separator.

| Flag | Repeatable | What it does |
|---|---|---|
| `--db URL` | yes | SQLAlchemy URL of a target database |
| `--target NAME` | yes | Pick a target from `takt.toml` by its name |
| `--config PATH` | no | Path to `takt.toml` instead of `./takt.toml` |
| `--name TEMPLATE` | no | Run name or name template |

takt flags never clash with pyperformance or pyperf flags.
Flag abbreviations are turned off: `--ta` is not taken for `--target`.
How targets and names are chosen is described on the [Configuration](configuration.md) page.

takt checks the targets and the name template before it starts the benchmarks.
A mistake there stops the command with exit code 2, and no benchmark runs.

### Result file

If you do not pass `-o`/`--output`, the result goes to `./takt-<YYYYmmddTHHMMSSZ>.json`, where the time is in UTC.
takt never deletes the result file.

takt understands `-o FILE`, `-oFILE`, `--output FILE`, `--output=FILE`, a shortened `--out FILE`, and `-o` joined to other short flags, such as `-fo FILE`.
It expands `~` and makes a relative path absolute from the current directory.
Then takt adds `--output <absolute path>` after the other flags of the benchmark command, before the `--` separator if there is one.
pyperformance and pyperf use the last `--output`, so the result goes to the file that takt reads.

The output of pyperformance and pyperf goes to the terminal as is.
After the benchmarks finish, takt brings the schema of every database to the current version and writes the result.

### Output

```text
Result 3fa2b1c4d5e6 (nightly 2026-09-25) from /home/me/takt-20260925T101500Z.json
  local: written
  maria_ci: written
```

The first line shows the first 12 characters of the result hash, the run name and the result file.
A run without a name is shown as `unnamed`.
Then there is one line per target:

| Text | Meaning |
|---|---|
| `written` | The result was written |
| `already loaded as '<name>'` | This database already had the result under this name |
| `already loaded (unnamed)` | This database already had the result without a name |
| `failed: <error>` | Writing to this database failed |
| `rolled back` | The result was written, then removed because another database failed |
| `not attempted` | takt stopped before it got to this database |

### When writing fails

If the result was not written to all targets, takt prints the reason for every target, then this to standard error:

```text
error: result was not written to all targets
Retry without re-running benchmarks: takt import /home/me/takt-20260925T101500Z.json --target local --target maria_ci
```

The command exits with code 1.
The result file stays on disk, so fix the database and run the printed `takt import` command.
The benchmarks do not run again.

### When the benchmarks fail

If pyperformance or the pyperf script exits with an error, takt writes nothing to the databases, prints the error and exits with code 1.
If the failed process still wrote a new result file, takt prints one more line to standard error:

```text
error: benchmark command failed with exit code 1: /usr/bin/python3 -m pyperformance run -b nbody,json_dumps --output /home/me/takt-20260925T101500Z.json
Partial result was written to /home/me/takt-20260925T101500Z.json. Load it without re-running benchmarks: takt import /home/me/takt-20260925T101500Z.json --target local
```

The file may lack the benchmarks that failed.
If the rest is enough for you, run the printed `takt import` command.

## takt import

`takt import` stores a ready pyperf or pyperformance result in every selected database.

```bash
takt import result.json --db sqlite:///bench.db --name patched
```

- The file can be `.json` or gzip-compressed `.json.gz`.
- It accepts the same `--db`, `--target`, `--config` and `--name` flags as `takt run`.
- The output is the same as for `takt run`.
- takt refuses a file that is not a valid pyperf result, for example with a measured value that is NaN or infinite, or with a benchmark name that is not a string. It prints `error: invalid pyperf result <file>: <reason>` and exits with code 1.
- If the file cannot be opened, unpacked or parsed as JSON, takt prints `error: cannot read pyperf result <file>: <reason>` and exits with code 1.

### Result hash

takt identifies a result by its hash: SHA-256 of the JSON content with sorted keys and without spaces.
The file name and the file formatting do not change the hash.
A `.json` file and its `.json.gz` copy have the same hash.

### Importing the same result again

takt checks every database separately.
If a database already has the result, takt skips it and prints `already loaded as '<name>'`.
The stored name does not change, even if you pass another `--name`.
If every database already has the result, the command succeeds and writes nothing.

### All or nothing

takt writes the result either to all selected databases or to none of them:

1. takt opens a transaction in every database and inserts the result.
2. If an insert fails in any database, takt rolls back every transaction and exits with an error.
3. Then takt commits the databases one by one.
4. If a commit fails after other databases were already committed, takt deletes the result from those databases again.

Known limitation: if the takt process is killed while it commits, the result can stay in some of the databases.
Run the same `takt import` again: it skips the databases that already have the result and writes it to the rest.

## takt compare

`takt compare` compares two or more results.
The first operand is the base; every other operand is compared with it.

```bash
takt compare 3fa2b1 "default 01.01.01" "jit+pgo:1" ~/path/to/res.json --target local
```

### Operands

takt checks every operand in this order and takes the first match:

| Operand | What it is |
|---|---|
| `results/a.json`, `~/r.json.gz` | A file on disk, if such a file exists |
| `default` | The run named `default`; if there are several such runs, it is an error with a list of candidates |
| `default:0`, `default:2` | The N-th run named `default`, counted from 0 and sorted by result date |
| `default:3fa2b1` | The run named `default` whose hash starts with these characters (6 or more) |
| `3fa2b1` | The run whose hash starts with these characters (6 or more lowercase hex characters) |

After `:` only digits mean a number; anything else means a hash prefix.
Runs with the same result date are sorted by hash, so the numbers are the same in every database.

If a name matches several runs, takt lists them:

```text
error: operand 'default' is ambiguous, candidates:
  default:0  2026-09-20 10:00:00  3fa2b1c4d5e6
  default:1  2026-09-25 10:00:00  9c01de7a8b2f
```

### Files and databases

- You can mix files and runs from a database in one comparison.
- Runs are read from the first target in the list. Use `--target` to pick another one.
- If all operands are files, takt does not need any database.

### Output

takt prints the table to the terminal.
With `--markdown PATH` it also writes the table to a Markdown file and prints `Markdown table written to <PATH>`.

```bash
takt compare base.json new.json --markdown compare.md
```

Example of the Markdown file:

```markdown
| Benchmark      | base.json | new.json              |
|----------------|:---------:|:---------------------:|
| nbody          | 100 ms    | 90.0 ms: 1.11x faster |
| Geometric mean | (ref)     | 1.04x faster          |

Benchmark hidden because not significant (2): a, b
Ignored benchmarks (1) of new.json: x
```

How to read it:

- The column title is the operand exactly as you typed it.
- The base column shows the mean value.
- Other columns show the mean value and the change against the base: `1.11x faster`, `1.05x slower`, `no change` or `not significant`.
- The `Geometric mean` row appears when the results have more than one benchmark in common and the table shows at least one of them.
- `Benchmark hidden because not significant` lists benchmarks where no difference is significant; they are not shown in the table.
- `Ignored benchmarks … of <operand>` lists benchmarks of that operand that the other operands do not have. Only benchmarks present in all operands are compared.

The numbers and the significance test are the same as in `pyperf compare_to --table`.

## Exit codes

| Code | When |
|---|---|
| 0 | Success, including "everything was already loaded" |
| 1 | Runtime error: database, file, benchmark, or the result was not written to all targets |
| 2 | Wrong arguments or configuration, found before any benchmark runs |
| 130 | Interrupted with Ctrl+C |

Every error is printed to standard error as one line `error: <message>`, without a traceback.
When `takt run` fails to write the result, or a benchmark fails but a result file was still written, takt also prints a `takt import` command that loads this file without re-running benchmarks.
