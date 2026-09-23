"""Function Calling, at the wire level - one exchange, four steps, raw JSON.

No framework, no abstraction, no agent loop. Just the four HTTP round-trip
facts that every tool-calling agent is built on:

    1. you send a `tools` parameter alongside the messages
    2. the model replies with `tool_calls` instead of content
    3. you execute it yourself and append a `role: "tool"` message
    4. the model reads that result and answers

Run:
    python function_calling_walkthrough.py
"""

import json
import os
import sys

from openai import OpenAI

MODEL = os.environ.get("AGENT_MODEL", "kimi-k2.6")
KEY = os.environ.get("MOONSHOT_API_KEY")
BASE = os.environ.get("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")

if not KEY:
    sys.exit("MOONSHOT_API_KEY is not set")

client = OpenAI(api_key=KEY, base_url=BASE)


def rule(n, title):
    print(f"\n{'=' * 74}\n  STEP {n}. {title}\n{'=' * 74}")


def show(label, obj):
    print(f"\n  --- {label} ---")
    for line in json.dumps(obj, ensure_ascii=False, indent=2).splitlines():
        print(f"  {line}")


# ---------------------------------------------------------------- the tool
def get_weather(city: str) -> dict:
    """The actual implementation. The model never sees this code."""
    fake = {"Beijing": (28, "Sunny"), "Paris": (14, "Overcast")}
    temp, sky = fake.get(city, (20, "Unknown"))
    return {"city": city, "temp_c": temp, "sky": sky}


TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city. Use this whenever the "
                       "user asks about weather - never answer from memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name in English, e.g. 'Beijing'"},
            },
            "required": ["city"],
        },
    },
}]

messages = [{"role": "user", "content": "What's the weather in Beijing right now?"}]

# ------------------------------------------------------- 1. declare tools
rule(1, "DECLARE - send the tool definitions with the request")
print("  The `tools` parameter is a sibling of `messages`, not part of them.")
print("  A tool the model is not told about does not exist for it.")
show("tools parameter", TOOLS)
show("messages", messages)

# ------------------------------------------------------- 2. model decides
rule(2, "DECIDE - the model returns tool_calls instead of content")
resp = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
choice = resp.choices[0]
assistant = choice.message.model_dump(exclude_none=True)
assistant.pop("annotations", None)

print(f"\n  finish_reason = {choice.finish_reason!r}"
      f"   <- 'tool_calls' means: I am not done, run these for me")
show("assistant message (append this to messages VERBATIM)", assistant)

call = assistant["tool_calls"][0]
print("\n  Two things that trip people up:")
print(f"    * function.arguments is a STRING, not an object: {call['function']['arguments']!r}")
print(f"      -> you must json.loads() it before calling anything")
print(f"    * every call carries an id: {call['id']!r}")
print( "      -> the result you send back must quote it in tool_call_id")

# ------------------------------------------------------- 3. you execute
rule(3, "EXECUTE - you run the function, then append a role:'tool' message")
print("  The model did NOT call anything. It emitted a request. Execution is")
print("  entirely on your side - that is the whole ch.1 point about RL")
print("  internalising the decision policy, not the execution.")

args = json.loads(call["function"]["arguments"])
result = get_weather(**args)

tool_message = {
    "role": "tool",
    "tool_call_id": call["id"],
    "name": call["function"]["name"],
    "content": json.dumps(result, ensure_ascii=False),
}
show("what you actually executed", {"function": call["function"]["name"], "kwargs": args})
show("tool result message", tool_message)

messages.append(assistant)       # order matters: the call first ...
messages.append(tool_message)    # ... then its result, immediately after

# ------------------------------------------------------- 4. model answers
rule(4, "ANSWER - the model reads the result and replies with no tool_calls")
resp2 = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
choice2 = resp2.choices[0]

print(f"\n  finish_reason = {choice2.finish_reason!r}"
      f"   <- 'stop' means: I am done, no more tools")
print(f"  tool_calls    = {choice2.message.tool_calls}")
print(f"\n  answer: {choice2.message.content}")

rule("*", "THE WHOLE LOOP IN ONE SENTENCE")
print("""  Declare tools -> the model decides which to call and with what arguments
  -> YOU execute and append the result -> the model reads it and continues.

  Repeat steps 2-3 until finish_reason is 'stop', and you have built ReAct.
  That repetition is the only difference between this script and agent/loop.py.

  Note what never changed: `tools` was sent again in step 4, identical, byte
  for byte. Tool definitions live in the static prefix - change them mid-run
  and you invalidate the prefix cache (ch.2).""")

print(f"\n  tokens: prompt={resp.usage.prompt_tokens}+{resp2.usage.prompt_tokens}"
      f"  completion={resp.usage.completion_tokens}+{resp2.usage.completion_tokens}")
