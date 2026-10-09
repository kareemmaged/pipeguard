"""PipeGuard checks. Every check returns a Result: pass | warn | fail | skip."""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pandas.api import types as pt

PASS, WARN, FAIL, SKIP = "pass", "warn", "fail", "skip"


@dataclass
class Result:
    name: str
    status: str
    summary: str
    details: list = field(default_factory=list)


# ---------- helpers ----------
def load(path):
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".parquet":
        return pd.read_parquet(p)
    if ext in (".json", ".jsonl"):
        return pd.read_json(p, lines=(ext == ".jsonl"))
    return pd.read_csv(p)


def kind(s: pd.Series) -> str:
    if pt.is_bool_dtype(s):
        return "boolean"
    if pt.is_integer_dtype(s):
        return "integer"
    if pt.is_float_dtype(s):
        v = s.dropna()
        return "integer" if len(v) and (v % 1 == 0).all() else "float"
    if pt.is_datetime64_any_dtype(s):
        return "datetime"
    return "string"


DATE_NAME = re.compile(r"(date|_at|time|timestamp)$", re.I)


def detect_date_columns(df: pd.DataFrame):
    return [
        c for c in df.columns
        if DATE_NAME.search(str(c))
        and (pt.is_datetime64_any_dtype(df[c]) or not pt.is_numeric_dtype(df[c]))
    ]


def _parse(s, fmt=None, utc=False):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return pd.to_datetime(s, errors="coerce", format=fmt or "mixed", utc=utc)


# ---------- the 8 checks ----------
def check_schema(df, cfg):
    name = "Schema validation"
    expected = cfg.get("schema")
    if not expected:
        return Result(name, SKIP, "No schema in config. Run `pipeguard init data.csv` to generate one.")
    problems = []
    for col, dtype in expected.items():
        if col not in df.columns:
            problems.append(f"Missing column: {col}")
        elif dtype != "any" and kind(df[col]) != dtype:
            problems.append(f"{col}: expected {dtype}, got {kind(df[col])}")
    extra = [c for c in df.columns if c not in expected]
    if extra:
        problems.append(f"Unexpected columns: {', '.join(map(str, extra))}")
    if problems:
        return Result(name, FAIL, f"{len(problems)} schema problem(s)", problems)
    return Result(name, PASS, f"All {len(expected)} columns match")


def check_nulls(df, cfg):
    name = "Null checks"
    c = cfg.get("nulls", {})
    default, per = c.get("max_pct", 5.0), c.get("columns", {})
    bad = []
    for col, pct in (df.isna().mean() * 100).items():
        limit = per.get(col, default)
        if pct > limit:
            bad.append(f"{col}: {pct:.1f}% null (limit {limit}%)")
    if bad:
        return Result(name, FAIL, f"{len(bad)} column(s) over null limit", bad)
    return Result(name, PASS, f"No column above null limit ({default}% default)")


def check_duplicates(df, cfg):
    name = "Duplicate detection"
    keys = cfg.get("duplicates", {}).get("keys") or None
    missing = [k for k in (keys or []) if k not in df.columns]
    if missing:
        return Result(name, FAIL, f"Key column(s) not found: {', '.join(missing)}")
    mask = df.duplicated(subset=keys, keep=False)
    extra = int(df.duplicated(subset=keys).sum())
    if not extra:
        return Result(name, PASS, f"No duplicates ({'on ' + ', '.join(keys) if keys else 'full rows'})")
    if keys:
        sample = df.loc[mask, keys].drop_duplicates().head(5).to_dict("records")
        details = [f"Duplicated key: {r}" for r in sample]
    else:
        details = [f"Duplicate row indexes (0-based): {', '.join(map(str, df.index[mask][:10]))}"]
    # duplicate primary keys are a hard failure; full-row duplicates are a warning
    return Result(name, FAIL if keys else WARN, f"{extra} duplicate row(s)", details)


def check_outliers(df, cfg):
    name = "Outlier detection"
    c = cfg.get("outliers", {})
    k, limit = c.get("iqr_k", 1.5), c.get("max_pct", 1.0)
    flagged, scanned = [], 0
    for col in df.select_dtypes("number").columns:
        s = df[col].dropna()
        if len(s) < 8:
            continue
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo, hi = q1 - k * iqr, q3 + k * iqr
        n = int(((s < lo) | (s > hi)).sum())
        scanned += 1
        pct = n / len(s) * 100
        if pct > limit:
            flagged.append(f"{col}: {n} outlier(s) ({pct:.1f}%), expected range [{lo:.2f}, {hi:.2f}]")
    if not scanned:
        return Result(name, SKIP, "No numeric columns with enough data")
    if flagged:
        return Result(name, WARN, f"{len(flagged)} column(s) with outliers", flagged)
    return Result(name, PASS, f"{scanned} numeric column(s) scanned, none above {limit}%")


