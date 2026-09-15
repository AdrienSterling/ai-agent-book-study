"""Self-test for loop.py - no API key, no cost, runs in a second.

    uv run python test_loop.py
"""

import sys

from harness import Harness
from loop import run_react_loop
from model import FakeModel
from trace import Tracer


class Spy:
    """Wraps a model and records exactly what context it was handed each turn."""

    def __init__(self, inner):
        self.inner = inner
        self.contexts = []
        self.tools_seen = []

    def __call__(self, messages, tools):
        self.contexts.append(list(messages))
        self.tools_seen.append(tools)
        return self.inner(messages, tools)


def run(ablate=None, stops_after=3, max_turns=12):
    model = Spy(FakeModel(turns_before_answer=stops_after))
    tracer = Tracer(verbose=False)
    answer, trajectory, reason = run_react_loop(
        model, Harness(ablate=ablate), "sum the quarterly revenue", tracer, max_turns=max_turns
    )
    return model, tracer, answer, trajectory, reason


TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


@test
def t1_answers_and_stops():
    """Returns the answer and 'answered' once the model stops calling tools."""
    _, _, answer, _, reason = run(stops_after=3)
    assert reason == "answered", f"stop_reason was {reason!r}"
    assert answer and "FINAL ANSWER" in answer, f"answer was {answer!r}"


@test
def t2_trajectory_is_well_formed():
    """user first; every tool result follows the call that requested it."""
    _, _, _, traj, _ = run(stops_after=3)
    assert traj[0]["role"] == "user", "trajectory must start with the user request"
    assert not any(m["role"] == "system" for m in traj), \
        "the system prompt belongs to the static prefix, not the trajectory"
    for i, m in enumerate(traj):
        for call in m.get("tool_calls") or []:
            follow = [x for x in traj[i + 1:i + 1 + len(m["tool_calls"])] if x["role"] == "tool"]
            assert any(x["tool_call_id"] == call["id"] for x in follow), \
                f"no tool result directly follows call {call['id']}"


@test
def t3_max_turns_is_enforced():
    """A model that never stops must be stopped by the harness."""
    _, tracer, answer, _, reason = run(stops_after=999, max_turns=5)
    assert reason == "max_turns", f"stop_reason was {reason!r}"
    assert answer is None, f"answer should be None, got {answer!r}"
    assert len(tracer.rows) == 5, f"expected 5 model calls, got {len(tracer.rows)}"


@test
def t4_context_is_prefix_plus_trajectory():
    """Rebuilt every turn, always prefixed, always growing."""
    model, _, _, _, _ = run(stops_after=3)
    sizes = [len(c) for c in model.contexts]
    assert all(c[0]["role"] == "system" for c in model.contexts), \
        "every context must start with the static prefix"
    assert sizes == sorted(sizes) and len(set(sizes)) == len(sizes), \
        f"context should grow strictly every turn, got {sizes}"
    assert all(t is not None for t in model.tools_seen), "tools should be passed when not ablated"


@test
def t5_tracer_sees_every_turn():
    """One tracer row per model call - this is what makes the O(n^2) visible."""
    model, tracer, _, _, _ = run(stops_after=4)
    assert len(tracer.rows) == len(model.contexts), \
        f"{len(tracer.rows)} tracer rows vs {len(model.contexts)} model calls"
    assert [r["turn"] for r in tracer.rows] == list(range(1, len(tracer.rows) + 1)), \
        "turn numbers must start at 1 and increase by 1"
    assert tracer.rows[-1]["cumulative"] > tracer.rows[0]["prompt"], "cumulative input should accumulate"


@test
def t6_ablation_tool_results_goes_blind():
    """Experiment 1-1: drop tool results and the agent acts blind - no error, no stop."""
    _, _, _, traj, _ = run(ablate="tool_results", stops_after=999, max_turns=4)
    assert not any(m["role"] == "tool" for m in traj), \
        "with --ablate tool_results the trajectory must contain no observations"


if __name__ == "__main__":
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"  PASS  {t.__name__}  - {t.__doc__.splitlines()[0]}")
        except NotImplementedError:
            print(f"  TODO  {t.__name__}  - loop.py is not implemented yet")
            failed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}  - {e}")
            failed += 1
    print()
    print("all tests passed - now run: uv run python main.py --simulate 16" if not failed
          else f"{failed}/{len(TESTS)} failing")
    sys.exit(1 if failed else 0)
