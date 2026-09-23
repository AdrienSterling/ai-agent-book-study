"""The bridge: MCP tool definitions -> Function Calling `tools` parameter.

This answers one question: if the server only hands over its tool list when
asked, how can those definitions be in the "static prefix"?

Because the asking happens ONCE, at startup, BEFORE the first model call.
By the time you talk to the model you already hold the whole catalogue.

  "static" does not mean "hardcoded" or "known at compile time".
  "static" means "identical in every request of this conversation".

    python mcp_to_function_calling.py
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

SERVER = Path(__file__).with_name("mcp_server.py")
PYTHON = Path(os.environ.get("AI_AGENT_BOOK", r"D:/AI Coding/ai-agent-book")) / ".venv/Scripts/python.exe"


def rule(t):
    print(f"\n{'=' * 78}\n  {t}\n{'=' * 78}")


# --------------------------------------------------------------------------
# T0 - STARTUP. Everything in this block runs once, before any model call.
# --------------------------------------------------------------------------
rule("T0  STARTUP - connect to every MCP server and cache its catalogue")

proc = subprocess.Popen(
    [str(PYTHON if PYTHON.exists() else sys.executable), str(SERVER)],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    text=True, encoding="utf-8", bufsize=1,
)
_id = 0


def rpc(method, params=None, notify=False):
    global _id
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        _id += 1
        msg["id"] = _id
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    return None if notify else json.loads(proc.stdout.readline())


print("  [T0.1] spawn server subprocess        (transport)")
print("  [T0.2] initialize                     (protocol handshake)")
rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "bridge", "version": "0.1"}})
rpc("notifications/initialized", {}, notify=True)

print("  [T0.3] tools/list                     <- THE ASKING HAPPENS HERE")
mcp_tools = rpc("tools/list", {})["result"]["tools"]
print(f"         got {len(mcp_tools)} tool definitions, now held in memory")
print("\n  Nothing above involved a model. Not one token was spent.")

# --------------------------------------------------------------------------
# Format conversion: MCP shape -> OpenAI Function Calling shape
# --------------------------------------------------------------------------
rule("T0.4  CONVERT - same JSON Schema, different envelope")


def mcp_to_openai(t):
    return {
        "type": "function",
        "function": {
            "name": t["name"],
            "description": t.get("description", ""),
            "parameters": t["inputSchema"],   # <- copied verbatim, no translation
        },
    }


openai_tools = [mcp_to_openai(t) for t in mcp_tools]

t0 = mcp_tools[0]
print("  MCP form:                          OpenAI form:")
print(f"    name        : {t0['name']:<20}   function.name")
print(f"    description : (docstring)            function.description")
print(f"    inputSchema : (JSON Schema)          function.parameters   <- SAME OBJECT")
print(f"\n  The schema is copied verbatim. The only work is re-wrapping.")
print(f"  This whole function is the entire 'MCP -> Function Calling' bridge:\n")
for line in ["def mcp_to_openai(t):", "    return {'type': 'function', 'function': {",
             "        'name': t['name'],", "        'description': t.get('description', ''),",
             "        'parameters': t['inputSchema'],   # verbatim", "    }}"]:
    print(f"      {line}")

# --------------------------------------------------------------------------
# T1, T2, T3 - the conversation. The tools array never changes.
# --------------------------------------------------------------------------
rule("T1..Tn  CONVERSATION - the same bytes go out every single turn")

blob = json.dumps(openai_tools, sort_keys=True)
digest = hashlib.sha256(blob.encode()).hexdigest()[:16]

messages = [{"role": "user", "content": "..."}]
for turn in range(1, 4):
    messages.append({"role": "assistant", "content": f"(turn {turn} reply)"})
    payload = {"model": "kimi-k2.6", "messages": messages, "tools": openai_tools}
    tools_digest = hashlib.sha256(json.dumps(payload["tools"], sort_keys=True).encode()).hexdigest()[:16]
    print(f"  turn {turn}: messages={len(payload['messages'])} (growing)   "
          f"tools sha256={tools_digest} ({len(blob)} bytes)")

print(f"\n  messages grows every turn -> that is the TRAJECTORY")
print(f"  tools is byte-identical every turn -> that is the STATIC PREFIX")
print(f"  It is static because nobody changed it after T0, not because it was")
print(f"  known before the program started.")

proc.stdin.close()
proc.wait(timeout=5)

rule("AND WHEN YOU *CANNOT* KNOW BEFOREHAND")
print("""  Your objection is exactly right for one real case: active tool discovery.
  There the agent meets a capability gap mid-task and a new schema has to
  arrive AFTER the conversation already started.

  Putting it into the prefix would invalidate the whole prefix cache - every
  earlier turn would have to be recomputed. So the fix is the opposite:

      append the new schema to the END of the trajectory,
      leave the prefix untouched,
      and it stays pinned there, hitting cache as ordinary history.

  So both answers are true, and the timing decides which:
      known at startup      -> static prefix   (tools parameter)
      discovered mid-task   -> trajectory      (appended, then pinned)""")
