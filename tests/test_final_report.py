import json

import numpy as np
import pandas as pd

from serein.eval import final_report


def _predictions(smokecast_error: float, seed: int = 0) -> pd.DataFrame:
    """Two seasons of synthetic site-days; SmokeCast misses by a fixed amount, NOAA by 5."""
    rng = np.random.default_rng(seed)
    dates = list(pd.date_range("2024-07-01", periods=30).date) + list(
        pd.date_range("2025-07-01", periods=30).date
    )
    rows = []
    for d in dates:
        for site in range(5):
            row = {"issue_date": d, "point_id": f"s{site}", "hms_prev": 0}
            for lead in range(4):
                y = 10 + rng.normal(0, 3)
                row[f"y_L{lead}"] = y
                row[f"smokecast_L{lead}"] = y + rng.choice([-1, 1]) * smokecast_error
                row[f"noaa_best_L{lead}"] = y + rng.choice([-1, 1]) * 5.0
                row[f"persistence_L{lead}"] = y + 7.0
            rows.append(row)
    return pd.DataFrame(rows)


def test_pass_needs_both_primary_leads_clearly_better():
    good = final_report.primary_table(_predictions(1.0), n_boot=200)
    assert final_report.verdict(good) == "PASS"
    tie = final_report.primary_table(_predictions(5.0), n_boot=200)
    assert final_report.verdict(tie) == "FAIL"


def test_one_missing_primary_lead_is_not_scoreable():
    pred = _predictions(1.0)
    pred["noaa_best_L2"] = np.nan
    table = final_report.primary_table(pred, n_boot=200)
    assert final_report.verdict(table).startswith("NOT SCOREABLE")


def test_year_split_covers_each_season_separately():
    years = final_report.by_year(_predictions(1.0), n_boot=100)
    assert sorted(years["year"].unique()) == [2024, 2025]
    assert (years.groupby("year")["n"].sum() == 30 * 5 * 4).all()


def test_competitors_keep_their_own_row_counts():
    pred = _predictions(1.0)
    pred.loc[:9, "persistence_L1"] = np.nan
    comp = final_report.competitor_table(pred).set_index(["lead", "model"])
    assert comp.loc[(1, "persistence"), "n"] == len(pred) - 10
    assert comp.loc[(1, "smokecast"), "n"] == len(pred)
    assert comp.loc[(1, "persistence"), "rmse"] == 7.0


def test_summary_files_record_hashes_of_what_was_scored(tmp_path):
    run = tmp_path / "west_us_final"
    run.mkdir()
    _predictions(1.0).to_parquet(run / "predictions.parquet", index=False)
    (run / "FINAL_RUN_LOCK.json").write_text("{}")
    table = tmp_path / "table_test.parquet"
    table.write_bytes(b"table bytes")
    text = final_report.summarize(run, table, n_boot=100)
    assert "FINAL test" in text and "PASS" in text
    saved = json.loads((run / "final_hashes.json").read_text())
    assert saved["table:table_test.parquet"] == final_report.sha256(table)
    assert saved["predictions.parquet"] == final_report.sha256(run / "predictions.parquet")
    assert (run / "final_summary.md").exists()
