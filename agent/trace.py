"""Instrumentation - makes the trajectory's cost visible.

The point of ch.1 thinking question #2: every turn re-reads the WHOLE trajectory,
so cumulative input tokens grow ~quadratically while the new content you actually
added grows linearly. This file prints that gap instead of asserting it.
"""


class Tracer:
    def __init__(self, verbose=True):
        self.rows = []
        self.verbose = verbose

    def turn(self, n, usage, n_messages, tool_names):
        prev = self.rows[-1] if self.rows else None
        cumulative = (prev["cumulative"] if prev else 0) + usage["prompt"]
        new_content = (prev["new_content"] if prev else 0) + usage["completion"]
        self.rows.append(
            {
                "turn": n,
                "messages": n_messages,
                "prompt": usage["prompt"],
                "cached": usage.get("cached", 0),
                "completion": usage["completion"],
                "cumulative": cumulative,
                "new_content": new_content,
                "tools": ",".join(tool_names) or "-",
            }
        )
        if self.verbose:
            r = self.rows[-1]
            cache = f" cache_hit={r['cached']:>6}" if r["cached"] else ""
            print(
                f"  turn {r['turn']:>2} | msgs {r['messages']:>3} | in {r['prompt']:>6}"
                f"{cache} | out {r['completion']:>4} | cum_in {r['cumulative']:>7} | {r['tools']}"
            )

    # ------------------------------------------------------------------

    def report(self):
        if not self.rows:
            print("no turns recorded")
            return
        last = self.rows[-1]
        n = last["turn"]
        print("\n" + "=" * 68)
        print(f"{'TOKEN ACCOUNTING':^68}")
        print("=" * 68)
        print(f"  turns                       {n}")
        print(f"  cumulative INPUT tokens     {last['cumulative']:>9,}   <- grows ~O(n^2)")
        print(f"  cumulative NEW content      {last['new_content']:>9,}   <- grows ~O(n)")
        if last["new_content"]:
            print(f"  you paid to re-read         {last['cumulative'] / last['new_content']:>9.1f}x  "
                  f"what you actually produced")
        cached = sum(r["cached"] for r in self.rows)
        if cached:
            print(f"  cache hits                  {cached:>9,}   ({cached / last['cumulative']:.0%} of input)")
        else:
            print("  cache hits                        none reported by this provider")

        self._chart()
        self._quadratic_check()

    def _chart(self, width=46):
        print("\n  cumulative input tokens per turn")
        peak = max(r["cumulative"] for r in self.rows) or 1
        for r in self.rows:
            bar = "#" * max(1, round(width * r["cumulative"] / peak))
            print(f"  {r['turn']:>3} {bar} {r['cumulative']:,}")

    def _quadratic_check(self):
        """If growth were linear, doubling the turns would double the total.
        Quadratic means it roughly quadruples. Show the measured ratio."""
        n = len(self.rows)
        if n < 4:
            return
        half = self.rows[n // 2 - 1]["cumulative"]
        full = self.rows[-1]["cumulative"]
        if half:
            print(
                f"\n  doubling turns {n // 2} -> {n} multiplied the bill by {full / half:.2f}x"
                f"   (linear would be ~2.0x, quadratic ~4.0x)"
            )
