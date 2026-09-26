# Commands

takt has three commands: `takt run`, `takt import` and `takt compare`.
`takt --version` prints `takt <version>`.

## takt run

`takt run` runs benchmarks and stores the result in every selected database.

### Two modes

takt removes its own flags (see "Flags" below) and looks at the first argument that is left:

- If it ends in `.py` and does not start with `-`, takt treats it as the path to a pyperf script (a script built on `pyperf.Runner`). takt runs it with the same Python that takt itself runs on.
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

takt checks the targets and the text of the name template before it starts the benchmarks.
A mistake there stops the command with exit code 2, and no benchmark runs.
The 255-character limit, and a `:` that comes from a value such as `{hostname}`, are checked only after the benchmarks: see "Run name" on the [Configuration](configuration.md) page.

### Result file

If you do not pass `-o`/`--output`, the result goes to `./takt-<YYYYmmddTHHMMSSZ>.json`, where the time is in UTC.
takt never deletes the result file.

takt understands `-o FILE`, `-oFILE`, `--output FILE`, `--output=FILE`, a shortened `--out FILE`, and `-o` joined to other short flags, such as `-fo FILE`.
It expands `~` and makes a relative path absolute from the current directory.
Then takt adds `--output <absolute path>` after the other flags of the benchmark command, before the `--` separator if there is one.
pyperformance and pyperf use the last `--output`, so the result goes to the file that takt reads.

The folder of the result file must already exist, and takt must be able to write to it.
Without `-o` this folder is the current directory.
takt checks this before any benchmark runs, because pyperformance writes the file only after the last benchmark.
Otherwise the command stops with exit code 2 and prints `error: cannot create result file <file>: folder <folder> does not exist; choose another file with -o`, or the same error with `is not writable`.
takt does not create the folder: a typo in the path would then go unnoticed.

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
| `failed: compensation failed: <error>` | The result was written, but takt could not remove it after another database failed |
| `rolled back` | The result was written, then removed because another database failed |
| `not attempted` | takt stopped before it got to this database |

After `compensation failed` the result stays in that database: see "All or nothing" below.

### When writing fails

If the result was not written to all targets, takt prints the reason for every target, then this to standard error:

```text
error: result was not written to all targets
Retry without re-running benchmarks: takt import /home/me/takt-20260925T101500Z.json --target local --target maria_ci --name 'nightly 2026-09-25'
```

The command exits with code 1.
The result file stays on disk, so fix the database and run the printed `takt import` command.
The benchmarks do not run again.

The printed command passes the run name that this command gave the result, not the name template: with `nightly {date}`, a retry on the next day still stores `nightly 2026-09-25`.
Braces in that name are doubled, so they stay literal text.
If the result has no name, the command has no `--name`.

### When the benchmarks fail

If pyperformance or the pyperf script exits with an error, takt writes nothing to the databases, prints the error and exits with code 1.
If the failed process still wrote a new result file, takt prints one more line to standard error:

```text
error: benchmark command failed with exit code 1: /usr/bin/python3 -m pyperformance run -b nbody,json_dumps --output /home/me/takt-20260925T101500Z.json
Partial result was written to /home/me/takt-20260925T101500Z.json. Load it without re-running benchmarks: takt import /home/me/takt-20260925T101500Z.json --target local
```

The file may lack the benchmarks that failed.
If the rest is enough for you, run the printed `takt import` command.

### After Ctrl+C

If you press Ctrl+C while the benchmarks run, takt writes nothing to the databases and exits with code 130.
A pyperf script writes each finished benchmark to the result file right away, so after Ctrl+C the file can already hold them.
If a new result file is on disk, takt prints only the `Partial result was written to …` line, without an `error:` line.
pyperformance writes its file only at the end, so after Ctrl+C there is usually no file and no such line.

If you press Ctrl+C after the benchmarks, while takt writes the result to the databases, for example while it waits for a locked database, the result file is complete.
takt then prints this line to standard error and exits with code 130:

```text
Result was written to /home/me/takt-20260925T101500Z.json. Load it without re-running benchmarks: takt import /home/me/takt-20260925T101500Z.json --target local --name 'nightly 2026-09-25'
```

Like the retry command above, it passes the run name that this command gave the result.
If Ctrl+C came while takt committed, some databases can already have the result; the printed command skips them (see "All or nothing" below).

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

In these cases the result still stays in some of the databases:

