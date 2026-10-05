from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "score_thesis", ROOT / "scripts" / "score_thesis.py"
)
assert SPEC and SPEC.loader
score_thesis = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score_thesis)


class ScoreThesisTests(unittest.TestCase):
    def test_gate_neutral_outweighs_non_gate_contradiction_for_adverse_summary(self) -> None:
        evidence = [
            {
                "evidence_id": "E-H4",
                "claim_id": "H4",
                "direction": "contradict",
                "weight": "5",
                "quality": "A",
                "status": "confirmed",
                "fact": "Non-gating regulatory contradiction.",
                "interpretation": "Weakens H4.",
                "source": "https://example.com/h4",
            },
            {
                "evidence_id": "E-H3",
                "claim_id": "H3",
                "direction": "neutral",
                "weight": "4",
                "quality": "A",
                "status": "confirmed",
                "fact": "XRPL production usage did not require user XRP exposure.",
                "interpretation": "Leaves the value-capture gate unproven.",
                "source": "https://example.com/h3",
            },
        ]

        strongest = score_thesis.strongest_adverse_evidence(evidence, {"H1", "H3", "H8"})

        self.assertIsNotNone(strongest)
        self.assertEqual(strongest["evidence_id"], "E-H3")

    def test_gate_contradiction_ranks_above_gate_neutral(self) -> None:
        evidence = [
            {
                "evidence_id": "E-NEUTRAL",
                "claim_id": "H3",
                "direction": "neutral",
                "weight": "5",
                "quality": "A",
                "status": "confirmed",
                "fact": "Gate remains unproven.",
                "interpretation": "Neutral.",
                "source": "https://example.com/neutral",
            },
            {
                "evidence_id": "E-CONTRA",
                "claim_id": "H3",
                "direction": "contradict",
                "weight": "2",
                "quality": "B",
                "status": "confirmed",
                "fact": "Evidence directly contradicts the gate.",
                "interpretation": "Negative.",
                "source": "https://example.com/contra",
            },
        ]

        strongest = score_thesis.strongest_adverse_evidence(evidence, {"H1", "H3", "H8"})

        self.assertIsNotNone(strongest)
        self.assertEqual(strongest["evidence_id"], "E-CONTRA")


if __name__ == "__main__":
    unittest.main()
