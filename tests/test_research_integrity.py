from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.score_thesis import calculate_scores, classify, clamp, render_report
from scripts.validate_research_data import (
    CLAIMS_FIELDS,
    EVIDENCE_FIELDS,
    PREDICTION_FIELDS,
    ValidationError,
    validate_all,
    validate_evidence,
)


class ScoreTests(unittest.TestCase):
    def test_clamp(self) -> None:
        self.assertEqual(clamp(11.0), 10.0)
        self.assertEqual(clamp(-11.0), -10.0)
        self.assertEqual(clamp(2.5), 2.5)

    def test_quality_and_status_multipliers(self) -> None:
        claims = [
            {"claim_id": "H1", "gate": "true", "title": "H1"},
            {"claim_id": "H3", "gate": "true", "title": "H3"},
            {"claim_id": "H8", "gate": "true", "title": "H8"},
        ]
        evidence = [
            {
                "evidence_id": "E1",
                "claim_id": "H3",
                "direction": "support",
                "weight": "4",
                "quality": "B",
                "status": "provisional",
                "observed_date": "2026-01-01",
                "fact": "x",
                "source": "https://example.com",
            }
        ]
        scores, *_ = calculate_scores(claims, evidence)
        self.assertAlmostEqual(scores["H3"], 1.6)

    def test_negative_h3_gate_forces_weakening(self) -> None:
        scores = {"H1": 4.0, "H3": -2.0, "H8": 4.0, "H2": 8.0}
        self.assertEqual(
            classify(scores, ["H1", "H3", "H8"]),
            "Weakening — XRP-specific value capture is negative",
        )

    def test_strengthening_requires_all_gates(self) -> None:
        self.assertTrue(
            classify({"H1": 3.0, "H3": 3.0, "H8": 0.0}, ["H1", "H3", "H8"]).startswith(
                "Mixed"
            )
        )
        self.assertTrue(
            classify({"H1": 2.0, "H3": 2.0, "H8": 2.0}, ["H1", "H3", "H8"]).startswith(
                "Strengthening"
            )
        )

    def test_report_is_deterministic_for_same_ledger(self) -> None:
        claims = [
            {"claim_id": "H1", "gate": "true", "title": "Bridge"},
            {"claim_id": "H3", "gate": "true", "title": "Capture"},
            {"claim_id": "H8", "gate": "true", "title": "Valuation"},
        ]
        evidence = [
            {
                "evidence_id": "E1",
                "observed_date": "2026-01-01",
                "claim_id": "H3",
                "direction": "contradict",
                "weight": "2",
                "quality": "A",
                "status": "confirmed",
                "fact": "A source-grounded contrary observation.",
                "source": "https://example.com/e1",
            }
        ]
        self.assertEqual(render_report(claims, evidence), render_report(claims, evidence))
        self.assertIn("A source-grounded contrary observation.", render_report(claims, evidence))


class ValidatorTests(unittest.TestCase):
    def _write_csv(self, path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _valid_claims(self) -> list[dict[str, str]]:
        rows = []
        for cid in ("H1", "H3", "H8"):
            rows.append(
                {
                    "claim_id": cid,
                    "title": cid,
                    "gate": "true",
                    "mechanism": "mechanism",
                    "primary_metric": "metric",
                    "bullish_condition": "bullish",
                    "bearish_or_falsifying_condition": "bearish",
                    "review_cadence": "monthly",
                    "status": "open",
                }
            )
        return rows

    def _valid_evidence(self) -> list[dict[str, str]]:
        return [
            {
                "evidence_id": "E1",
                "observed_date": "2020-01-01",
                "claim_id": "H1",
                "direction": "support",
                "weight": "2",
                "quality": "A",
                "fact": "fact",
                "interpretation": "interpretation",
                "source": "https://example.com/evidence",
                "status": "confirmed",
            }
        ]

    def _valid_predictions(self) -> list[dict[str, str]]:
        return [
            {
                "prediction_id": "P1",
                "claim_id": "H3",
                "registered_date": "2020-01-01",
                "metric": "metric",
                "direction": "positive",
                "threshold": "threshold",
                "start_date": "2020-01-01",
                "evaluation_date": "2030-01-01",
                "benchmark": "benchmark",
                "failure_condition": "failure",
                "status": "open",
                "result": "",
            }
        ]

    def test_valid_minimal_ledger_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "data"
            data.mkdir()
            self._write_csv(data / "claims.csv", CLAIMS_FIELDS, self._valid_claims())
            self._write_csv(data / "evidence.csv", EVIDENCE_FIELDS, self._valid_evidence())
            self._write_csv(data / "predictions.csv", PREDICTION_FIELDS, self._valid_predictions())
            validate_all(root)

    def test_unknown_claim_fails_loudly(self) -> None:
        rows = self._valid_evidence()
        rows[0]["claim_id"] = "H999"
        with self.assertRaisesRegex(ValidationError, "unknown claim_id"):
            validate_evidence(rows, {"H1", "H3", "H8"})

    def test_malformed_weight_fails_loudly(self) -> None:
        rows = self._valid_evidence()
        rows[0]["weight"] = "not-a-number"
        with self.assertRaisesRegex(ValidationError, "weight must be numeric"):
            validate_evidence(rows, {"H1", "H3", "H8"})

    def test_duplicate_evidence_id_fails_loudly(self) -> None:
        rows = self._valid_evidence() * 2
        with self.assertRaisesRegex(ValidationError, "duplicate evidence_id"):
            validate_evidence(rows, {"H1", "H3", "H8"})


if __name__ == "__main__":
    unittest.main()
