<a href="https://ibb.co/gFQbNhRv"><img src="https://i.ibb.co/zHCWpD48/Screenshot-2026-10-09-192752.png" alt="Screenshot-2026-10-09-192752" border="0"></a>

# PipeGuard 🛡️

**A lightweight, local-first data quality CLI for data engineers.**

PipeGuard checks CSV, JSON, JSONL, and Parquet files for common data quality issues, prints a concise terminal summary, and generates a standalone HTML report that is easy to review or share.

> Data pipelines can finish successfully while quietly producing incorrect, incomplete, stale, or inconsistent data. PipeGuard helps surface those problems before the data is used downstream.

## Why PipeGuard?

Data quality checks are often written as one-off scripts or discovered only after a dashboard, report, or downstream job looks wrong. This creates debugging work, delays, and a loss of confidence in data. PipeGuard packages common checks into one repeatable command, configurable through a readable YAML file, with an HTML report that makes findings easier to understand.

## What it checks

| Check                  | What it helps catch                                          |
| ---------------------- | ------------------------------------------------------------ |
| Schema validation      | Missing, unexpected, or incorrectly typed columns            |
| Null checks            | Columns whose null rate exceeds a configurable threshold     |
| Duplicate detection    | Duplicate rows or repeated business keys                     |
| Outlier detection      | Numeric values outside an IQR-based range                    |
| Invalid date detection | Date/time values that cannot be parsed                       |
| Referential integrity  | Values in a column that do not exist in a reference file     |
| Row-count comparison   | Unexpected volume changes against a baseline or previous run |
| Data freshness         | Data older than a configured time limit                      |

Checks can return **Passed**, **Warning**, **Failed**, or **Skipped**. A failed check causes `pipeguard check` to return a non-zero exit code, which makes it useful in scripts and CI workflows.

## Quick start

### 1. Requirements

- Python 3.9 or newer
- pip
- For Parquet support, install the optional `pyarrow` dependency

### 2. Install from a local clone

```bash
git clone https://github.com/YOUR_USERNAME/pipeguard.git
cd pipeguard
pip install -e .

cd sample
pipeguard check orders.csv      # runs the 8 checks, saves the run to .pipeguard/last_run.json
pipeguard report --open         # writes pipeguard_report.html and opens it
```

For Parquet files:

```bash
pip install -e ".[parquet]"
```

## Usage

### Generate a starter configuration

```bash
pipeguard init path/to/data.csv --out pipeguard.yml
```

If the output file already exists, PipeGuard protects it from accidental overwrites. Add `--force` only when you want to replace it.

### Run checks

```bash
pipeguard check path/to/data.csv --config pipeguard.yml
```

Compare row count with another file:

```bash
pipeguard check path/to/current.csv --config pipeguard.yml --baseline path/to/previous.csv
```

### Supported input formats

- CSV (`.csv`)
- JSON (`.json`)
- JSON Lines (`.jsonl`)
- Parquet (`.parquet`, with `pyarrow` installed)

### Configuration notes:

- `schema` supports `string`, `integer`, `float`, `boolean`, `datetime`, and `any`.
- `nulls.max_pct` is the default allowed null percentage; `nulls.columns` can override it for specific columns.
- `duplicates.keys` checks uniqueness for the selected key columns. An empty list checks full-row duplicates, which are reported as a warning.
- `outliers` uses the interquartile range (IQR) on numeric columns with enough non-null values. Outliers are warnings, not automatic proof of bad data.
- `foreign_keys` points to another CSV/JSON/JSONL/Parquet file and a reference column. Relative paths are resolved from the config file's directory when possible.
- `row_count.tolerance_pct` sets the allowed percentage change from the previous run or supplied baseline. You can also set `min_rows`.
- `freshness` checks the newest parseable timestamp in the selected column against `max_age_hours`.

## Example workflow

```text
Source file → PipeGuard checks → Terminal summary → HTML report
                         └────→ non-zero exit on failed checks
```

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

**Built as a hands-on Data Engineering project** to explore practical data validation, command-line tooling, configuration-driven checks, and readable reporting.