def check_dates(df, cfg):
    name = "Invalid date detection"
    c = cfg.get("dates", {})
    cols = c.get("columns") or detect_date_columns(df)
    if not cols:
        return Result(name, SKIP, "No date columns found (set dates.columns in config)")
    bad = []
    for col in cols:
        if col not in df.columns:
            bad.append(f"{col}: column not found")
            continue
        s = df[col]
        n = int((s.notna() & _parse(s, c.get("format")).isna()).sum())
        if n:
            examples = s[s.notna() & _parse(s, c.get("format")).isna()].head(3).tolist()
            bad.append(f"{col}: {n} unparseable value(s), e.g. {examples}")
    if bad:
        return Result(name, FAIL, f"{len(bad)} date column(s) with invalid values", bad)
    return Result(name, PASS, f"{len(cols)} date column(s) valid: {', '.join(cols)}")


def check_referential(df, cfg, base_dir="."):
    name = "Referential integrity"
    fks = cfg.get("foreign_keys")
    if not fks:
        return Result(name, SKIP, "No foreign_keys in config")
    bad = []
    for fk in fks:
        if not isinstance(fk, dict) or not {"column", "ref_file", "ref_column"} <= set(fk):
            return Result(name, FAIL, "Invalid foreign_keys entry: each needs column, ref_file, ref_column")
        col, ref_file, ref_col = fk["column"], fk["ref_file"], fk["ref_column"]
        path = Path(ref_file)
        if not path.is_absolute() and (Path(base_dir) / path).exists():
            path = Path(base_dir) / path
        ref = load(path)
        left, right = df[col].dropna(), ref[ref_col].dropna()
        if pt.is_numeric_dtype(left) and pt.is_numeric_dtype(right):
            left, right = left.astype(float), right.astype(float)
        else:
            left, right = left.astype(str), right.astype(str)
        orphans = left[~left.isin(set(right))]
        if len(orphans):
            bad.append(f"{col} -> {ref_file}.{ref_col}: {len(orphans)} orphan row(s), e.g. {orphans.head(3).tolist()}")
    if bad:
        return Result(name, FAIL, f"{len(bad)} broken relationship(s)", bad)
    return Result(name, PASS, f"{len(fks)} foreign key(s) intact")


def check_row_count(df, cfg, prev_rows=None):
    name = "Row count comparison"
    c = cfg.get("row_count", {})
    n, problems = len(df), []
    if c.get("min_rows") and n < c["min_rows"]:
        problems.append(f"{n} rows, below min_rows={c['min_rows']}")
    base = c.get("baseline_rows") or prev_rows
    tol = c.get("tolerance_pct", 10)
    if base:
        change = (n - base) / base * 100
        if abs(change) > tol:
            problems.append(f"{n} rows vs baseline {base} ({change:+.1f}%, tolerance ±{tol}%)")
        elif not problems:
            return Result(name, PASS, f"{n} rows vs baseline {base} ({change:+.1f}%)")
    elif not problems:
        return Result(name, SKIP, f"{n} rows. No baseline yet; this run becomes the baseline for next time")
    return Result(name, FAIL, "Row count out of bounds", problems)


def check_freshness(df, cfg, file_path=None):
    name = "Data freshness"
    c = cfg.get("freshness")
    if not c:
        return Result(name, SKIP, "No freshness config (set freshness.column and max_age_hours)")
    col, max_h = c.get("column"), c.get("max_age_hours", 24)
    if col:
        if col not in df.columns:
            return Result(name, FAIL, f"Freshness column not found: {col}")
        ts = _parse(df[col], c.get("format"), utc=True).max()
        if pd.isna(ts):
            return Result(name, FAIL, f"No valid timestamps in {col}")
        latest, src = ts.to_pydatetime(), col
    elif file_path:
        latest, src = datetime.fromtimestamp(Path(file_path).stat().st_mtime, timezone.utc), "file modified time"
    else:
        return Result(name, SKIP, "Nothing to measure freshness from")
    age = (datetime.now(timezone.utc) - latest).total_seconds() / 3600
    msg = f"Latest {src}: {latest:%Y-%m-%d %H:%M} UTC ({age:.1f}h old, limit {max_h}h)"
    return Result(name, FAIL if age > max_h else PASS, msg)


# ---------- runner ----------
def run_all(df, cfg, *, prev_rows=None, file_path=None, base_dir="."):
    jobs = [
        ("Schema validation", lambda: check_schema(df, cfg)),
        ("Null checks", lambda: check_nulls(df, cfg)),
        ("Duplicate detection", lambda: check_duplicates(df, cfg)),
        ("Outlier detection", lambda: check_outliers(df, cfg)),
        ("Invalid date detection", lambda: check_dates(df, cfg)),
        ("Referential integrity", lambda: check_referential(df, cfg, base_dir)),
        ("Row count comparison", lambda: check_row_count(df, cfg, prev_rows)),
        ("Data freshness", lambda: check_freshness(df, cfg, file_path)),
    ]
    results = []
    for name, fn in jobs:
        try:
            results.append(fn())
        except Exception as e:  # a broken check must not kill the run
            results.append(Result(name, FAIL, f"Check crashed: {type(e).__name__}: {e}"))
    return results
