#!/usr/bin/env python3
"""Validate XRPTHESIS research data before scoring or telemetry writes."""

from __future__ import annotations

import csv
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "data" / "claims.csv"
EVIDENCE = ROOT / "data" / "evidence.csv"
PREDICTIONS = ROOT / "data" / "predictions.csv"

QUALITY = {"A", "B", "C", "D"}
EVIDENCE_STATUS = {"confirmed", "provisional", "disputed"}
EVIDENCE_DIRECTION = {"support", "neutral", "contradict"}
PREDICTION_DIRECTION = {"positive", "negative", "neutral"}
PREDICTION_STATUS = {"open", "passed", "failed", "expired", "indeterminate"}
REQUIRED_GATE_CLAIMS = {"H1", "H3", "H8"}
CLAIM_ID_RE = re.compile(r"^H[1-9][0-9]*$")


class DataValidationError(ValueError):
    """Raised when committed research data violates the project schema."""


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require_fields(row: dict[str, str], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if not (row.get(field) or "").strip()]
    if missing:
        raise DataValidationError(f"{label} missing required fields: {', '.join(missing)}")


def parse_iso_date(value: str, label: str) -> date:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise DataValidationError(f"{label} must use YYYY-MM-DD: {value!r}") from exc


def validate_web_url(value: str, label: str) -> None:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise DataValidationError(f"{label} must be an http(s) URL: {value!r}")


def ensure_unique(value: str, seen: set[str], label: str) -> None:
    if value in seen:
        raise DataValidationError(f"Duplicate {label} {value!r}")
    seen.add(value)


def validate_claims(claims: list[dict[str, str]]) -> tuple[set[str], set[str]]:
    required = (
        "claim_id",
        "title",
        "gate",
        "mechanism",
        "primary_metric",
        "bullish_condition",
        "bearish_or_falsifying_condition",
        "review_cadence",
        "status",
    )
    claim_ids: set[str] = set()
    gates: set[str] = set()

    for index, row in enumerate(claims, start=2):
        label = f"claims.csv row {index}"
        require_fields(row, required, label)
        claim_id = row["claim_id"].strip()
        ensure_unique(claim_id, claim_ids, "claim_id")
        if not CLAIM_ID_RE.fullmatch(claim_id):
            raise DataValidationError(f"Invalid claim_id {claim_id!r}")

        gate = row["gate"].strip().lower()
        if gate not in {"true", "false"}:
            raise DataValidationError(f"{label} gate must be true or false")
        if gate == "true":
            gates.add(claim_id)

    missing_gates = REQUIRED_GATE_CLAIMS - gates
    if missing_gates:
        raise DataValidationError(
            "Required scoring gates missing or not marked gate=true: "
            + ", ".join(sorted(missing_gates))
        )

    return claim_ids, gates


def validate_evidence(
    evidence: list[dict[str, str]], claim_ids: set[str], today: date
) -> None:
    required = (
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
    )
    evidence_ids: set[str] = set()
    source_fact_pairs: set[tuple[str, str]] = set()

    for index, row in enumerate(evidence, start=2):
        label = f"evidence.csv row {index}"
        require_fields(row, required, label)

        evidence_id = row["evidence_id"].strip()
        ensure_unique(evidence_id, evidence_ids, "evidence_id")

        claim_id = row["claim_id"].strip()
        if claim_id not in claim_ids:
            raise DataValidationError(f"Unknown claim_id {claim_id!r} in {evidence_id}")

        observed = parse_iso_date(row["observed_date"], f"{evidence_id}.observed_date")
        if observed > today:
            raise DataValidationError(f"{evidence_id}.observed_date is in the future")

        direction = row["direction"].strip().lower()
        if direction not in EVIDENCE_DIRECTION:
            raise DataValidationError(f"Unknown direction {direction!r} in {evidence_id}")

        quality = row["quality"].strip().upper()
        if quality not in QUALITY:
            raise DataValidationError(f"Unknown quality {quality!r} in {evidence_id}")

        status = row["status"].strip().lower()
        if status not in EVIDENCE_STATUS:
            raise DataValidationError(f"Unknown status {status!r} in {evidence_id}")

        try:
            weight = float(row["weight"])
        except ValueError as exc:
            raise DataValidationError(f"Non-numeric weight in {evidence_id}") from exc
        if not 1.0 <= weight <= 5.0:
            raise DataValidationError(f"Weight must be between 1 and 5 in {evidence_id}")

        source = row["source"].strip()
        validate_web_url(source, f"{evidence_id}.source")
        source_fact = (source, row["fact"].strip())
        if source_fact in source_fact_pairs:
            raise DataValidationError(
                f"Duplicate source+fact evidence detected in {evidence_id}; "
                "record materially distinct observations instead"
            )
        source_fact_pairs.add(source_fact)


def validate_predictions(
    predictions: list[dict[str, str]], claim_ids: set[str], today: date
) -> None:
    required = (
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
    )
    prediction_ids: set[str] = set()

    for index, row in enumerate(predictions, start=2):
        label = f"predictions.csv row {index}"
        require_fields(row, required, label)

        prediction_id = row["prediction_id"].strip()
        ensure_unique(prediction_id, prediction_ids, "prediction_id")

        claim_id = row["claim_id"].strip()
        if claim_id not in claim_ids:
            raise DataValidationError(f"Unknown claim_id {claim_id!r} in {prediction_id}")

        registered = parse_iso_date(
            row["registered_date"], f"{prediction_id}.registered_date"
        )
        start = parse_iso_date(row["start_date"], f"{prediction_id}.start_date")
        evaluation = parse_iso_date(
            row["evaluation_date"], f"{prediction_id}.evaluation_date"
        )

        if registered > today:
            raise DataValidationError(f"{prediction_id}.registered_date is in the future")
        if registered > start:
            raise DataValidationError(
                f"{prediction_id} start_date precedes registered_date"
            )
        if evaluation < start:
            raise DataValidationError(
                f"{prediction_id} evaluation_date precedes start_date"
            )

        direction = row["direction"].strip().lower()
        if direction not in PREDICTION_DIRECTION:
            raise DataValidationError(
                f"Unknown prediction direction {direction!r} in {prediction_id}"
            )

        status = row["status"].strip().lower()
        if status not in PREDICTION_STATUS:
            raise DataValidationError(
                f"Unknown prediction status {status!r} in {prediction_id}"
            )


def validate_all(
    claims: list[dict[str, str]],
    evidence: list[dict[str, str]],
    predictions: list[dict[str, str]],
    *,
    today: date | None = None,
) -> tuple[set[str], set[str]]:
    effective_today = today or datetime.now(timezone.utc).date()
    claim_ids, gates = validate_claims(claims)
    validate_evidence(evidence, claim_ids, effective_today)
    validate_predictions(predictions, claim_ids, effective_today)
    return claim_ids, gates


def main() -> None:
    claims = load_csv(CLAIMS)
    evidence = load_csv(EVIDENCE)
    predictions = load_csv(PREDICTIONS)
    claim_ids, gates = validate_all(claims, evidence, predictions)
    print(
        "Validated "
        f"{len(claim_ids)} claims, {len(evidence)} evidence rows, "
        f"{len(predictions)} predictions; gates={','.join(sorted(gates))}"
    )


if __name__ == "__main__":
    main()
