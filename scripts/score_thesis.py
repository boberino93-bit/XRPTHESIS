#!/usr/bin/env python3
"""Deterministically score the XRP thesis evidence ledger.

This is research telemetry, not a probability model or trading signal.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "data" / "claims.csv"
EVIDENCE = ROOT / "data" / "evidence.csv"
REPORT = ROOT / "reports" / "latest-score.md"

QUALITY = {"A": 1.00, "B": 0.80, "C": 0.60, "D": 0.25}
STATUS = {"confirmed": 1.00, "provisional": 0.50, "disputed": 0.25}
DIRECTION = {"support": 1.0, "neutral": 0.0, "contradict": -1.0}


def clamp(value: float, lo: float = -10.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def classify(scores: dict[str, float], gates: list[str]) -> str:
    gate_scores = [scores.get(g, 0.0) for g in gates]
    avg = sum(scores.values()) / len(scores) if scores else 0.0

    if any(score <= -5.0 for score in gate_scores):
        return "Weakening — a gating hypothesis is strongly negative"
    if scores.get("H3", 0.0) <= -2.0:
        return "Weakening — XRP-specific value capture is negative"
    if gate_scores and all(score >= 2.0 for score in gate_scores) and avg >= 2.0:
        return "Strengthening — gates and aggregate evidence are positive"
    if avg <= -2.0:
        return "Weakening — aggregate evidence is negative"
    return "Mixed / insufficient — adoption evidence does not yet establish all gating links"


def main() -> None:
    claims = load_csv(CLAIMS)
    evidence = load_csv(EVIDENCE)

    raw = defaultdict(float)
    support_count = defaultdict(int)
    contradict_count = defaultdict(int)
    neutral_count = defaultdict(int)

    for row in evidence:
        claim_id = row["claim_id"].strip()
        direction = row["direction"].strip().lower()
        quality = row["quality"].strip().upper()
        status = row["status"].strip().lower()
        weight = float(row["weight"])

        if direction not in DIRECTION:
            raise ValueError(f"Unknown direction {direction!r} in {row['evidence_id']}")
        if quality not in QUALITY:
            raise ValueError(f"Unknown quality {quality!r} in {row['evidence_id']}")
        if status not in STATUS:
            raise ValueError(f"Unknown status {status!r} in {row['evidence_id']}")

        raw[claim_id] += weight * DIRECTION[direction] * QUALITY[quality] * STATUS[status]
        if direction == "support":
            support_count[claim_id] += 1
        elif direction == "contradict":
            contradict_count[claim_id] += 1
        else:
            neutral_count[claim_id] += 1

    scores = {row["claim_id"]: clamp(raw[row["claim_id"]]) for row in claims}
    gates = [row["claim_id"] for row in claims if row["gate"].strip().lower() == "true"]
    classification = classify(scores, gates)

    lines = [
        "# XRP Thesis — Latest Deterministic Score",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        f"**Classification:** {classification}",
        "",
        "> Scores summarize the evidence ledger. They are not probabilities, price forecasts, or trade signals.",
        "",
        "| Claim | Gate | Score | Support | Contradict | Neutral |",
        "|---|:---:|---:|---:|---:|---:|",
    ]

    for row in claims:
        cid = row["claim_id"]
        gate = "YES" if row["gate"].strip().lower() == "true" else ""
        lines.append(
            f"| {cid} — {row['title']} | {gate} | {scores[cid]:+.2f} | "
            f"{support_count[cid]} | {contradict_count[cid]} | {neutral_count[cid]} |"
        )

    lines.extend([
        "",
        "## Interpretation guardrail",
        "",
        "A positive H2/H7 score means evidence of XRPL/institutional/RWA adoption is accumulating. "
        "It does **not** prove H3. H3 must be supported by XRP-specific demand/liquidity evidence.",
        "",
        "## Strongest evidence against the thesis",
        "",
        "This section is intentionally mandatory in every generated report. Automated scoring cannot decide "
        "which contrary fact is economically strongest; reviewers should inspect contradictory and H3-neutral evidence in `data/evidence.csv`.",
        "",
    ])

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT}")
    print(classification)
    for cid in sorted(scores):
        print(f"{cid}: {scores[cid]:+.2f}")


if __name__ == "__main__":
    main()
