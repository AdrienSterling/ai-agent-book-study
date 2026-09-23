"""MCP with NO SDK - the raw bytes on the pipe.

mcp_client_demo.py used the official client, which hides the actual protocol.
This file uses nothing but `subprocess` and `json`, so you can see what MCP
really is:

    newline-delimited JSON-RPC 2.0 messages over the server's stdin/stdout.

That is the entire transport. No sockets, no HTTP, no framing headers - one
JSON object per line, request in on stdin, response out on stdout. Every byte
is printed below, in both directions.

    python mcp_raw.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

SERVER = Path(__file__).with_name("mcp_server.py")
PYTHON = Path(os.environ.get("AI_AGENT_BOOK", r"D:/AI Coding/ai-agent-book")) / ".venv/Scripts/python.exe"

proc = subprocess.Popen(
    [str(PYTHON if PYTHON.exists() else sys.executable), str(SERVER)],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    text=True, encoding="utf-8", bufsize=1,
)

_id = 0


def send(method, params=None, notify=False):
    """Write one JSON-RPC message to the server's stdin. That is all a client does."""
    global _id
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:                      # a request has an id; a notification does not
        _id += 1
        msg["id"] = _id
    line = json.dumps(msg)
    print(f"\n  >>> STDIN  {line}")
    proc.stdin.write(line + "\n")       # <- the newline IS the message delimiter
    proc.stdin.flush()
    if notify:
        return None
    reply = proc.stdout.readline()      # <- one line back = one response
    print(f"  <<< STDOUT {reply.strip()[:300]}{'...' if len(reply.strip()) > 300 else ''}")
    return json.loads(reply)


def rule(t):
    print(f"\n{'=' * 78}\n  {t}\n{'=' * 78}")


rule("1. initialize - client says hello, server answers with its capabilities")
print("  Note the shape: jsonrpc / id / method / params. Plain JSON-RPC 2.0.")
r = send("initialize", {
    "protocolVersion": "2025-06-18",
    "capabilities": {},
    "clientInfo": {"name": "raw-client", "version": "0.1"},
})
info = r["result"]
print(f"\n  server : {info['serverInfo']['name']} v{info['serverInfo']['version']}")
print(f"  agreed protocol version : {info['protocolVersion']}")

rule("2. notifications/initialized - required, and it has NO id")
print("  A notification is fire-and-forget: no id means the server must not reply.")
print("  Skip this and a strict server refuses everything that follows.")
send("notifications/initialized", {}, notify=True)
print("  (nothing read back - that is the point)")

rule("3. tools/list - ask what the server can do")
r = send("tools/list", {})
tools = r["result"]["tools"]
print(f"\n  {len(tools)} tools came back. First one, in full:")
print(json.dumps(tools[0], ensure_ascii=False, indent=2))
print("\n  ^ THIS is what a host copies into the `tools` parameter of a")
print("    Function Calling request. Same JSON Schema, different envelope.")

rule("4. tools/call - actually invoke one")
r = send("tools/call", {
    "name": "convert_currency",
    "arguments": {"amount": 2100000, "from_currency": "EUR", "to_currency": "USD"},
})
content = r["result"]["content"]
print(f"\n  result content blocks: {len(content)}")
for c in content:
    print(f"    type={c['type']}  text={c.get('text')}")

rule("5. an error, to show errors are in-band too")
r = send("tools/call", {
    "name": "convert_currency",
    "arguments": {"amount": 1, "from_currency": "XYZ", "to_currency": "USD"},
})
res = r.get("result", {})
print(f"\n  isError = {res.get('isError')}   <- not a JSON-RPC error, a normal result")
for c in res.get("content", []):
    print(f"    {c.get('text', '')[:160]}")
print("\n  This matters: the tool failing is an OBSERVATION the agent can read")
print("  and recover from, not a transport error that kills the session.")

proc.stdin.close()
proc.wait(timeout=5)

rule("SO WHAT IS MCP, MECHANICALLY?")
print("""  1. Start the server as a subprocess (or open an HTTP connection).
  2. Write JSON-RPC 2.0 objects to its stdin, one per line.
  3. Read JSON-RPC responses from its stdout, one per line.
  4. Four methods carry almost everything:
        initialize                handshake + capability negotiation
        notifications/initialized "ok, go" - no id, no reply
        tools/list                give me your tool definitions
        tools/call                run this one with these arguments

  That is the whole protocol surface you need for tools. `FastMCP` and
  `ClientSession` are conveniences over exactly these lines of JSON.

  And note what never appeared anywhere above: a model. MCP moves tool
  DEFINITIONS and tool RESULTS between your code and a tool provider.
  Handing those definitions to a model, and turning its tool_calls back
  into tools/call, is your code's job - that is Function Calling.""")
