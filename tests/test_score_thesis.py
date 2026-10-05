from __future__ import annotations

import importlib.util
import unittest
from datetime import date
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "score_thesis.py"
SPEC = importlib.util.spec_from_file_location("score_thesis", MODULE_PATH)
score_thesis = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(score_thesis)


def claim(cid: str, gate: bool = False) -> dict[str, str]:
    return {
        "claim_id": cid,
        "title": cid,
        "gate": "true" if gate else "false",
        "mechanism": "mechanism",
        "primary_metric": "metric",
        "bullish_condition": "bullish",
        "bearish_or_falsifying_condition": "bearish",
        "review_cadence": "monthly",
        "status": "open",
    }


def evidence(
    eid: str,
    cid: str,
    direction: str = "support",
    weight: str = "1",
    quality: str = "A",
    status: str = "confirmed",
    fact: str | None = None,
) -> dict[str, str]:
    return {
        "evidence_id": eid,
        "observed_date": "2026-10-05",
        "claim_id": cid,
        "direction": direction,
        "weight": weight,
        "quality": quality,
        "fact": fact or f"fact {eid}",
        "interpretation": f"interpretation {eid}",
        "source": f"https://example.com/{eid}",
        "status": status,
    }


def prediction(pid: str, cid: str) -> dict[str, str]:
    return {
        "prediction_id": pid,
        "claim_id": cid,
        "registered_date": "2026-10-05",
        "metric": "metric",
        "direction": "positive",
        "threshold": "threshold",
        "start_date": "2026-10-05",
        "evaluation_date": "2027-10-05",
        "benchmark": "benchmark",
        "failure_condition": "failure",
        "status": "open",
        "result": "",
    }


class ScoreMathTests(unittest.TestCase):
    def test_quality_and_status_multipliers(self) -> None:
        row = evidence(
            "E1", "H3", direction="support", weight="4", quality="B", status="provisional"
        )
        self.assertAlmostEqual(score_thesis.evidence_contribution(row), 1.6)

    def test_score_clamping(self) -> None:
        claims = [claim("H1", True)]
        rows = [evidence(f"E{i}", "H1", weight="5", quality="A") for i in range(3)]
        scores, *_ = score_thesis.calculate_scores(claims, rows)
        self.assertEqual(scores["H1"], 10.0)

    def test_negative_h3_gate_weakens(self) -> None:
        scores = {"H1": 3.0, "H2": 4.0, "H3": -2.1, "H8": 3.0}
        result = score_thesis.classify(scores, ["H1", "H3", "H8"])
        self.assertIn("Weakening", result)
        self.assertIn("XRP-specific", result)

    def test_strengthening_requires_all_gates(self) -> None:
        positive = {
            "H1": 3.0,
            "H2": 3.0,
            "H3": 3.0,
            "H4": 3.0,
            "H5": 3.0,
            "H6": 3.0,
            "H7": 3.0,
            "H8": 3.0,
        }
        self.assertIn(
            "Strengthening", score_thesis.classify(positive, ["H1", "H3", "H8"])
        )
        positive["H8"] = 1.9
        self.assertNotIn(
            "Strengthening", score_thesis.classify(positive, ["H1", "H3", "H8"])
        )


class ValidationTests(unittest.TestCase):
    def base_state(self):
        claims = [claim("H1", True), claim("H3", True), claim("H8", True)]
        rows = [evidence("E1", "H3")]
        predictions = [prediction("P1", "H3")]
        return claims, rows, predictions

    def test_unknown_claim_id_fails(self) -> None:
        claims, rows, predictions = self.base_state()
        rows[0]["claim_id"] = "H99"
        with self.assertRaisesRegex(ValueError, "unknown claim_id"):
            score_thesis.validate_inputs(
                claims, rows, predictions, today=date(2026, 10, 5)
            )

    def test_malformed_weight_fails(self) -> None:
        claims, rows, predictions = self.base_state()
        rows[0]["weight"] = "9"
        with self.assertRaisesRegex(ValueError, r"weight must be in \[1, 5\]"):
            score_thesis.validate_inputs(
                claims, rows, predictions, today=date(2026, 10, 5)
            )

    def test_duplicate_source_fact_fails(self) -> None:
        claims, rows, predictions = self.base_state()
        duplicate = evidence("E2", "H3", fact=rows[0]["fact"])
        duplicate["source"] = rows[0]["source"]
        rows.append(duplicate)
        with self.assertRaisesRegex(
            ValueError, "duplicates an existing exact source\\+fact"
        ):
            score_thesis.validate_inputs(
                claims, rows, predictions, today=date(2026, 10, 5)
            )

    def test_prediction_window_must_be_coherent(self) -> None:
        claims, rows, predictions = self.base_state()
        predictions[0]["start_date"] = "2027-10-05"
        predictions[0]["evaluation_date"] = "2026-10-05"
        with self.assertRaisesRegex(ValueError, "evaluation_date precedes start_date"):
            score_thesis.validate_inputs(
                claims, rows, predictions, today=date(2026, 10, 5)
            )


if __name__ == "__main__":
    unittest.main()
