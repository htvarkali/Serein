"""Pre-registered summary of a finished backtest run (BACKTEST_PROTOCOL.md section 6).

Reads only the saved outputs of one run folder; it never trains, downloads or
scores anything new. Written before the final test so the final numbers are
summarized by code fixed in advance. It works on any run, so it is tested on
development runs.

    uv run python -m serein.eval.final_report outputs/backtest/west_us_final \
        --table data/processed/west_us/table_test.parquet

Writes ``final_summary.md`` and ``final_hashes.json`` into the run folder:

* primary criterion: per lead, RMSE(SmokeCast) - RMSE(noaa_best) with the day-block
  bootstrap 95% interval; PASS only if the interval is entirely below 0 at lead 1
  AND lead 2;
* the same comparison split by season year (2024 vs. 2025 for the final test);
* row counts and RMSE for every competitor at every lead on its own available rows;
* SHA-256 of the files that reproduce the numbers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from serein.eval.metrics import bootstrap_rmse_diff

COMPETITORS = (
    "noaa_best",
    "aqm_bc",
    "hrrr_smoke",
    "persistence",
    "persistence_morning",
    "climatology",
    "gbm",
    "smokecast_nograph",
)
PRIMARY_LEADS = (1, 2)
HASHED = (
    "predictions.parquet",
    "smokecast.pt",
    "FINAL_RUN_LOCK.json",
    "model.json",
    "conformal.json",
    "report.md",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _leads(pred: pd.DataFrame) -> list[int]:
    return sorted(int(c[3:]) for c in pred.columns if c.startswith("y_L") and c[3:].isdigit())


def _rmse(p: np.ndarray, y: np.ndarray) -> tuple[float, int]:
    ok = np.isfinite(p) & np.isfinite(y)
    if not ok.any():
        return np.nan, 0
    return float(np.sqrt(np.mean((p[ok] - y[ok]) ** 2))), int(ok.sum())


def primary_table(pred: pd.DataFrame, n_boot: int = 1000) -> pd.DataFrame:
    """SmokeCast vs. noaa_best per lead on rows where both and the target exist."""
    dates = pred["issue_date"].to_numpy()
    rows = []
    for lead in _leads(pred):
        y = pred[f"y_L{lead}"].to_numpy(float)
        s = pred[f"smokecast_L{lead}"].to_numpy(float)
        b = pred[f"noaa_best_L{lead}"].to_numpy(float)
        ok = np.isfinite(y) & np.isfinite(s) & np.isfinite(b)
        ci = bootstrap_rmse_diff(s[ok], b[ok], y[ok], dates[ok], n_boot=n_boot) if ok.any() else {}
        rows.append(
            {
                "lead": lead,
                "n": int(ok.sum()),
                "rmse_smokecast": _rmse(s[ok], y[ok])[0],
                "rmse_noaa_best": _rmse(b[ok], y[ok])[0],
                "diff": ci.get("diff", np.nan),
                "ci_lo": ci.get("ci_lo", np.nan),
                "ci_hi": ci.get("ci_hi", np.nan),
            }
        )
    return pd.DataFrame(rows)


def verdict(primary: pd.DataFrame) -> str:
    """PASS only when the interval is entirely below 0 at every primary lead."""
    sub = primary.set_index("lead").reindex(list(PRIMARY_LEADS))
    if sub["ci_hi"].isna().any():
        return "NOT SCOREABLE (a primary lead has no interval)"
    return "PASS" if bool((sub["ci_hi"] < 0).all()) else "FAIL"


def by_year(pred: pd.DataFrame, n_boot: int = 1000) -> pd.DataFrame:
    years = pd.to_datetime(pred["issue_date"]).dt.year
    parts = []
    for year in sorted(years.unique()):
        t = primary_table(pred[years == year].reset_index(drop=True), n_boot=n_boot)
        t.insert(0, "year", int(year))
        parts.append(t)
    return pd.concat(parts, ignore_index=True)


def competitor_table(pred: pd.DataFrame) -> pd.DataFrame:
    """Every competitor on its own available rows (row counts differ by design)."""
    rows = []
    for lead in _leads(pred):
        y = pred[f"y_L{lead}"].to_numpy(float)
        for name in ("smokecast", *COMPETITORS):
            col = f"{name}_L{lead}"
            if col not in pred:
                continue
            r, n = _rmse(pred[col].to_numpy(float), y)
            rows.append({"lead": lead, "model": name, "n": n, "rmse": r})
    return pd.DataFrame(rows)


def hashes(run_dir: Path, table: Path | None) -> dict[str, str]:
    out = {name: sha256(run_dir / name) for name in HASHED if (run_dir / name).exists()}
    if table is not None:
        out[f"table:{table.name}"] = sha256(table)
    return out


def _block(df: pd.DataFrame) -> str:
    """Plain-text table in a fenced block (no extra dependency for markdown tables)."""
    fence = "`" * 3
    return f"{fence}\n{df.round(3).to_string(index=False)}\n{fence}"


def summarize(run_dir: Path, table: Path | None = None, n_boot: int = 1000) -> str:
    pred = pd.read_parquet(run_dir / "predictions.parquet")
    primary = primary_table(pred, n_boot=n_boot)
    years = by_year(pred, n_boot=n_boot)
    comp = competitor_table(pred)
    digest = hashes(run_dir, table)
    lock = run_dir / "FINAL_RUN_LOCK.json"
    kind = "FINAL test" if lock.exists() else "development run (not the final test)"
    lines = [
        f"# Summary of {run_dir.name} ({kind})",
        "",
        f"Primary criterion (BACKTEST_PROTOCOL.md section 6): {verdict(primary)}",
        ("PASS needs the 95% day-bootstrap interval of RMSE(SmokeCast) - RMSE(noaa_best)"
         " entirely below 0 at lead 1 and lead 2."),
        "",
        "## Primary comparison, all rows",
        "",
        _block(primary),
        "",
        "## Split by season year",
        "",
        _block(years),
        "",
        "## Every competitor on its own rows",
        "",
        _block(comp),
        "",
        "## SHA-256 of the files behind these numbers",
        "",
        *[f"- `{k}`: {v}" for k, v in digest.items()],
        "",
    ]
    text = "\n".join(lines)
    (run_dir / "final_summary.md").write_text(text, encoding="utf-8")
    (run_dir / "final_hashes.json").write_text(json.dumps(digest, indent=1), encoding="utf-8")
    return text


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pre-registered summary of a finished backtest run")
    ap.add_argument("run", type=Path, help="run folder in outputs/backtest/")
    ap.add_argument(
        "--table",
        type=Path,
        default=None,
        help="feature table the run scored, to hash (for the final test: table_test)",
    )
    ap.add_argument("--n-boot", type=int, default=1000)
    args = ap.parse_args(argv)
    print(summarize(args.run, args.table, args.n_boot))


if __name__ == "__main__":
    main()
