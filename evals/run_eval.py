"""Offline eval: run the full pipeline on labeled claims and report accuracy per verdict class.

Run on every prompt / model change to catch regressions:
    python evals/run_eval.py            # all claims
    python evals/run_eval.py --limit 3  # quick smoke test
"""
import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from agent import run_pipeline  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="evals/results.json")
    args = ap.parse_args()

    cases = json.load(open(os.path.join(os.path.dirname(__file__), "claims.json")))[: args.limit]
    per_class = defaultdict(lambda: [0, 0])          # expected -> [correct, total]
    confusion = Counter()
    rows = []

    for i, case in enumerate(cases, 1):
        t0 = time.time()
        result = run_pipeline(case["claim"])
        got = result["verdict"]["verdict"]
        ok = got == case["expected"]
        per_class[case["expected"]][0] += ok
        per_class[case["expected"]][1] += 1
        confusion[(case["expected"], got)] += 1
        rows.append({**case, "got": got, "correct": ok,
                     "confidence": result["verdict"].get("confidence"),
                     "steps": len(result["trace"]), "sources": len(result["sources"]),
                     "citation_issues": len(result["verdict"].get("citation_issues", [])),
                     "seconds": round(time.time() - t0, 1)})
        print(f"[{i}/{len(cases)}] {'✓' if ok else '✗'} {case['claim'][:55]:55} expected={case['expected']:22} got={got}")

    total_ok = sum(r["correct"] for r in rows)
    print(f"\nOverall accuracy: {total_ok}/{len(rows)} = {total_ok / max(len(rows), 1):.0%}")
    for cls, (c, t) in per_class.items():
        print(f"  {cls:22} {c}/{t}")
    print("\nConfusion (expected -> got):")
    for (exp, got), n in sorted(confusion.items()):
        print(f"  {exp:22} -> {got:22} {n}")
    avg = lambda k: sum(r[k] for r in rows) / max(len(rows), 1)  # noqa: E731
    print(f"\nAvg agent steps: {avg('steps'):.1f} · avg sources: {avg('sources'):.1f} · "
          f"avg citation issues: {avg('citation_issues'):.1f} · avg latency: {avg('seconds'):.1f}s")

    json.dump(rows, open(args.out, "w"), indent=2)
    print(f"Saved per-claim results to {args.out}")


if __name__ == "__main__":
    main()
