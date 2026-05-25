"""Multi-round convergence test.

For each note: capture body, then set->get up to MAX_ROUNDS times,
recording each result. Detect when consecutive results match (=converged).

This is needed for GUI-created notes which often need 2-3 rounds to settle.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes
from compare import sha256, unified_diff

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA = REPO_ROOT / "data"
MULTI = DATA / "multi"
RUNS = DATA / "runs"

MAX_ROUNDS = 5


def run(delay: float, filter_pattern: str | None) -> int:
    MULTI.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)

    all_notes = notes.list_notes()
    if filter_pattern:
        all_notes = [n for n in all_notes if filter_pattern in n.name]

    if not all_notes:
        print("No notes match.", file=sys.stderr)
        return 1

    results = []
    for ref in all_notes:
        name = ref.name
        print(f"\n[{name}]")
        sub = MULTI / name
        sub.mkdir(exist_ok=True)

        rounds: list[str] = []
        try:
            body = notes.get_body(name)
        except notes.NotesError as e:
            print(f"  initial get ERROR: {e}", file=sys.stderr)
            results.append({"name": name, "status": "error", "error": str(e)})
            continue
        rounds.append(body)
        (sub / "r0.html").write_text(body, encoding="utf-8")

        converged_at = None
        for r in range(1, MAX_ROUNDS + 1):
            try:
                notes.set_body(name, rounds[-1])
                time.sleep(delay)
                body = notes.get_body(name)
            except notes.NotesError as e:
                print(f"  round {r} ERROR: {e}", file=sys.stderr)
                break
            rounds.append(body)
            (sub / f"r{r}.html").write_text(body, encoding="utf-8")

            if body == rounds[-2]:
                converged_at = r
                print(f"  converged after {r} round(s)")
                break

        # Build per-round diffs
        diffs = []
        for i in range(1, len(rounds)):
            d = unified_diff(rounds[i - 1], rounds[i], f"{name}.r{i - 1}-r{i}")
            (sub / f"r{i - 1}-r{i}.diff").write_text(d, encoding="utf-8")
            diffs.append({"from": i - 1, "to": i, "lines": d.count("\n"), "empty": not d})

        if converged_at is None:
            print(f"  DID NOT CONVERGE within {MAX_ROUNDS} rounds")

        results.append({
            "name": name,
            "rounds_run": len(rounds) - 1,
            "converged_at_round": converged_at,
            "round_hashes": [sha256(r) for r in rounds],
            "round_bytes": [len(r) for r in rounds],
            "diffs": diffs,
        })

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RUNS / f"multi-{ts}.json"
    out.write_text(json.dumps({"timestamp": ts, "delay": delay, "max_rounds": MAX_ROUNDS, "filter": filter_pattern, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote: {out}")

    converged = sum(1 for r in results if r.get("converged_at_round") is not None)
    print(f"\nSummary: {converged}/{len(results)} converged within {MAX_ROUNDS} rounds")
    # Histogram
    hist: dict[int, int] = {}
    for r in results:
        c = r.get("converged_at_round")
        if c is not None:
            hist[c] = hist.get(c, 0) + 1
    print("Convergence histogram (round -> count):")
    for k in sorted(hist):
        print(f"  r{k}: {hist[k]}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Multi-round convergence test")
    p.add_argument("--delay", type=float, default=2.0)
    p.add_argument("--filter", help="Substring filter on note names")
    args = p.parse_args()
    return run(args.delay, args.filter)


if __name__ == "__main__":
    sys.exit(main())
