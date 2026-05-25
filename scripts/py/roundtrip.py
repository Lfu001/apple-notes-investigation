"""Round-trip test runner.

For each note in iCloud > HTMLTest:
  1. get_body -> save as data/before/<name>.html
  2. set_body with that exact content
  3. wait (delay)
  4. get_body again -> save as data/after/<name>.html
  5. (optional) repeat step 2-4 with the 'after' content to check 2nd-round convergence
  6. compute hashes, generate diffs, write summary JSON
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
from compare import is_fixed_point, sha256, unified_diff

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA = REPO_ROOT / "data"
BEFORE = DATA / "before"
AFTER = DATA / "after"
DIFFS = DATA / "diffs"
RUNS = DATA / "runs"


def round_trip_once(name: str, delay: float) -> tuple[str, str]:
    """Return (before, after) for one round-trip of the named note."""
    before = notes.get_body(name)
    notes.set_body(name, before)
    time.sleep(delay)
    after = notes.get_body(name)
    return before, after


def run(delay: float, second_round: bool, filter_pattern: str | None) -> int:
    BEFORE.mkdir(parents=True, exist_ok=True)
    AFTER.mkdir(parents=True, exist_ok=True)
    DIFFS.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)

    all_notes = notes.list_notes()
    if filter_pattern:
        all_notes = [n for n in all_notes if filter_pattern in n.name]
    if not all_notes:
        print("No notes found in HTMLTest folder.", file=sys.stderr)
        return 1

    print(f"Found {len(all_notes)} note(s) in HTMLTest:")
    for n in all_notes:
        print(f"  - {n.name}")

    results = []
    for ref in all_notes:
        name = ref.name
        print(f"\n[{name}] round-trip…", flush=True)
        try:
            before, after = round_trip_once(name, delay)
        except notes.NotesError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            results.append({"name": name, "status": "error", "error": str(e)})
            continue

        (BEFORE / f"{name}.html").write_text(before, encoding="utf-8")
        (AFTER / f"{name}.html").write_text(after, encoding="utf-8")

        fp_first = is_fixed_point(before, after)
        result = {
            "name": name,
            "id": ref.id,
            "before_sha256": sha256(before),
            "after_sha256": sha256(after),
            "before_bytes": len(before),
            "after_bytes": len(after),
            "fixed_point_first_round": fp_first,
        }

        if not fp_first:
            diff = unified_diff(before, after, name)
            (DIFFS / f"{name}.diff").write_text(diff, encoding="utf-8")
            result["diff_lines"] = diff.count("\n")
            print(f"  CHANGED (1st round): {result['diff_lines']} diff lines")

            if second_round:
                # See if the after-content is itself a fixed point
                try:
                    notes.set_body(name, after)
                    time.sleep(delay)
                    after2 = notes.get_body(name)
                except notes.NotesError as e:
                    print(f"  2nd-round ERROR: {e}", file=sys.stderr)
                    result["second_round_error"] = str(e)
                else:
                    (AFTER / f"{name}.round2.html").write_text(after2, encoding="utf-8")
                    fp_second = is_fixed_point(after, after2)
                    result["fixed_point_second_round"] = fp_second
                    result["after2_sha256"] = sha256(after2)
                    if not fp_second:
                        diff2 = unified_diff(after, after2, name)
                        (DIFFS / f"{name}.round2.diff").write_text(diff2, encoding="utf-8")
                    print(f"  2nd round fixed_point={fp_second}")
        else:
            print("  FIXED POINT (1st round)")

        results.append(result)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = RUNS / f"{ts}.json"
    summary = {
        "timestamp": ts,
        "delay_seconds": delay,
        "second_round_enabled": second_round,
        "filter": filter_pattern,
        "results": results,
    }
    run_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote summary: {run_path}")

    n_fp1 = sum(1 for r in results if r.get("fixed_point_first_round"))
    n_fp2 = sum(1 for r in results if r.get("fixed_point_second_round"))
    n_err = sum(1 for r in results if r.get("status") == "error")
    print(
        f"\nSummary: {n_fp1}/{len(results)} fixed-point on 1st round, "
        f"{n_fp2} converged on 2nd round, {n_err} errors"
    )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Round-trip test for Notes.app HTML")
    p.add_argument("--delay", type=float, default=1.5, help="Seconds to wait after set_body")
    p.add_argument(
        "--no-second-round",
        dest="second_round",
        action="store_false",
        default=True,
        help="Skip the 2nd-round convergence check",
    )
    p.add_argument("--filter", help="Only process notes whose name contains this substring")
    args = p.parse_args()
    return run(args.delay, args.second_round, args.filter)


if __name__ == "__main__":
    sys.exit(main())
