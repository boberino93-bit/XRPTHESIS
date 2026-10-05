#!/usr/bin/env python3
"""Deterministically score the XRP thesis evidence ledger.

This is research telemetry, not a probability model or trading signal.
"""

from __future__ import annotations

import csv
from collections import defaultdict
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


def calculate_scores(
    claims: list[dict[str, str]], evidence: list[dict[str, str]]
) -> tuple[
    dict[str, float],
    dict[str, int],
    dict[str, int],
    dict[str, int],
    list[str],
    str,
]:
    claim_ids = {row["claim_id"].strip() for row in claims}
    raw = defaultdict(float)
    support_count = defaultdict(int)
    contradict_count = defaultdict(int)
    neutral_count = defaultdict(int)

    for row in evidence:
        evidence_id = row["evidence_id"].strip()
        claim_id = row["claim_id"].strip()
        if claim_id not in claim_ids:
            raise ValueError(f"Unknown claim_id {claim_id!r} in {evidence_id}")

        direction = row["direction"].strip().lower()
        quality = row["quality"].strip().upper()
        status = row["status"].strip().lower()
        weight = float(row["weight"])

        if direction not in DIRECTION:
            raise ValueError(f"Unknown direction {direction!r} in {evidence_id}")
        if quality not in QUALITY:
            raise ValueError(f"Unknown quality {quality!r} in {evidence_id}")
        if status not in STATUS:
            raise ValueError(f"Unknown status {status!r} in {evidence_id}")

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
    return scores, support_count, contradict_count, neutral_count, gates, classification


def evidence_strength(row: dict[str, str]) -> float:
    return (
        float(row["weight"])
        * QUALITY[row["quality"].strip().upper()]
        * STATUS[row["status"].strip().lower()]
    )


def source_reference(source: str) -> str:
    urls = [part.strip() for part in source.split(";") if part.strip()]
    if not urls:
        return "source missing"
    if len(urls) == 1:
        return f"[source]({urls[0]})"
    return f"[primary source]({urls[0]}) (+{len(urls) - 1} more in the evidence ledger)"


def render_adversarial_section(evidence: list[dict[str, str]]) -> list[str]:
    contradictory = sorted(
        (row for row in evidence if row["direction"].strip().lower() == "contradict"),
        key=lambda row: (-evidence_strength(row), row["evidence_id"]),
    )
    h3_neutral = sorted(
        (
            row
            for row in evidence
            if row["claim_id"].strip() == "H3"
            and row["direction"].strip().lower() == "neutral"
        ),
        key=lambda row: (-evidence_strength(row), row["evidence_id"]),
    )

    lines = [
        "## Strongest evidence against the thesis",
        "",
        "This section is generated directly from the committed evidence ledger so automated rescoring cannot replace adversarial context with placeholder prose.",
        "",
        "### Contradictory evidence",
        "",
    ]

    if contradictory:
        for row in contradictory[:3]:
            lines.append(
                f"- **{row['evidence_id']} / {row['claim_id']}** — {row['fact']} "
                f"({source_reference(row['source'])})"
            )
    else:
        lines.append("- No rows are currently classified as `contradict`.")

    lines.extend(["", "### H3-neutral constraints", ""])
    if h3_neutral:
        for row in h3_neutral[:3]:
            lines.append(
                f"- **{row['evidence_id']}** — {row['fact']} "
                f"({source_reference(row['source'])})"
            )
    else:
        lines.append("- No H3-neutral rows are currently recorded.")

    lines.extend(
        [
            "",
            "Neutral H3 observations are shown because real ecosystem adoption that does not establish XRP-specific demand is a central falsification constraint, even though neutral rows contribute zero to the numeric score.",
            "",
        ]
    )
    return lines


def render_report(claims: list[dict[str, str]], evidence: list[dict[str, str]]) -> str:
    scores, support_count, contradict_count, neutral_count, gates, classification = calculate_scores(
        claims, evidence
    )
    evidence_through = max((row["observed_date"].strip() for row in evidence), default="none")
    average = sum(scores.values()) / len(scores) if scores else 0.0

    lines = [
        "# XRP Thesis — Latest Deterministic Score",
        "",
        f"Evidence through: {evidence_through}",
        f"Evidence rows: {len(evidence)}",
        "",
        f"**Classification:** {classification}",
        "",
        "> Scores summarize the evidence ledger. They are not probabilities, price forecasts, or trade signals.",
        "",
        f"Aggregate mean score: **{average:+.2f}**. Gate scores remain decisive for classification.",
        "",
        "| Claim | Gate | Score | Support | Contradict | Neutral |",
        "|---|:---:|---:|---:|---:|---:|",
    ]

    for row in claims:
        cid = row["claim_id"]
        gate = "YES" if cid in gates else ""
        lines.append(
            f"| {cid} — {row['title']} | {gate} | {scores[cid]:+.2f} | "
            f"{support_count[cid]} | {contradict_count[cid]} | {neutral_count[cid]} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation guardrail",
            "",
            "A positive H2/H7 score means evidence of XRPL/institutional/RWA adoption is accumulating. It does **not** prove H3. H3 requires XRP-specific demand/liquidity evidence, while H1 separately requires economically meaningful bridge/settlement usage.",
            "",
        ]
    )
    lines.extend(render_adversarial_section(evidence))
    return "\n".join(lines)


def main() -> None:
    claims = load_csv(CLAIMS)
    evidence = load_csv(EVIDENCE)
    report = render_report(claims, evidence)
    scores, _, _, _, _, classification = calculate_scores(claims, evidence)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(f"Wrote {REPORT}")
    print(classification)
    for cid in sorted(scores):
        print(f"{cid}: {scores[cid]:+.2f}")


if __name__ == "__main__":
    main()
