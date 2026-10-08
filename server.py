"""MCP server that gives AI agents safe, read only access to sales data and ARIMA forecasts.

Run it with:  python server.py
An MCP client (for example Claude Code or Claude Desktop) starts it over stdio.
"""
import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

import forecasting as fc
import seed_data

DB_PATH = Path(os.environ.get("SALES_DB", Path(__file__).parent / "sales.db"))
if not DB_PATH.exists():                 # first start: create the synthetic demo data
    seed_data.create_db(DB_PATH)

mcp = MCPServer(
    "sales-forecast",
    instructions=(
        "Tools for sales analysis. Start with list_products. Use get_sales_history for the raw numbers, "
        "top_products to compare products, forecast_sales for an ARIMA forecast and find_anomalies for unusual months. "
        "All tools are read only. The data is synthetic demo data."
    ),
)


def _con():
    return fc.connect_readonly(DB_PATH)


def _series(con, product):
    try:
        return fc.get_series(con, product)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool()
def list_products() -> list[str]:
    """List all product names in the sales database."""
    with _con() as con:
        return fc.list_products(con)


@mcp.tool()
def get_sales_history(product: str, last_months: int = 12) -> list[dict]:
    """Monthly units sold for one product, newest months last."""
    with _con() as con:
        series = _series(con, product).tail(max(1, min(last_months, 120)))
    return [{"month": str(m), "units": int(u)} for m, u in series.items()]


@mcp.tool()
def top_products(last_months: int = 12, n: int = 3) -> list[dict]:
    """The best selling products over the last N months, ranked by units."""
    with _con() as con:
        return fc.top_products(con, last_months, n)


@mcp.tool()
def forecast_sales(product: str, months_ahead: int = 3) -> list[dict]:
    """ARIMA(1,1,1) forecast of monthly units for one product, with an 80 percent range (low and high)."""
    with _con() as con:
        series = _series(con, product)
    return fc.forecast(series, months_ahead)


@mcp.tool()
def find_anomalies(product: str, threshold: float = 2.5) -> list[dict]:
    """Find months with an unusually large jump or drop compared to the previous month."""
    with _con() as con:
        series = _series(con, product)
    return fc.detect_anomalies(series, threshold)


if __name__ == "__main__":
    mcp.run(transport="stdio")
