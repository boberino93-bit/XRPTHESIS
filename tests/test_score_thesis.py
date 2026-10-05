from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import score_thesis  # noqa: E402


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
        result = score_thesis.classify(scores, {"H1", "H3", "H8"})
        self.assertEqual(result, "Weakening — XRP-specific value capture is negative")

    def test_strengthening_requires_all_gates(self) -> None:
        scores = {"H1": 3.0, "H2": 8.0, "H3": 3.0, "H8": 1.99}
        result = score_thesis.classify(scores, {"H1", "H3", "H8"})
        self.assertTrue(result.startswith("Mixed / insufficient"))

        scores["H8"] = 3.0
        result = score_thesis.classify(scores, {"H1", "H3", "H8"})
        self.assertTrue(result.startswith("Strengthening"))

    def test_gate_contradiction_ranks_above_gate_neutral(self) -> None:
        evidence = [
            {
                "evidence_id": "E-NEUTRAL",
                "claim_id": "H3",
                "direction": "neutral",
                "weight": "5",
                "quality": "A",
                "status": "confirmed",
            },
            {
                "evidence_id": "E-CONTRA",
                "claim_id": "H3",
                "direction": "contradict",
                "weight": "2",
                "quality": "B",
                "status": "confirmed",
            },
        ]
        strongest = score_thesis.strongest_adverse_evidence(
            evidence, {"H1", "H3", "H8"}
        )
        self.assertIsNotNone(strongest)
        self.assertEqual(strongest["evidence_id"], "E-CONTRA")

    def test_report_is_deterministic_for_same_ledger(self) -> None:
        claims = [
            {"claim_id": "H3", "title": "XRP-specific value capture"},
        ]
        evidence = [
            {
                "evidence_id": "E1",
                "observed_date": "2026-10-05",
                "claim_id": "H3",
                "direction": "contradict",
                "weight": "2",
                "quality": "A",
                "status": "confirmed",
                "fact": "Fact.",
                "interpretation": "Interpretation.",
                "source": "https://example.com/source",
            }
        ]
        scores = {"H3": -2.0}
        counts = {
            "support": {"H3": 0},
            "contradict": {"H3": 1},
            "neutral": {"H3": 0},
        }
        first = score_thesis.build_report(
            claims, evidence, scores, counts, {"H3"}
        )
        second = score_thesis.build_report(
            claims, evidence, scores, counts, {"H3"}
        )
        self.assertEqual(first, second)
        self.assertNotIn("Generated:", first)


if __name__ == "__main__":
    unittest.main()
