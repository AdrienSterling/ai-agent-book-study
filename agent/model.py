"""Model - the decision core. The only thing here is: context in, decision out.

Two implementations share one interface so the loop you write in loop.py never
knows which is running:
    RealModel  - an OpenAI-compatible endpoint (Moonshot / DeepSeek / OpenAI / ...)
    FakeModel  - deterministic, no API key, no cost. Used by test_loop.py and
                 by `main.py --simulate N` to make the O(n^2) curve visible for free.
"""

import json
import os
from dataclasses import dataclass, field

PROVIDERS = {
    "moonshot": {"key": "MOONSHOT_API_KEY", "base": "https://api.moonshot.cn/v1", "model": "kimi-k2-0905-preview"},
    "deepseek": {"key": "DEEPSEEK_API_KEY", "base": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "openai": {"key": "OPENAI_API_KEY", "base": None, "model": "gpt-4o-mini"},
}


@dataclass
class Decision:
    """What the model decided this turn."""

    message: dict                      # raw assistant message, appended to the trajectory verbatim
    tool_calls: list = field(default_factory=list)
    answer: str | None = None          # set only when there are no tool calls
    usage: dict = field(default_factory=dict)  # prompt / cached / completion tokens


class RealModel:
    def __init__(self, provider=None, model=None):
        from openai import OpenAI  # imported late so --simulate works without the dep

        provider = provider or self._autodetect()
        cfg = PROVIDERS[provider]
        api_key = os.environ.get(cfg["key"])
        if not api_key:
            raise SystemExit(f"{cfg['key']} is not set. Try --simulate 12 for the offline demo.")
        base = os.environ.get(f"{provider.upper()}_BASE_URL") or cfg["base"]
        self.client = OpenAI(api_key=api_key, base_url=base)
        self.name = model or os.environ.get("AGENT_MODEL") or cfg["model"]
        self.provider = provider

    @staticmethod
    def _autodetect():
        for p, cfg in PROVIDERS.items():
            if os.environ.get(cfg["key"]):
                return p
        raise SystemExit("No provider key found. Set MOONSHOT_API_KEY / DEEPSEEK_API_KEY / OPENAI_API_KEY.")

    def list_models(self):
        return sorted(m.id for m in self.client.models.list().data)

    def __call__(self, messages, tools):
        kwargs = {"model": self.name, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        resp = self.client.chat.completions.create(**kwargs)
        choice = resp.choices[0].message
        message = choice.model_dump(exclude_none=True)
        # some providers return non-standard keys that they then reject on the way back in
        message.pop("annotations", None)
        message.pop("audio", None)

        u = resp.usage
        details = getattr(u, "prompt_tokens_details", None)
        usage = {
            "prompt": u.prompt_tokens,
            "cached": getattr(details, "cached_tokens", 0) or 0,
            "completion": u.completion_tokens,
        }
        calls = [tc.model_dump() for tc in (choice.tool_calls or [])]
        return Decision(message=message, tool_calls=calls, answer=choice.content if not calls else None, usage=usage)


class FakeModel:
    """Deterministic stand-in. Calls one tool per turn for `turns_before_answer`
    turns, then answers. Token counts are a rough char/4 estimate - enough to
    show the shape of the growth, which is the whole point."""

    name = "fake-model"
    provider = "fake"

    def __init__(self, turns_before_answer=10):
        self.turns_before_answer = turns_before_answer
        self.turn = 0

    def __call__(self, messages, tools):
        self.turn += 1
        prompt_tokens = sum(len(json.dumps(m, ensure_ascii=False)) for m in messages) // 4

        if self.turn > self.turns_before_answer or not tools:
            text = f"FINAL ANSWER: done after {self.turn} turns."
            return Decision(
                message={"role": "assistant", "content": text},
                answer=text,
                usage={"prompt": prompt_tokens, "cached": 0, "completion": len(text) // 4},
            )

        call = {
            "id": f"call_{self.turn}",
            "type": "function",
            "function": {
                "name": "convert_currency",
                "arguments": json.dumps({"amount": 1000 * self.turn, "from_currency": "EUR", "to_currency": "USD"}),
            },
        }
        message = {
            "role": "assistant",
            "content": None,
            "reasoning": f"Step {self.turn}: convert the next amount before summing.",
            "tool_calls": [call],
        }
        return Decision(
            message=message,
            tool_calls=[call],
            usage={"prompt": prompt_tokens, "cached": 0, "completion": 40},
        )
