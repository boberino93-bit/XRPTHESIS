from __future__ import annotations

import copy
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_data  # noqa: E402


TODAY = date(2026, 10, 5)


def claim(claim_id: str, gate: bool) -> dict[str, str]:
    return {
        "claim_id": claim_id,
        "title": f"Claim {claim_id}",
        "gate": "true" if gate else "false",
        "mechanism": "Mechanism",
        "primary_metric": "Metric",
        "bullish_condition": "Bullish condition",
        "bearish_or_falsifying_condition": "Bearish condition",
        "review_cadence": "monthly",
        "status": "open",
    }


def baseline_claims() -> list[dict[str, str]]:
    return [claim("H1", True), claim("H2", False), claim("H3", True), claim("H8", True)]


def baseline_evidence() -> list[dict[str, str]]:
    return [
        {
            "evidence_id": "E1",
            "observed_date": "2026-10-05",
            "claim_id": "H3",
            "direction": "neutral",
            "weight": "4",
            "quality": "A",
            "fact": "A source-grounded fact.",
            "interpretation": "An interpretation.",
            "source": "https://example.com/evidence",
            "status": "confirmed",
        }
    ]


def baseline_predictions() -> list[dict[str, str]]:
    return [
        {
            "prediction_id": "P1",
            "claim_id": "H3",
            "registered_date": "2026-10-05",
            "metric": "Metric",
            "direction": "positive",
            "threshold": "Threshold",
            "start_date": "2026-10-05",
            "evaluation_date": "2027-10-05",
            "benchmark": "Benchmark",
            "failure_condition": "Failure condition",
            "status": "open",
            "result": "",
        }
    ]


class ValidateDataTests(unittest.TestCase):
    def test_valid_baseline_passes(self) -> None:
        claim_ids, gates = validate_data.validate_all(
            baseline_claims(), baseline_evidence(), baseline_predictions(), today=TODAY
        )
        self.assertEqual(claim_ids, {"H1", "H2", "H3", "H8"})
        self.assertEqual(gates, {"H1", "H3", "H8"})

    def test_unknown_claim_id_fails_loudly(self) -> None:
        evidence = baseline_evidence()
        evidence[0]["claim_id"] = "H99"
        with self.assertRaises(validate_data.DataValidationError):
            validate_data.validate_all(
                baseline_claims(), evidence, baseline_predictions(), today=TODAY
            )

    def test_missing_required_field_fails_loudly(self) -> None:
        evidence = baseline_evidence()
        evidence[0]["fact"] = ""
        with self.assertRaises(validate_data.DataValidationError):
            validate_data.validate_all(
                baseline_claims(), evidence, baseline_predictions(), today=TODAY
            )

    def test_invalid_weight_fails_loudly(self) -> None:
        evidence = baseline_evidence()
        evidence[0]["weight"] = "6"
        with self.assertRaises(validate_data.DataValidationError):
            validate_data.validate_all(
                baseline_claims(), evidence, baseline_predictions(), today=TODAY
            )

    def test_duplicate_evidence_id_fails_loudly(self) -> None:
        evidence = baseline_evidence()
        duplicate = copy.deepcopy(evidence[0])
        duplicate["source"] = "https://example.com/other"
        duplicate["fact"] = "A distinct fact."
        evidence.append(duplicate)
        with self.assertRaises(validate_data.DataValidationError):
            validate_data.validate_all(
                baseline_claims(), evidence, baseline_predictions(), today=TODAY
            )

    def test_duplicate_source_fact_fails_loudly(self) -> None:
        evidence = baseline_evidence()
        duplicate = copy.deepcopy(evidence[0])
        duplicate["evidence_id"] = "E2"
        evidence.append(duplicate)
        with self.assertRaises(validate_data.DataValidationError):
            validate_data.validate_all(
                baseline_claims(), evidence, baseline_predictions(), today=TODAY
            )

    def test_prediction_date_order_is_enforced(self) -> None:
        predictions = baseline_predictions()
        predictions[0]["evaluation_date"] = "2026-10-04"
        with self.assertRaises(validate_data.DataValidationError):
            validate_data.validate_all(
                baseline_claims(), baseline_evidence(), predictions, today=TODAY
            )

    def test_required_gates_must_exist_and_be_marked_gate(self) -> None:
        claims = baseline_claims()
        claims[-1]["gate"] = "false"
        with self.assertRaises(validate_data.DataValidationError):
            validate_data.validate_all(
                claims, baseline_evidence(), baseline_predictions(), today=TODAY
            )


if __name__ == "__main__":
    unittest.main()
