from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import __version__
from .checks import detect_date_columns, kind, load, run_all
from .report import render

STATE_DIR = Path(".pipeguard")
STATE = STATE_DIR / "last_run.json"
ICON = {"pass": "✓", "warn": "!", "fail": "✗", "skip": "–"}
ANSI = {"pass": "32", "warn": "33", "fail": "31", "skip": "90"}


def paint(text, status):
    return f"\033[{ANSI[status]}m{text}\033[0m" if sys.stdout.isatty() else text


def cmd_init(a):
    out = Path(a.out)
    if out.exists() and not a.force:
        sys.exit(f"{out} already exists (use --force to overwrite)")
    df = load(a.file)
    dates = detect_date_columns(df)
    cfg = {
        "schema": {str(c): kind(df[c]) if c not in dates else "string" for c in df.columns},
        "nulls": {"max_pct": 5.0, "columns": {}},
        "duplicates": {"keys": []},
        "outliers": {"iqr_k": 1.5, "max_pct": 1.0},
        "dates": {"columns": dates},
        "foreign_keys": [],
        "row_count": {"tolerance_pct": 10},
    }
    if dates:
        cfg["freshness"] = {"column": dates[0], "max_age_hours": 24}
    out.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
    print(f"Created {out}. Edit it (set duplicates.keys, foreign_keys, thresholds), then run: pipeguard check {a.file}")


def cmd_check(a):
    cfg_path = Path(a.config) if a.config else Path("pipeguard.yml")
    cfg = yaml.safe_load(cfg_path.read_text()) or {} if cfg_path.exists() else {}
    if a.config and not cfg_path.exists():
        sys.exit(f"Config not found: {cfg_path}")

    df = load(a.file)
    resolved = str(Path(a.file).resolve())

    prev_rows = None
    if STATE.exists():
        prev = json.loads(STATE.read_text())
        if prev.get("file") == resolved:
            prev_rows = prev.get("rows")
    if a.baseline:
        cfg.setdefault("row_count", {})["baseline_rows"] = len(load(a.baseline))

    results = run_all(df, cfg, prev_rows=prev_rows, file_path=a.file,
                      base_dir=str(cfg_path.parent) if cfg_path.exists() else ".")

    print(f"\nPipeGuard · {a.file} · {len(df):,} rows × {len(df.columns)} cols\n")
    for r in results:
        print(f"{paint(ICON[r.status], r.status)} {r.name:<24} {r.summary}")
        for d in r.details[:5]:
            print(f"    · {d}")
    counts = {s: sum(r.status == s for r in results) for s in ICON}
    print(f"\n{counts['pass']} passed, {counts['warn']} warnings, {counts['fail']} failed, {counts['skip']} skipped")

    STATE_DIR.mkdir(exist_ok=True)
    STATE.write_text(json.dumps({
        "file": resolved, "name": Path(a.file).name,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": len(df), "columns": len(df.columns),
        "results": [asdict(r) for r in results],
    }, indent=2, default=str))
    print("Run `pipeguard report` for the HTML report.")
    sys.exit(1 if counts["fail"] else 0)  # non-zero exit = CI friendly


def cmd_report(a):
    src = Path(a.input)
    if not src.exists():
        sys.exit("No run found. Run `pipeguard check <file>` first.")
    out = Path(a.out)
    out.write_text(render(json.loads(src.read_text())), encoding="utf-8")
    print(f"Report written to {out.resolve()}")
    if a.open:
        webbrowser.open(out.resolve().as_uri())


def main():
    p = argparse.ArgumentParser(prog="pipeguard", description="Data quality checks with an HTML report")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="generate pipeguard.yml from a data file")
    i.add_argument("file"); i.add_argument("--out", default="pipeguard.yml"); i.add_argument("--force", action="store_true")
    i.set_defaults(fn=cmd_init)

    c = sub.add_parser("check", help="run all checks on a file (csv, parquet, json, jsonl)")
    c.add_argument("file"); c.add_argument("--config"); c.add_argument("--baseline", help="previous file, for row count comparison")
    c.set_defaults(fn=cmd_check)

    r = sub.add_parser("report", help="build an HTML report from the last run")
    r.add_argument("--input", default=str(STATE)); r.add_argument("--out", default="pipeguard_report.html")
    r.add_argument("--open", action="store_true", help="open in browser")
    r.set_defaults(fn=cmd_report)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
