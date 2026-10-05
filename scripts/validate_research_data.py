#!/usr/bin/env python3
"""Validate XRPTHESIS research ledgers before scoring or automation writes.

The validator intentionally uses only the Python standard library so it can run
in local development and GitHub Actions without dependency installation.
"""

from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

CLAIMS_FIELDS = [
    "claim_id",
    "title",
    "gate",
    "mechanism",
    "primary_metric",
    "bullish_condition",
    "bearish_or_falsifying_condition",
    "review_cadence",
    "status",
]
EVIDENCE_FIELDS = [
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
]
PREDICTION_FIELDS = [
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
    "result",
]

EVIDENCE_DIRECTIONS = {"support", "neutral", "contradict"}
EVIDENCE_QUALITY = {"A", "B", "C", "D"}
EVIDENCE_STATUS = {"confirmed", "provisional", "disputed"}
PREDICTION_DIRECTIONS = {"positive", "negative", "neutral"}
PREDICTION_STATUS = {"open", "met", "failed", "expired", "indeterminate"}
REQUIRED_GATES = {"H1", "H3", "H8"}
ALLOWED_URL_SCHEMES = {"http", "https"}


class ValidationError(ValueError):
    """Raised when one or more ledger integrity rules fail."""


def read_csv(path: Path, expected_fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise ValidationError(f"Missing required file: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != expected_fields:
            raise ValidationError(
                f"{path}: schema mismatch. Expected {expected_fields!r}, got {reader.fieldnames!r}"
            )
        return list(reader)


def require_nonempty(row: dict[str, str], fields: list[str], context: str) -> None:
    missing = [field for field in fields if not (row.get(field) or "").strip()]
    if missing:
        raise ValidationError(f"{context}: required fields are empty: {', '.join(missing)}")


def require_unique(rows: list[dict[str, str]], field: str, context: str) -> None:
    seen: set[str] = set()
    for row in rows:
        value = (row.get(field) or "").strip()
        if not value:
            raise ValidationError(f"{context}: empty {field}")
        if value in seen:
            raise ValidationError(f"{context}: duplicate {field} {value!r}")
        seen.add(value)


def parse_iso_date(value: str, context: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{context}: invalid ISO date {value!r}") from exc


def validate_source_urls(value: str, context: str) -> None:
    urls = [part.strip() for part in value.split(";") if part.strip()]
    if not urls:
        raise ValidationError(f"{context}: source must contain at least one URL")
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES or not parsed.netloc:
            raise ValidationError(f"{context}: invalid source URL {url!r}")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def validate_claims(rows: list[dict[str, str]]) -> set[str]:
    require_unique(rows, "claim_id", "claims.csv")
    ids: set[str] = set()
    gates: set[str] = set()
    for row in rows:
        cid = row["claim_id"].strip()
        require_nonempty(row, CLAIMS_FIELDS, f"claims.csv:{cid}")
        gate = row["gate"].strip().lower()
        if gate not in {"true", "false"}:
            raise ValidationError(f"claims.csv:{cid}: gate must be true/false, got {row['gate']!r}")
        ids.add(cid)
        if gate == "true":
            gates.add(cid)
    missing_gates = REQUIRED_GATES - gates
    if missing_gates:
        raise ValidationError(f"claims.csv: required scoring gates missing/not enabled: {sorted(missing_gates)}")
    return ids


def validate_evidence(rows: list[dict[str, str]], claim_ids: set[str]) -> None:
    require_unique(rows, "evidence_id", "evidence.csv")
    duplicate_facts: set[tuple[str, str, str]] = set()
    today = date.today()

    for row in rows:
        eid = row["evidence_id"].strip()
        require_nonempty(row, EVIDENCE_FIELDS, f"evidence.csv:{eid}")
        claim_id = row["claim_id"].strip()
        if claim_id not in claim_ids:
            raise ValidationError(f"evidence.csv:{eid}: unknown claim_id {claim_id!r}")

        observed = parse_iso_date(row["observed_date"].strip(), f"evidence.csv:{eid}")
        if observed > today:
            raise ValidationError(f"evidence.csv:{eid}: observed_date {observed} is in the future")

        direction = row["direction"].strip().lower()
        quality = row["quality"].strip().upper()
        status = row["status"].strip().lower()
        if direction not in EVIDENCE_DIRECTIONS:
            raise ValidationError(f"evidence.csv:{eid}: invalid direction {direction!r}")
        if quality not in EVIDENCE_QUALITY:
            raise ValidationError(f"evidence.csv:{eid}: invalid quality {quality!r}")
        if status not in EVIDENCE_STATUS:
            raise ValidationError(f"evidence.csv:{eid}: invalid status {status!r}")

        try:
            weight = float(row["weight"])
        except ValueError as exc:
            raise ValidationError(f"evidence.csv:{eid}: weight must be numeric") from exc
        if not 1.0 <= weight <= 5.0:
            raise ValidationError(f"evidence.csv:{eid}: weight {weight} outside allowed range 1-5")

        validate_source_urls(row["source"].strip(), f"evidence.csv:{eid}")
        fingerprint = (
            claim_id,
            normalize_text(row["fact"]),
            normalize_text(row["source"]),
        )
        if fingerprint in duplicate_facts:
            raise ValidationError(
                f"evidence.csv:{eid}: duplicate claim/source/fact observation; merge or explicitly differentiate it"
            )
        duplicate_facts.add(fingerprint)


def validate_predictions(rows: list[dict[str, str]], claim_ids: set[str]) -> None:
    require_unique(rows, "prediction_id", "predictions.csv")
    required = [field for field in PREDICTION_FIELDS if field != "result"]
    today = date.today()

    for row in rows:
        pid = row["prediction_id"].strip()
        require_nonempty(row, required, f"predictions.csv:{pid}")
        claim_id = row["claim_id"].strip()
        if claim_id not in claim_ids:
            raise ValidationError(f"predictions.csv:{pid}: unknown claim_id {claim_id!r}")

        registered = parse_iso_date(row["registered_date"].strip(), f"predictions.csv:{pid}")
        start = parse_iso_date(row["start_date"].strip(), f"predictions.csv:{pid}")
        evaluation = parse_iso_date(row["evaluation_date"].strip(), f"predictions.csv:{pid}")
        if registered > today:
            raise ValidationError(f"predictions.csv:{pid}: registered_date {registered} is in the future")
        if start < registered:
            raise ValidationError(f"predictions.csv:{pid}: start_date precedes registered_date")
        if evaluation < start:
            raise ValidationError(f"predictions.csv:{pid}: evaluation_date precedes start_date")

        direction = row["direction"].strip().lower()
        status = row["status"].strip().lower()
        if direction not in PREDICTION_DIRECTIONS:
            raise ValidationError(f"predictions.csv:{pid}: invalid direction {direction!r}")
        if status not in PREDICTION_STATUS:
            raise ValidationError(f"predictions.csv:{pid}: invalid status {status!r}")
        if status == "open" and row["result"].strip():
            raise ValidationError(f"predictions.csv:{pid}: open prediction must not already contain a result")
        if status != "open" and not row["result"].strip():
            raise ValidationError(f"predictions.csv:{pid}: closed prediction requires a result")


def validate_all(root: Path = ROOT) -> None:
    data = root / "data"
    claims = read_csv(data / "claims.csv", CLAIMS_FIELDS)
    evidence = read_csv(data / "evidence.csv", EVIDENCE_FIELDS)
    predictions = read_csv(data / "predictions.csv", PREDICTION_FIELDS)

    claim_ids = validate_claims(claims)
    validate_evidence(evidence, claim_ids)
    validate_predictions(predictions, claim_ids)


if __name__ == "__main__":
    validate_all()
    print("Research data validation passed.")
