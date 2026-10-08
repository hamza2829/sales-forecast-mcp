import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import forecasting as fc
import seed_data


@pytest.fixture
def con(tmp_path):
    db = tmp_path / "test.db"
    seed_data.create_db(db)
    return fc.connect_readonly(db)


def test_products_and_history(con):
    assert "Laptop Pro" in fc.list_products(con)
    series = fc.get_series(con, "Laptop Pro")
    assert len(series) == 36 and series.index[0] == pd.Period("2023-01")


def test_unknown_product_gives_clear_error(con):
    with pytest.raises(ValueError, match="Unknown product"):
        fc.get_series(con, "Nope")


def test_database_is_read_only(con):
    import sqlite3
    with pytest.raises(sqlite3.OperationalError):
        con.execute("DELETE FROM sales")


def test_top_products_sorted(con):
    top = fc.top_products(con, 12, 3)
    assert len(top) == 3 and top[0]["units"] >= top[1]["units"] >= top[2]["units"]


def test_forecast_shape_and_range(con):
    out = fc.forecast(fc.get_series(con, "Standing Desk"), 4)
    assert [r["month"] for r in out][0] == "2026-01" and len(out) == 4
    assert all(r["low"] <= r["forecast"] <= r["high"] for r in out)


def test_forecast_needs_history():
    with pytest.raises(ValueError):
        fc.forecast(pd.Series([1.0] * 5, index=pd.period_range("2024-01", periods=5, freq="M")))


def test_detect_anomalies_finds_spike():
    s = pd.Series([100.0] * 11 + [400.0] + [100.0] * 11, index=pd.period_range("2024-01", periods=23, freq="M"))
    months = [a["month"] for a in fc.detect_anomalies(s)]
    assert "2024-12" in months