- takt could not delete the result in step 4. Such a database shows `failed: compensation failed: <error>`.
- The takt process was killed, or interrupted with Ctrl+C, while it committed. takt then prints no report; after Ctrl+C it exits with code 130, and `takt run` also prints the `Result was written to …` line.

After `compensation failed`, the `Result` line of the failed command shows the first 12 characters of the result hash and the name stored in that database.
After a stop there is no such line.
The stopped command stored the result with the same `loaded_at` time in every database it reached, so in those databases this query shows it as the newest result:

```sql
SELECT hash, name, loaded_at FROM takt_suite ORDER BY loaded_at DESC LIMIT 1;
```

To have the result in every database, run `takt import` for the result file again: it skips the databases that already have the result and writes it to the rest.
If the name template has `{date}` or `{datetime}`, takt fills them in with the new time, so the rest can get another name.
To give the rest the same name, pass the stored name with `--name`; the command that `takt run` prints after `compensation failed` or Ctrl+C already does this.

To remove the result instead, run these queries, in this order, only in the databases where the failed command left it: the ones with `compensation failed`, or, after a stop, the ones where the query above shows it with the `loaded_at` of that command.
Do not run them in a database that shows `already loaded`: it had the result before this command.
Child tables go first: MariaDB does not delete a row while other rows refer to it.
Put the first 12 characters of the result hash in place of `3fa2b1c4d5e6`.

```sql
DELETE FROM takt_measurement WHERE suite_hash LIKE '3fa2b1c4d5e6%';
DELETE FROM takt_run_metadata WHERE suite_hash LIKE '3fa2b1c4d5e6%';
DELETE FROM takt_worker_run WHERE suite_hash LIKE '3fa2b1c4d5e6%';
DELETE FROM takt_benchmark WHERE suite_hash LIKE '3fa2b1c4d5e6%';
DELETE FROM takt_suite WHERE hash LIKE '3fa2b1c4d5e6%';
DELETE FROM takt_loaded_hash WHERE hash LIKE '3fa2b1c4d5e6%';
```

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
An operand that fits none of these forms is an error with exit code 1, for example an empty operand, `default:`, `:1`, `a:b:c` or `default:XYZ`.
Runs with the same result date are sorted by hash, so the numbers are the same in every database.
Runs without a result date come last; the list of candidates shows them with `unknown date`.

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
- If an operand is not a file and no target is configured, takt prints `error: operand '<operand>' is not a file and no database target is configured` and exits with code 2. An operand that fits no form still gives exit code 1: takt checks the form of every operand first.

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
- `Ignored benchmarks … of <operand>` lists benchmarks of that operand that are not compared. Only benchmarks that every operand has with measured values are compared: a benchmark that some operand lacks, or has only warmup values for, is ignored.

If no benchmark is left to compare, takt prints no table: it prints `error: benchmark suites have no benchmark in common` and exits with code 1.
This also happens when the results have benchmarks with the same names, but some operand has only warmup values for each of them.

The numbers and the significance test are the same as in `pyperf compare_to --table`.

## Exit codes

| Code | When |
|---|---|
| 0 | Success, including "everything was already loaded" |
| 1 | Runtime error: database, file, benchmark, the result was not written to all targets, a `compare` operand that fits no form, was not found or is ambiguous, or `compare` results with no benchmark in common |
| 2 | Wrong arguments or configuration, found before any benchmark runs, a final run name that breaks the rules, or a `compare` operand that is not a file when no target is configured |
| 130 | Interrupted with Ctrl+C |

A mistake in the command line itself, such as a missing argument or a flag without its value, is reported by argparse.
It prints the usage of the command and then a line like `takt import: error: the following arguments are required: PATH`.
An unknown flag of `takt import` or `takt compare` prints the general usage of `takt` and the line `takt: error: unrecognized arguments: <flags>`.
`takt run` does not reject unknown flags: it passes them to pyperformance or the pyperf script.
`takt run` checks `-o`/`--output` itself: without a file path it prints only the line `error: option -o/--output requires a file path`.
The exit code is 2.

Every other error is printed to standard error as `error: <message>`, without a traceback.
Most messages are one line; an ambiguous operand also lists the candidates below it.
When `takt run` fails to write the result, or a benchmark fails but a result file was still written, takt also prints a `takt import` command that loads this file without re-running benchmarks.
When the final run name breaks the rules after the benchmarks, takt prints the path of the result file: load it with `takt import` and another `--name`.
