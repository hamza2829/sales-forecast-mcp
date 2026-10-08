"""Creates a small SQLite database with SYNTHETIC monthly sales (not real company data)."""
import sqlite3
import sys
from pathlib import Path

import numpy as np

PRODUCTS = {  # name: (base units per month, yearly growth, seasonality strength)
    "Laptop Pro": (120, 0.10, 0.15),
    "Office Chair": (80, 0.02, 0.05),
    "Standing Desk": (60, 0.20, 0.10),
    "Monitor 27": (150, 0.05, 0.20),
    "USB Dock": (200, -0.05, 0.08),
}


def create_db(path, months=36, seed=42):
    rng = np.random.default_rng(seed)  # fixed seed: same data every run
    path = Path(path)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE sales (product TEXT, month TEXT, units INTEGER, PRIMARY KEY (product, month))")
    for name, (base, growth, season) in PRODUCTS.items():
        for m in range(months):
            year, month = 2023 + m // 12, m % 12 + 1
            trend = base * (1 + growth * m / 12)
            seasonal = 1 + season * np.sin(2 * np.pi * (month - 1) / 12)  # yearly wave
            units = max(int(trend * seasonal + rng.normal(0, base * 0.05)), 0)
            con.execute("INSERT INTO sales VALUES (?, ?, ?)", (name, f"{year}-{month:02d}", units))
    con.commit()
    con.close()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "sales.db"
    create_db(target)
    print("created", target)
