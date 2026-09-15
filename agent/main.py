"""Chapter 1 artifact - a bare ReAct loop, no framework.

    uv run python test_loop.py            # verify loop.py, offline, free
    uv run python main.py --simulate 16   # watch cumulative tokens grow, offline, free
    uv run python main.py                 # real model, default task
    uv run python main.py --ablate tool_definitions     # Experiment 1-1
    uv run python main.py --list-models
"""

import argparse

from harness import ABLATIONS, Harness
from loop import run_react_loop
from model import PROVIDERS, FakeModel, RealModel
from trace import Tracer

DEFAULT_TASK = (
    "Company quarterly revenue: Q1 2.5M USD, Q2 2.1M EUR, Q3 1.8M GBP, Q4 380M JPY. "
    "Compute the annual total and the quarterly average, both in USD."
)


def main():
    p = argparse.ArgumentParser(description="ch.1 - bare ReAct loop")
    p.add_argument("--task", default=DEFAULT_TASK)
    p.add_argument("--provider", choices=list(PROVIDERS), help="default: first key found in env")
    p.add_argument("--model", help="override the model id")
    p.add_argument("--max-turns", type=int, default=12)
    p.add_argument("--ablate", choices=ABLATIONS, help="Experiment 1-1: drop one context component")
    p.add_argument("--simulate", type=int, metavar="N", default=0,
                   help="offline: fake model that calls a tool N times before answering")
    p.add_argument("--list-models", action="store_true")
    p.add_argument("--show-trajectory", action="store_true")
    args = p.parse_args()

    if args.list_models:
        for m in RealModel(args.provider, args.model).list_models():
            print(" ", m)
        return

    model = FakeModel(args.simulate) if args.simulate else RealModel(args.provider, args.model)
    harness = Harness(ablate=args.ablate)
    tracer = Tracer()

    print(f"\nmodel     {model.name}  ({model.provider})")
    print(f"ablation  {args.ablate or 'none - full context'}")
    print(f"task      {args.task[:70]}{'...' if len(args.task) > 70 else ''}\n")

    answer, trajectory, reason = run_react_loop(
        model, harness, args.task, tracer, max_turns=args.max_turns
    )

    print(f"\nstop reason: {reason}")
    print("-" * 68)
    print(answer if answer else "(no answer - the agent never stopped on its own)")
    print("-" * 68)

    tracer.report()

    if args.show_trajectory:
        print("\n  TRAJECTORY")
        for i, m in enumerate(trajectory):
            body = m.get("content") or ""
            if m.get("tool_calls"):
                body = " + ".join(c["function"]["name"] + "(" + c["function"]["arguments"] + ")"
                                  for c in m["tool_calls"])
            print(f"  {i:>2} {m['role']:<10} {str(body)[:90]}")

    print("\n  Note: an agent that answers is not the same as an agent that was right.")
    print("  Re-run with --ablate tool_definitions and read the answer carefully.\n")


if __name__ == "__main__":
    main()
