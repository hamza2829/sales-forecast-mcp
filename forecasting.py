"""Sales analysis functions. No MCP code in here, so they are easy to test and explain."""
import sqlite3
import warnings

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


def connect_readonly(path):
    """Open the database read only, so a tool can never change the data."""
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def list_products(con):
    return [r[0] for r in con.execute("SELECT DISTINCT product FROM sales ORDER BY product")]


def get_series(con, product):
    """Monthly units for one product as a pandas Series indexed by month."""
    rows = con.execute("SELECT month, units FROM sales WHERE product = ? ORDER BY month", (product,)).fetchall()
    if not rows:
        raise ValueError(f"Unknown product: {product}. Use list_products to see valid names.")
    return pd.Series([u for _, u in rows], index=pd.PeriodIndex([m for m, _ in rows], freq="M"), dtype=float)


def top_products(con, last_months=12, n=3):
    """Products with the most units in the last N months."""
    last_months = max(1, min(int(last_months), 120))
    n = max(1, min(int(n), 50))
    out = []
    for p in list_products(con):
        out.append({"product": p, "units": int(get_series(con, p).tail(last_months).sum())})
    return sorted(out, key=lambda r: r["units"], reverse=True)[:n]


def forecast(series, months_ahead=3, order=(1, 1, 1)):
    """ARIMA forecast. order = (p, d, q): autoregression, differencing, moving average."""
    months_ahead = max(1, min(int(months_ahead), 24))
    if len(series) < 12:
        raise ValueError("Need at least 12 months of history for a forecast")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # statsmodels is noisy on small data
        fit = ARIMA(series, order=order).fit()
        result = fit.get_forecast(months_ahead)
    mean = result.predicted_mean
    ci = result.conf_int(alpha=0.2)  # 80 percent interval
    return [
        {"month": str(period), "forecast": round(float(mean.iloc[i])), "low": round(float(ci.iloc[i, 0])), "high": round(float(ci.iloc[i, 1]))}
        for i, period in enumerate(mean.index)
    ]


def detect_anomalies(series, threshold=2.5):
    """Months where sales differ from the previous month by more than `threshold` standard deviations."""
    change = series.diff().dropna()
    std = change.std()
    if std == 0 or pd.isna(std):
        return []
    z = (change - change.mean()) / std
    return [
        {"month": str(m), "units": int(series[m]), "change": int(change[m]), "z_score": round(float(z[m]), 2)}
        for m in z.index if abs(z[m]) > threshold
    ]
