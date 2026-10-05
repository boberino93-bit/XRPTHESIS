from __future__ import annotations

import copy
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import score_thesis  # noqa: E402

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


def claims() -> list[dict[str, str]]:
    return [claim("H1", True), claim("H2", False), claim("H3", True), claim("H8", True)]


def evidence() -> list[dict[str, str]]:
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


def predictions() -> list[dict[str, str]]:
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


class ScoreThesisTests(unittest.TestCase):
    def test_quality_and_status_multipliers(self) -> None:
        row = {
            "direction": "support",
            "weight": "5",
            "quality": "B",
            "status": "provisional",
        }
        self.assertEqual(score_thesis.evidence_contribution(row), 2.0)

    def test_score_clamping(self) -> None:
        self.assertEqual(score_thesis.clamp(14.0), 10.0)
        self.assertEqual(score_thesis.clamp(-14.0), -10.0)
        self.assertEqual(score_thesis.clamp(1.25), 1.25)

    def test_negative_h3_forces_weakening(self) -> None:
        scores = {"H1": 3.0, "H2": 8.0, "H3": -2.0, "H8": 3.0}
        result = score_thesis.classify(scores, ["H1", "H3", "H8"])
        self.assertEqual(result, "Weakening — XRP-specific value capture is negative")

    def test_strengthening_requires_all_gates(self) -> None:
        scores = {"H1": 3.0, "H2": 8.0, "H3": 3.0, "H8": 1.99}
        self.assertTrue(
            score_thesis.classify(scores, ["H1", "H3", "H8"]).startswith(
                "Mixed / insufficient"
            )
        )
        scores["H8"] = 3.0
        self.assertTrue(
            score_thesis.classify(scores, ["H1", "H3", "H8"]).startswith(
                "Strengthening"
            )
        )

    def test_unknown_claim_id_fails_loudly(self) -> None:
        rows = evidence()
        rows[0]["claim_id"] = "H99"
        with self.assertRaises(ValueError):
            score_thesis.validate_inputs(claims(), rows, predictions(), today=TODAY)

    def test_blank_required_field_fails_loudly(self) -> None:
        rows = evidence()
        rows[0]["fact"] = ""
        with self.assertRaises(ValueError):
            score_thesis.validate_inputs(claims(), rows, predictions(), today=TODAY)

    def test_duplicate_source_fact_fails_loudly(self) -> None:
        rows = evidence()
        duplicate = copy.deepcopy(rows[0])
        duplicate["evidence_id"] = "E2"
        rows.append(duplicate)
        with self.assertRaises(ValueError):
            score_thesis.validate_inputs(claims(), rows, predictions(), today=TODAY)

    def test_prediction_dates_must_be_coherent(self) -> None:
        rows = predictions()
        rows[0]["evaluation_date"] = "2026-10-04"
        with self.assertRaises(ValueError):
            score_thesis.validate_inputs(claims(), evidence(), rows, today=TODAY)

    def test_report_render_is_reproducible(self) -> None:
        first = score_thesis.render_report(claims(), evidence(), predictions())
        second = score_thesis.render_report(claims(), evidence(), predictions())
        self.assertEqual(first, second)
        self.assertNotIn("Generated:", first)


if __name__ == "__main__":
    unittest.main()
