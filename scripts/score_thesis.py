#!/usr/bin/env python3
"""Validate and deterministically score the XRP thesis research state.

This is research telemetry, not a probability model or trading signal.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "data" / "claims.csv"
EVIDENCE = ROOT / "data" / "evidence.csv"
PREDICTIONS = ROOT / "data" / "predictions.csv"
REPORT = ROOT / "reports" / "latest-score.md"

QUALITY = {"A": 1.00, "B": 0.80, "C": 0.60, "D": 0.25}
STATUS = {"confirmed": 1.00, "provisional": 0.50, "disputed": 0.25}
DIRECTION = {"support": 1.0, "neutral": 0.0, "contradict": -1.0}
PREDICTION_DIRECTION = {"positive", "negative", "two-sided"}
PREDICTION_STATUS = {"open", "met", "failed", "expired", "indeterminate"}
REQUIRED_GATES = {"H1", "H3", "H8"}

CLAIM_REQUIRED_FIELDS = {
    "claim_id",
    "title",
    "gate",
    "mechanism",
    "primary_metric",
    "bullish_condition",
    "bearish_or_falsifying_condition",
    "review_cadence",
    "status",
}
EVIDENCE_REQUIRED_FIELDS = {
    "evidence_id",
    "observed_date",
    "claim_id",
    "direction",
    "weight",
    "quality",
    "fact",
    "interpretation",
    "source",
    "status",
}
PREDICTION_REQUIRED_FIELDS = {
    "prediction_id",
    "claim_id",
    "registered_date",
    "metric",
    "direction",
    "threshold",
    "start_date",
    "evaluation_date",
    "benchmark",
    "failure_condition",
    "status",
}


def clamp(value: float, lo: float = -10.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, value))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def require_columns(rows: list[dict[str, str]], required: set[str], source: Path) -> None:
    if not rows:
        raise ValueError(f"{source}: no data rows")
    columns = set(rows[0].keys())
    missing = required - columns
    if missing:
        raise ValueError(f"{source}: missing required columns {sorted(missing)}")


def require_nonblank(
    row: dict[str, str], fields: set[str], source: Path, row_id: str
) -> None:
    for field in fields:
        if not row.get(field, "").strip():
            raise ValueError(f"{source}: {row_id} has blank {field}")


def require_unique(rows: list[dict[str, str]], field: str, source: Path) -> None:
    seen: set[str] = set()
    for row in rows:
        value = row.get(field, "").strip()
        if not value:
            raise ValueError(f"{source}: blank {field}")
        if value in seen:
            raise ValueError(f"{source}: duplicate {field} {value!r}")
        seen.add(value)


def parse_iso_date(value: str, source: Path, row_id: str, field: str) -> date:
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError(f"{source}: {row_id} has invalid {field} {value!r}") from exc


def validate_web_sources(value: str, source: Path, row_id: str) -> None:
    urls = [item.strip() for item in value.split(";") if item.strip()]
    if not urls:
        raise ValueError(f"{source}: {row_id} has no source URL")
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"{source}: {row_id} has invalid source URL {url!r}")


def normalize_text(value: str) -> str:
    return " ".join(value.split()).strip().lower()


def validate_inputs(
    claims: list[dict[str, str]],
    evidence: list[dict[str, str]],
    predictions: list[dict[str, str]],
    *,
    today: date | None = None,
) -> str:
    today = today or datetime.now(timezone.utc).date()

    require_columns(claims, CLAIM_REQUIRED_FIELDS, CLAIMS)
    require_columns(evidence, EVIDENCE_REQUIRED_FIELDS, EVIDENCE)
    require_columns(predictions, PREDICTION_REQUIRED_FIELDS, PREDICTIONS)

    require_unique(claims, "claim_id", CLAIMS)
    require_unique(evidence, "evidence_id", EVIDENCE)
    require_unique(predictions, "prediction_id", PREDICTIONS)

    claim_ids = {row["claim_id"].strip() for row in claims}

    for row in claims:
        cid = row["claim_id"].strip()
        require_nonblank(row, CLAIM_REQUIRED_FIELDS, CLAIMS, cid)
        gate = row["gate"].strip().lower()
        if gate not in {"true", "false"}:
            raise ValueError(f"{CLAIMS}: {cid} has invalid gate {gate!r}")

    missing_gates = REQUIRED_GATES - claim_ids
    if missing_gates:
        raise ValueError(f"{CLAIMS}: missing required gate claims {sorted(missing_gates)}")
    false_gates = [
        row["claim_id"].strip()
        for row in claims
        if row["claim_id"].strip() in REQUIRED_GATES
        and row["gate"].strip().lower() != "true"
    ]
    if false_gates:
        raise ValueError(f"{CLAIMS}: required gates not marked true {sorted(false_gates)}")

    observed_dates: list[date] = []
    source_fact_pairs: set[tuple[str, str]] = set()

    for row in evidence:
        eid = row["evidence_id"].strip()
        require_nonblank(row, EVIDENCE_REQUIRED_FIELDS, EVIDENCE, eid)

        claim_id = row["claim_id"].strip()
        direction = row["direction"].strip().lower()
        quality = row["quality"].strip().upper()
        status = row["status"].strip().lower()

        if claim_id not in claim_ids:
            raise ValueError(f"{EVIDENCE}: {eid} references unknown claim_id {claim_id!r}")
        if direction not in DIRECTION:
            raise ValueError(f"{EVIDENCE}: {eid} has unknown direction {direction!r}")
        if quality not in QUALITY:
            raise ValueError(f"{EVIDENCE}: {eid} has unknown quality {quality!r}")
        if status not in STATUS:
            raise ValueError(f"{EVIDENCE}: {eid} has unknown status {status!r}")

        try:
            weight = float(row["weight"])
        except ValueError as exc:
            raise ValueError(f"{EVIDENCE}: {eid} has non-numeric weight") from exc
        if not 1.0 <= weight <= 5.0:
            raise ValueError(f"{EVIDENCE}: {eid} weight must be in [1, 5], got {weight}")

        observed = parse_iso_date(row["observed_date"], EVIDENCE, eid, "observed_date")
        if observed > today:
            raise ValueError(f"{EVIDENCE}: {eid} observed_date {observed} is in the future")
        observed_dates.append(observed)

        validate_web_sources(row["source"], EVIDENCE, eid)

        duplicate_key = (normalize_text(row["source"]), normalize_text(row["fact"]))
        if duplicate_key in source_fact_pairs:
            raise ValueError(
                f"{EVIDENCE}: {eid} duplicates an existing exact source+fact observation"
            )
        source_fact_pairs.add(duplicate_key)

    for row in predictions:
        pid = row["prediction_id"].strip()
        require_nonblank(row, PREDICTION_REQUIRED_FIELDS, PREDICTIONS, pid)

        claim_id = row["claim_id"].strip()
        if claim_id not in claim_ids:
            raise ValueError(f"{PREDICTIONS}: {pid} references unknown claim_id {claim_id!r}")

        registered = parse_iso_date(
            row["registered_date"], PREDICTIONS, pid, "registered_date"
        )
        start = parse_iso_date(row["start_date"], PREDICTIONS, pid, "start_date")
        evaluation = parse_iso_date(
            row["evaluation_date"], PREDICTIONS, pid, "evaluation_date"
        )

        if registered > today:
            raise ValueError(
                f"{PREDICTIONS}: {pid} registered_date {registered} is in the future"
            )
        if start < registered:
            raise ValueError(
                f"{PREDICTIONS}: {pid} start_date precedes registered_date"
            )
        if evaluation < start:
            raise ValueError(
                f"{PREDICTIONS}: {pid} evaluation_date precedes start_date"
            )

        direction = row["direction"].strip().lower()
        if direction not in PREDICTION_DIRECTION:
            raise ValueError(
                f"{PREDICTIONS}: {pid} has invalid direction {direction!r}"
            )

        status = row["status"].strip().lower()
        if status not in PREDICTION_STATUS:
            raise ValueError(f"{PREDICTIONS}: {pid} has invalid status {status!r}")

    return max(observed_dates).isoformat()


def evidence_contribution(row: dict[str, str]) -> float:
    return (
        float(row["weight"])
        * DIRECTION[row["direction"].strip().lower()]
        * QUALITY[row["quality"].strip().upper()]
        * STATUS[row["status"].strip().lower()]
    )


def calculate_scores(
    claims: list[dict[str, str]], evidence: list[dict[str, str]]
) -> tuple[
    dict[str, float],
    dict[str, int],
    dict[str, int],
    dict[str, int],
]:
    raw = defaultdict(float)
    support_count = defaultdict(int)
    contradict_count = defaultdict(int)
    neutral_count = defaultdict(int)

    for row in evidence:
        claim_id = row["claim_id"].strip()
        direction = row["direction"].strip().lower()
        raw[claim_id] += evidence_contribution(row)
        if direction == "support":
            support_count[claim_id] += 1
        elif direction == "contradict":
            contradict_count[claim_id] += 1
        else:
            neutral_count[claim_id] += 1

    scores = {row["claim_id"]: clamp(raw[row["claim_id"]]) for row in claims}
    return scores, support_count, contradict_count, neutral_count


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


def strongest_contrary_rows(
    evidence: list[dict[str, str]], gates: set[str], limit: int = 3
) -> list[dict[str, str]]:
    contrary = [
        row for row in evidence if row["direction"].strip().lower() == "contradict"
    ]
    contrary.sort(
        key=lambda row: (
            row["claim_id"].strip() in gates,
            abs(evidence_contribution(row)),
            row["observed_date"].strip(),
            row["evidence_id"].strip(),
        ),
        reverse=True,
    )
    return contrary[:limit]


def render_report(
    claims: list[dict[str, str]],
    evidence: list[dict[str, str]],
    predictions: list[dict[str, str]],
) -> str:
    cutoff = validate_inputs(claims, evidence, predictions)
    scores, support_count, contradict_count, neutral_count = calculate_scores(
        claims, evidence
    )
    gates = [row["claim_id"] for row in claims if row["gate"].strip().lower() == "true"]
    gate_set = set(gates)
    classification = classify(scores, gates)

    lines = [
        "# XRP Thesis — Latest Deterministic Score",
        "",
        f"Evidence cutoff: {cutoff}",
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
            "This section is generated deterministically from explicit `contradict` rows, with gating claims ranked first. "
            "It preserves source-grounded contrary evidence in automated reports.",
            "",
        ]
    )

    contrary = strongest_contrary_rows(evidence, gate_set)
    if contrary:
        for row in contrary:
            cid = row["claim_id"].strip()
            gate_label = " gate" if cid in gate_set else ""
            contribution = evidence_contribution(row)
            lines.append(
                f"- **{row['evidence_id']} — {cid}{gate_label} ({contribution:+.2f} weighted):** "
                f"{row['fact'].strip()} "
                f"**Interpretation:** {row['interpretation'].strip()} "
                f"**Source:** {row['source'].strip()}"
            )
    else:
        lines.append("- No explicit `contradict` evidence rows are currently recorded.")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if reports/latest-score.md is missing or stale relative to the committed research state.",
    )
    args = parser.parse_args()

    claims = load_csv(CLAIMS)
    evidence = load_csv(EVIDENCE)
    predictions = load_csv(PREDICTIONS)
    rendered = render_report(claims, evidence, predictions)

    if args.check:
        current = REPORT.read_text(encoding="utf-8") if REPORT.exists() else ""
        if current != rendered:
            print(
                "reports/latest-score.md is stale or inconsistent with claims/evidence/predictions",
                file=sys.stderr,
            )
            raise SystemExit(1)
        print("Research state is internally consistent.")
        return

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(rendered, encoding="utf-8")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
