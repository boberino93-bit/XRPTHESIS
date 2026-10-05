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


def evidence_strength(row: dict[str, str]) -> float:
    return (
        float(row["weight"])
        * QUALITY[row["quality"].strip().upper()]
        * STATUS[row["status"].strip().lower()]
    )


def strongest_adverse_evidence(
    evidence: list[dict[str, str]], gates: set[str]
) -> dict[str, str] | None:
    """Return the most decision-relevant adverse observation.

    Gate contradictions rank highest. Gate-neutral evidence is next because a
    thesis gate remaining unproven can be more important than a contradiction
    to a non-gating supporting hypothesis. Non-gate contradictions follow.
    Within each class, source-adjusted evidence strength decides the winner.
    """

    candidates: list[tuple[tuple[int, int, float], dict[str, str]]] = []
    for row in evidence:
        claim_id = row["claim_id"].strip()
        direction = row["direction"].strip().lower()
        is_gate = claim_id in gates

        if direction == "contradict":
            adverse_class = 3 if is_gate else 1
        elif direction == "neutral" and is_gate:
            adverse_class = 2
        else:
            continue

        candidates.append(
            (
                (
                    adverse_class,
                    1 if row["status"].strip().lower() == "confirmed" else 0,
                    evidence_strength(row),
                ),
                row,
            )
        )

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def main() -> None:
    claims = load_csv(CLAIMS)
    evidence = load_csv(EVIDENCE)

    claim_ids = [row["claim_id"].strip() for row in claims]
    if len(claim_ids) != len(set(claim_ids)):
        raise ValueError("Duplicate claim_id values found in data/claims.csv")

    gates = {
        row["claim_id"].strip()
        for row in claims
        if row["gate"].strip().lower() == "true"
    }

    raw = defaultdict(float)
    support_count = defaultdict(int)
    contradict_count = defaultdict(int)
    neutral_count = defaultdict(int)
    evidence_ids: set[str] = set()

    for row in evidence:
        evidence_id = row["evidence_id"].strip()
        claim_id = row["claim_id"].strip()
        direction = row["direction"].strip().lower()
        quality = row["quality"].strip().upper()
        status = row["status"].strip().lower()

        if not evidence_id:
            raise ValueError("Evidence row has an empty evidence_id")
        if evidence_id in evidence_ids:
            raise ValueError(f"Duplicate evidence_id {evidence_id!r}")
        evidence_ids.add(evidence_id)

        if claim_id not in claim_ids:
            raise ValueError(f"Unknown claim_id {claim_id!r} in {evidence_id}")
        if direction not in DIRECTION:
            raise ValueError(f"Unknown direction {direction!r} in {evidence_id}")
        if quality not in QUALITY:
            raise ValueError(f"Unknown quality {quality!r} in {evidence_id}")
        if status not in STATUS:
            raise ValueError(f"Unknown status {status!r} in {evidence_id}")

        try:
            weight = float(row["weight"])
        except ValueError as exc:
            raise ValueError(f"Non-numeric weight in {evidence_id}") from exc
        if not 1.0 <= weight <= 5.0:
            raise ValueError(f"Weight must be between 1 and 5 in {evidence_id}")

        raw[claim_id] += weight * DIRECTION[direction] * QUALITY[quality] * STATUS[status]
        if direction == "support":
            support_count[claim_id] += 1
        elif direction == "contradict":
            contradict_count[claim_id] += 1
        else:
            neutral_count[claim_id] += 1

    scores = {row["claim_id"]: clamp(raw[row["claim_id"]]) for row in claims}
    classification = classify(scores, sorted(gates))
    strongest_adverse = strongest_adverse_evidence(evidence, gates)

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

    lines.extend(
        [
            "",
            "## Interpretation guardrail",
            "",
            "A positive H2/H7 score means evidence of XRPL/institutional/RWA adoption is accumulating. "
            "It does **not** prove H3. H3 must be supported by XRP-specific demand/liquidity evidence.",
            "",
            "## Strongest evidence against the thesis",
            "",
        ]
    )

    if strongest_adverse is None:
        lines.extend(
            [
                "No contradictory or gate-neutral evidence is currently recorded. "
                "That is a data-state observation, not evidence that the thesis is correct.",
                "",
            ]
        )
    else:
        direction = strongest_adverse["direction"].strip().lower()
        lines.extend(
            [
                f"**{strongest_adverse['evidence_id']} — {strongest_adverse['claim_id']} "
                f"({direction}, quality {strongest_adverse['quality']}, weight {strongest_adverse['weight']})**",
                "",
                strongest_adverse["fact"].strip(),
                "",
                f"Interpretation: {strongest_adverse['interpretation'].strip()}",
                "",
                f"Source: {strongest_adverse['source'].strip()}",
                "",
            ]
        )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT}")
    print(classification)
    for cid in sorted(scores):
        print(f"{cid}: {scores[cid]:+.2f}")


if __name__ == "__main__":
    main()
