"""Starts the server over stdio like an AI client would and calls every tool."""
import asyncio, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    params = StdioServerParameters(command=sys.executable, args=["server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Tools:", [t.name for t in (await session.list_tools()).tools])
            calls = [
                ("list_products", {}),
                ("top_products", {"last_months": 12, "n": 3}),
                ("get_sales_history", {"product": "Laptop Pro", "last_months": 3}),
                ("forecast_sales", {"product": "Laptop Pro", "months_ahead": 3}),
                ("find_anomalies", {"product": "Monitor 27"}),
                ("forecast_sales", {"product": "Does Not Exist"}),
            ]
            for name, args in calls:
                result = await session.call_tool(name, args)
                text = " ".join(c.text.replace("\n", "").replace("  ", "") for c in result.content) or "(empty result)"
                if args.get("product") == "Does Not Exist":
                    assert result.is_error and "Unknown product" in text
                else:
                    assert not result.is_error, f"{name} failed: {text}"
                print(f"\n{name}({args}) error={result.is_error}\n{text[:500]}")


asyncio.run(main())
