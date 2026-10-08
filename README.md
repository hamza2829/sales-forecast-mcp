# sales-forecast-mcp

A small MCP (Model Context Protocol) server in Python that gives AI agents safe, read only access to sales data and ARIMA forecasts.

I built it as a compact example of wrapping existing analysis code (SQL queries and an ARIMA model, like the ones I used in my ERP project) as tools that an AI agent can discover and call. The data is synthetic demo data.

## Tools

| Tool | What it does |
|---|---|
| `list_products` | Lists all product names |
| `get_sales_history` | Monthly units for one product |
| `top_products` | Best selling products over the last N months |
| `forecast_sales` | ARIMA(1,1,1) forecast with an 80 percent range |
| `find_anomalies` | Months with an unusually large jump or drop |

## Design

- `forecasting.py` has the analysis logic with no MCP code, so it is easy to test.
- `server.py` wraps those functions as MCP tools using `MCPServer`. Docstrings and type hints become the tool descriptions and input schemas that the model reads.
- The database is opened **read only**, so a tool can never change data. Inputs are limited (for example the forecast horizon), and an unknown product returns a clear error that the model can recover from.
- `seed_data.py` creates the synthetic SQLite database (fixed random seed, so it is the same every run).
- `tests/` has pytest unit tests. `try_client.py` runs a full round trip through a real MCP client over stdio.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                      # unit tests
python try_client.py        # calls every tool through a real MCP client
```

## Use it with Claude Code

```bash
claude mcp add sales-forecast -- python /full/path/to/server.py
```

Then ask: "Which three products sold best last year, and what do you expect for Laptop Pro in the next three months?"

## Limits and next steps

- ARIMA order is fixed at (1,1,1). A next step is picking the order automatically and comparing models.
- Only monthly data. Weekly data or seasonal ARIMA (SARIMA) would be a good extension.
- Real data would need a proper database and access control.
