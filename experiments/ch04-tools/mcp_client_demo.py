"""A minimal MCP client - shows the protocol one step at a time.

It launches an MCP server as a subprocess over stdio (by default the one in
mcp_server.py next to this file), then walks
the three calls every MCP client makes:

    initialize   handshake: who are you, what do you support
    tools/list   the server hands back tool definitions (name + JSON Schema)
    tools/call   invoke one tool and read the result

This is the whole of "MCP is a client-server protocol" made concrete.
Nothing here is specific to a model - the LLM never appears. MCP's job is to
get tool DEFINITIONS to whoever needs them; deciding which to call is the
model's job (ch.1: RL internalises the decision policy, not the execution).

    python mcp_client_demo.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BOOK = Path(os.environ.get("AI_AGENT_BOOK", r"D:/AI Coding/ai-agent-book"))
# Default: my own MCP server (experiments/ch04-tools/mcp_server.py).
# Pass a path to point it at any other MCP server, e.g. the book's perception tools.
SERVER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("mcp_server.py")
PYTHON = BOOK / ".venv" / "Scripts" / "python.exe"


def rule(title):
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")


async def main():
    if not SERVER.exists():
        sys.exit(f"MCP server not found: {SERVER}")

    params = StdioServerParameters(
        command=str(PYTHON if PYTHON.exists() else sys.executable),
        args=[str(SERVER)],
        cwd=str(SERVER.parent),
    )

    rule("1. transport: launching the server as a subprocess over stdio")
    print(f"  command : {params.command}")
    print(f"  args    : {params.args}")
    print("  (the same server could instead be reached over Streamable HTTP;")
    print("   the protocol does not change, only the transport)")

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:

            rule("2. initialize - the handshake")
            info = await session.initialize()
            print(f"  server name    : {info.serverInfo.name}")
            print(f"  server version : {info.serverInfo.version}")
            print(f"  protocol       : {info.protocolVersion}")
            print(f"  capabilities   : {[k for k, v in info.capabilities if v]}")

            rule("3. tools/list - the server hands back its tool definitions")
            tools = (await session.list_tools()).tools
            print(f"  server exposes {len(tools)} tools\n")
            for t in tools[:3]:
                schema = t.inputSchema or {}
                props = list((schema.get("properties") or {}).keys())
                print(f"  - {t.name}")
                print(f"      description : {(t.description or '').strip()[:88]}")
                print(f"      required    : {schema.get('required', [])}")
                print(f"      properties  : {props[:8]}")
            print(f"\n  ... and {len(tools) - 3} more.")
            print("  NOTE: every one of these definitions costs tokens if the host")
            print("  injects them all. This is exactly the 'too many tools' problem")
            print("  from ch.4 - and why hosts move to indexes and tool search.")

            target = next((t.name for t in tools if t.name in ("weather", "convert_currency")), tools[0].name)

            rule(f"4. tools/call - invoking '{target}'")
            args = ({"location": "Paris"} if target == "weather"
                    else {"amount": 2100000, "from_currency": "EUR", "to_currency": "USD"}
                    if target == "convert_currency" else {})
            print(f"  request  : {json.dumps({'name': target, 'arguments': args}, ensure_ascii=False)}")
            result = await session.call_tool(target, args)
            text = "".join(c.text for c in result.content if getattr(c, "type", "") == "text")
            try:
                text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
            except Exception:
                pass
            print("  response :")
            for line in text.splitlines()[:18]:
                print(f"    {line}")

            rule("what just happened")
            print("""  The client never imported the tool's code. It learned the tool existed,
  learned its parameter schema, and invoked it - entirely through the protocol.
  That is the 'write once, use anywhere' claim: this same server works with
  Cursor, Claude Desktop or your own agent, unchanged.

  And the risk that comes with it: those descriptions go straight into the
  model's context. A malicious server can hide instructions in a description
  (tool description poisoning) - which is why ch.4 says to audit descriptions
  as untrusted input and pin server versions.""")


if __name__ == "__main__":
    asyncio.run(main())
