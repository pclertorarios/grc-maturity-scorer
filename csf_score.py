"""NIST CSF 2.0 maturity scorer.

Reads a CSV of self-assessment results (one row per CSF 2.0 category) and
produces a maturity summary per Function, the gap against a target tier,
and a prioritized list of categories to work on.

Input CSV columns:
    function   - CSF 2.0 Function code: GV, ID, PR, DE, RS, RC
    category   - Category identifier, e.g. GV.OC, ID.AM, PR.AA
    current    - Current maturity score (0-4)
    target     - Target maturity score (0-4)
    weight     - Optional business weight (default 1.0)

Usage:
    python csf_score.py sample_assessment.csv
    python csf_score.py sample_assessment.csv --json
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path

FUNCTIONS = {
    "GV": "Govern",
    "ID": "Identify",
    "PR": "Protect",
    "DE": "Detect",
    "RS": "Respond",
    "RC": "Recover",
}
MIN_SCORE, MAX_SCORE = 0.0, 4.0


@dataclass
class CategoryResult:
    function: str
    category: str
    current: float
    target: float
    weight: float = 1.0

    @property
    def gap(self) -> float:
        return max(self.target - self.current, 0.0)

    @property
    def weighted_gap(self) -> float:
        return self.gap * self.weight


def _score(value: str, field: str, line: int) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"line {line}: '{field}' must be a number, got {value!r}")
    if not MIN_SCORE <= number <= MAX_SCORE:
        raise ValueError(f"line {line}: '{field}' must be between 0 and 4, got {number}")
    return number


def load_assessment(path: Path) -> list[CategoryResult]:
    results: list[CategoryResult] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"function", "category", "current", "target"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
        for line, row in enumerate(reader, start=2):
            function = row["function"].strip().upper()
            if function not in FUNCTIONS:
                raise ValueError(f"line {line}: unknown function {function!r}")
            category = row["category"].strip().upper()
            if not category.startswith(function + "."):
                raise ValueError(f"line {line}: category {category!r} does not belong to {function}")
            weight_raw = (row.get("weight") or "").strip()
            weight = float(weight_raw) if weight_raw else 1.0
            if weight <= 0:
                raise ValueError(f"line {line}: 'weight' must be positive")
            results.append(
                CategoryResult(
                    function=function,
                    category=category,
                    current=_score(row["current"], "current", line),
                    target=_score(row["target"], "target", line),
                    weight=weight,
                )
            )
    if not results:
        raise ValueError("assessment file has no rows")
    return results


def summarize(results: list[CategoryResult]) -> dict:
    by_function: dict[str, dict] = {}
    for code, name in FUNCTIONS.items():
        rows = [r for r in results if r.function == code]
        if not rows:
            continue
        total_weight = sum(r.weight for r in rows)
        current = sum(r.current * r.weight for r in rows) / total_weight
        target = sum(r.target * r.weight for r in rows) / total_weight
        by_function[code] = {
            "name": name,
            "categories": len(rows),
            "current": round(current, 2),
            "target": round(target, 2),
            "gap": round(max(target - current, 0.0), 2),
        }
    total_weight = sum(r.weight for r in results)
    overall_current = sum(r.current * r.weight for r in results) / total_weight
    overall_target = sum(r.target * r.weight for r in results) / total_weight
    priorities = sorted(
        (r for r in results if r.gap > 0),
        key=lambda r: (-r.weighted_gap, r.category),
    )
    return {
        "overall": {
            "current": round(overall_current, 2),
            "target": round(overall_target, 2),
            "gap": round(max(overall_target - overall_current, 0.0), 2),
        },
        "functions": by_function,
        "priorities": [
            {"category": r.category, "gap": round(r.gap, 2), "weighted_gap": round(r.weighted_gap, 2)}
            for r in priorities
        ],
    }


def render_text(summary: dict, top: int = 5) -> str:
    lines = ["NIST CSF 2.0 maturity summary", "=" * 32]
    o = summary["overall"]
    lines.append(f"Overall: current {o['current']:.2f} / target {o['target']:.2f} (gap {o['gap']:.2f})")
    lines.append("")
    lines.append(f"{'Function':<13}{'Cat.':>5}{'Current':>9}{'Target':>8}{'Gap':>6}")
    for code, f in summary["functions"].items():
        lines.append(f"{code + ' ' + f['name']:<13}{f['categories']:>5}{f['current']:>9.2f}{f['target']:>8.2f}{f['gap']:>6.2f}")
    lines.append("")
    lines.append(f"Top {top} priorities (by weighted gap):")
    for item in summary["priorities"][:top]:
        lines.append(f"  - {item['category']}: gap {item['gap']:.2f} (weighted {item['weighted_gap']:.2f})")
    if not summary["priorities"]:
        lines.append("  - none: every category meets its target")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score a NIST CSF 2.0 self-assessment.")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--top", type=int, default=5, help="number of priorities to show")
    args = parser.parse_args(argv)
    try:
        summary = summarize(load_assessment(args.csv_file))
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2) if args.json else render_text(summary, args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
