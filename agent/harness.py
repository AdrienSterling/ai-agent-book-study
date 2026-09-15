"""Harness - everything inside the agent boundary but outside the model.

Book mapping (ch.1):
    Harness = context management + tool interface + constrain + verify + correct
This file covers the first three. verify/correct arrive in ch.5.

The Environment (the tool implementations at the bottom of this file) is NOT Harness -
it is what the tools reach into. Keeping them in one file is a ch.1 simplification.
"""

import json

# --------------------------------------------------------------------------
# Tool definitions - the "action interface" the model can see.
# Anything not declared here does not exist for the model.
# --------------------------------------------------------------------------

RATES_TO_USD = {"USD": 1.0, "EUR": 1.087, "GBP": 1.266, "JPY": 0.00669, "CNY": 0.1385}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert an amount from one currency to USD-based target currency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount in the source currency, e.g. 2100000"},
                    "from_currency": {"type": "string", "description": "USD | EUR | GBP | JPY | CNY"},
                    "to_currency": {"type": "string", "description": "USD | EUR | GBP | JPY | CNY"},
                },
                "required": ["amount", "from_currency", "to_currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate an arithmetic expression. Supports + - * / ( ) and numbers only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "e.g. '(2500000 + 2282608.7) / 4'"},
                },
                "required": ["expression"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are a financial analysis agent. Use the provided tools for every currency "
    "conversion and every arithmetic step - never compute from memory. "
    "When the task is complete, reply with a final answer and make no further tool calls."
)

# --------------------------------------------------------------------------
# Environment - the tools actually executing. Not part of the Harness.
# --------------------------------------------------------------------------


def _convert_currency(amount, from_currency, to_currency):
    f, t = from_currency.upper(), to_currency.upper()
    if f not in RATES_TO_USD or t not in RATES_TO_USD:
        raise ValueError(f"unsupported currency pair {f}->{t}")
    return {"result": round(amount * RATES_TO_USD[f] / RATES_TO_USD[t], 2), "pair": f"{f}->{t}"}


def _calculate(expression):
    allowed = set("0123456789.+-*/() ")
    if not set(expression) <= allowed:
        raise ValueError("expression contains characters outside the allowed set")
    return {"result": eval(expression, {"__builtins__": {}}, {})}  # constrained above


IMPLEMENTATIONS = {"convert_currency": _convert_currency, "calculate": _calculate}


# --------------------------------------------------------------------------
# The Harness itself
# --------------------------------------------------------------------------

ABLATIONS = ("tool_definitions", "tool_results", "reasoning", "history")


class Harness:
    """Assembles context, exposes tools, constrains calls.

    `ablate` reproduces Experiment 1-1: remove exactly one context component
    and observe how the agent fails. Note it never fails loudly.
    """

    def __init__(self, ablate=None):
        if ablate and ablate not in ABLATIONS:
            raise SystemExit(f"--ablate must be one of {ABLATIONS}")
        self.ablate = ablate

    # ---- context management -------------------------------------------------

    def static_prefix(self):
        """System prompt + tool definitions. Constant across the run.
        Keeping it byte-stable is what lets prefix caching hit (ch.2)."""
        return [{"role": "system", "content": SYSTEM_PROMPT}]

    def tools_param(self):
        """Ablation 'tool_definitions': the model keeps talking, it just cannot act."""
        return None if self.ablate == "tool_definitions" else TOOL_SCHEMAS

    def build_context(self, trajectory):
        """context = static prefix + trajectory   <- the whole of ch.1 in one line."""
        traj = trajectory
        if self.ablate == "history":
            # keep only the newest user message and anything after the last one
            last_user = max((i for i, m in enumerate(traj) if m["role"] == "user"), default=0)
            traj = traj[last_user:]
        return self.static_prefix() + traj

    # ---- recording into the trajectory --------------------------------------

    def record_decision(self, trajectory, decision):
        """Append the model's reply. Ablation 'reasoning' drops the thinking."""
        msg = dict(decision.message)
        if self.ablate == "reasoning":
            msg.pop("reasoning", None)
            msg.pop("reasoning_content", None)
        trajectory.append(msg)

    def record_observation(self, trajectory, call_id, name, content):
        """Append a tool result. Ablation 'tool_results' drops it -> blind retries."""
        if self.ablate == "tool_results":
            return
        trajectory.append(
            {"role": "tool", "tool_call_id": call_id, "name": name, "content": content}
        )

    # ---- constrain + execute -------------------------------------------------

    def validate(self, call):
        """Constrain: reject anything the model invented. Returns (name, kwargs) or raises."""
        name = call["function"]["name"]
        if name not in IMPLEMENTATIONS:
            raise ValueError(f"unknown tool '{name}' (model hallucinated it)")
        try:
            kwargs = json.loads(call["function"]["arguments"] or "{}")
        except json.JSONDecodeError as e:
            raise ValueError(f"arguments were not valid JSON: {e}")
        return name, kwargs

    def execute(self, call):
        """Validate then run. Errors come back as observations, not exceptions -
        an agent that can read its own error can recover from it."""
        try:
            name, kwargs = self.validate(call)
            return json.dumps(IMPLEMENTATIONS[name](**kwargs), ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
