#!/usr/bin/env python3
"""Deterministically score the XRP thesis evidence ledger.

This is research telemetry, not a probability model or trading signal.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from validate_data import load_csv, validate_all

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "data" / "claims.csv"
EVIDENCE = ROOT / "data" / "evidence.csv"
PREDICTIONS = ROOT / "data" / "predictions.csv"
REPORT = ROOT / "reports" / "latest-score.md"

QUALITY = {"A": 1.00, "B": 0.80, "C": 0.60, "D": 0.25}
STATUS = {"confirmed": 1.00, "provisional": 0.50, "disputed": 0.25}
DIRECTION = {"support": 1.0, "neutral": 0.0, "contradict": -1.0}


def clamp(value: float, lo: float = -10.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def evidence_contribution(row: dict[str, str]) -> float:
    direction = row["direction"].strip().lower()
    quality = row["quality"].strip().upper()
    status = row["status"].strip().lower()
    weight = float(row["weight"])
    return weight * DIRECTION[direction] * QUALITY[quality] * STATUS[status]


def classify(scores: dict[str, float], gates: set[str]) -> str:
    gate_scores = [scores.get(gate, 0.0) for gate in sorted(gates)]
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


def score_claims(
    claims: list[dict[str, str]], evidence: list[dict[str, str]]
) -> tuple[dict[str, float], dict[str, dict[str, int]]]:
    raw = defaultdict(float)
    counts = {
        "support": defaultdict(int),
        "contradict": defaultdict(int),
        "neutral": defaultdict(int),
    }

    for row in evidence:
        claim_id = row["claim_id"].strip()
        direction = row["direction"].strip().lower()
        raw[claim_id] += evidence_contribution(row)
        counts[direction][claim_id] += 1

    scores = {
        row["claim_id"].strip(): clamp(raw[row["claim_id"].strip()])
        for row in claims
    }
    return scores, counts


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
    Within each class, confirmed evidence and source-adjusted strength decide.
    """

    candidates: list[tuple[tuple[int, int, float, str], dict[str, str]]] = []
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
                    row["evidence_id"].strip(),
                ),
                row,
            )
        )

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def build_report(
    claims: list[dict[str, str]],
    evidence: list[dict[str, str]],
    scores: dict[str, float],
    counts: dict[str, dict[str, int]],
    gates: set[str],
) -> str:
    classification = classify(scores, gates)
    strongest_adverse = strongest_adverse_evidence(evidence, gates)
    ledger_through = max(
        (row["observed_date"].strip() for row in evidence), default="n/a"
    )

    lines = [
        "# XRP Thesis — Latest Deterministic Score",
        "",
        f"Ledger through: {ledger_through}",
        "",
        f"**Classification:** {classification}",
        "",
        "> Scores summarize the committed evidence ledger. They are not probabilities, price forecasts, or trade signals.",
        "",
        f"Evidence rows: {len(evidence)}",
        "",
        "| Claim | Gate | Score | Support | Contradict | Neutral |",
        "|---|:---:|---:|---:|---:|---:|",
    ]

    for row in claims:
        claim_id = row["claim_id"].strip()
        gate = "YES" if claim_id in gates else ""
        lines.append(
            f"| {claim_id} — {row['title']} | {gate} | {scores[claim_id]:+.2f} | "
            f"{counts['support'][claim_id]} | {counts['contradict'][claim_id]} | "
            f"{counts['neutral'][claim_id]} |"
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

    return "\n".join(lines)


def main() -> None:
    claims = load_csv(CLAIMS)
    evidence = load_csv(EVIDENCE)
    predictions = load_csv(PREDICTIONS)
    _, gates = validate_all(claims, evidence, predictions)

    scores, counts = score_claims(claims, evidence)
    report = build_report(claims, evidence, scores, counts, gates)
    classification = classify(scores, gates)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT}")
    print(classification)
    for claim_id in sorted(scores):
        print(f"{claim_id}: {scores[claim_id]:+.2f}")


if __name__ == "__main__":
    main()
