"""A minimal MCP server - the two tools from my own agent, exposed over MCP.

Same two functions as `agent/harness.py`, but instead of being hard-wired into
one agent they are now published through a protocol any MCP client can speak.
That is the whole point of ch.4's "write once, use anywhere".

Run it directly (it speaks stdio and waits for a client):
    python mcp_server.py

Or let the client launch it:
    python mcp_client_demo.py
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-agent-tools")

RATES_TO_USD = {"USD": 1.0, "EUR": 1.087, "GBP": 1.266, "JPY": 0.00669, "CNY": 0.1385}


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount between currencies.

    Use this whenever a figure is not already in the target currency - never
    convert from memory, the rates here are the authoritative ones.
    Supports only USD, EUR, GBP, JPY, CNY; anything else is rejected rather
    than guessed. Example: amount=2100000, from_currency="EUR", to_currency="USD".
    """
    f, t = from_currency.upper(), to_currency.upper()
    if f not in RATES_TO_USD or t not in RATES_TO_USD:
        raise ValueError(f"unsupported currency pair {f}->{t}; supported: {sorted(RATES_TO_USD)}")
    return {"result": round(amount * RATES_TO_USD[f] / RATES_TO_USD[t], 2), "pair": f"{f}->{t}"}


@mcp.tool()
def calculate(expression: str) -> dict:
    """Evaluate an arithmetic expression.

    Use this for every arithmetic step instead of computing mentally.
    Accepts ONLY digits and + - * / ( ) and spaces - no variables, no function
    calls, no comparisons. Example: expression="(2500000 + 2282700) / 4".
    """
    allowed = set("0123456789.+-*/() ")
    if not set(expression) <= allowed:
        raise ValueError("expression contains characters outside the allowed set")
    return {"result": eval(expression, {"__builtins__": {}}, {})}  # constrained above


if __name__ == "__main__":
    mcp.run()
