from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import measure_h1_bridge_utility as h1  # noqa: E402


USD = {"currency": "USD", "issuer": "rUSD"}
EUR = {"currency": "EUR", "issuer": "rEUR"}


def issued(asset: dict[str, str], value: str) -> dict[str, str]:
    return {**asset, "value": value}


def modified_offer(gets_before, gets_after, pays_before, pays_after):
    return {
        "ModifiedNode": {
            "LedgerEntryType": "Offer",
            "LedgerIndex": "ABC",
            "PreviousFields": {
                "TakerGets": gets_before,
                "TakerPays": pays_before,
            },
            "FinalFields": {
                "TakerGets": gets_after,
                "TakerPays": pays_after,
            },
        }
    }


def bridge_tx(hash_value: str = "TX1"):
    tx = {
        "TransactionType": "Payment",
        "hash": hash_value,
        "Amount": issued(EUR, "45"),
        "SendMax": issued(USD, "100"),
    }
    meta = {
        "TransactionResult": "tesSUCCESS",
        "delivered_amount": issued(EUR, "45"),
        "AffectedNodes": [
            modified_offer(
                issued(USD, "100"), issued(USD, "90"), "50000000", "45000000"
            ),
            modified_offer(
                "50000000", "45000000", issued(EUR, "50"), issued(EUR, "45")
            ),
        ],
    }
    return tx, meta


def expanded_ledger(index: int) -> dict:
    tx, meta = bridge_tx(f"TX{index}")
    return {
        "close_time": index,
        "transactions": [{"tx_json": tx, "meta": meta}],
    }


class H1BridgeUtilityTests(unittest.TestCase):
    def test_xrp_amount_is_converted_from_drops(self) -> None:
        self.assertEqual(str(h1.amount_value("1250000")), "1.25")
        self.assertEqual(h1.amount_asset("1250000"), "XRP")

    def test_classifies_two_offer_xrp_bridge_candidate(self) -> None:
        tx, meta = bridge_tx()
        result = h1.classify_payment(tx, meta)
        self.assertIsNotNone(result)
        self.assertEqual(result["route_class"], "xrp_bridge_candidate")
        self.assertEqual(result["classification_confidence"], "medium")
        self.assertEqual(result["xrp_offer_leg_count"], 2)
        self.assertFalse(result["amm_object_changed"])
        self.assertFalse(result["amm_reconstruction_needed"])

    def test_amm_reconstruction_is_flagged_only_when_amm_state_changed(self) -> None:
        tx, meta = bridge_tx()
        meta["AffectedNodes"].append(
            {
                "ModifiedNode": {
                    "LedgerEntryType": "AMM",
                    "LedgerIndex": "AMM1",
                    "PreviousFields": {},
                    "FinalFields": {},
                }
            }
        )
        result = h1.classify_payment(tx, meta)
        self.assertIsNotNone(result)
        self.assertTrue(result["amm_object_changed"])
        self.assertTrue(result["amm_reconstruction_needed"])

    def test_direct_xrp_payment_is_not_called_a_bridge(self) -> None:
        tx = {
            "TransactionType": "Payment",
            "hash": "DIRECT",
            "Amount": "1000000",
        }
        meta = {
            "TransactionResult": "tesSUCCESS",
            "delivered_amount": "1000000",
            "AffectedNodes": [],
        }
        result = h1.classify_payment(tx, meta)
        self.assertIsNotNone(result)
        self.assertEqual(result["route_class"], "direct_xrp_settlement")
        self.assertEqual(result["delivered_value"], "1")

    def test_failed_payment_is_excluded(self) -> None:
        tx, meta = bridge_tx()
        meta["TransactionResult"] = "tecPATH_DRY"
        self.assertIsNone(h1.classify_payment(tx, meta))

    def test_resume_truncates_uncheckpointed_output_and_continues_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            jsonl = root / "scan.jsonl"
            csv_path = root / "scan.csv"
            summary = root / "scan-summary.json"
            checkpoint = root / "scan.checkpoint.json"

            with patch.object(
                h1,
                "fetch_ledger",
                side_effect=[expanded_ledger(1), RuntimeError("simulated interruption")],
            ):
                with self.assertRaises(RuntimeError):
                    h1.scan_to_files(
                        start=1,
                        end=3,
                        endpoints=("https://example.invalid",),
                        jsonl_path=jsonl,
                        csv_path=csv_path,
                        summary_path=summary,
                        checkpoint_path=checkpoint,
                        resume=False,
                        sleep_s=0,
                    )

            state = json.loads(checkpoint.read_text(encoding="utf-8"))
            self.assertEqual(state["last_completed_ledger"], 1)
            committed_bytes = state["jsonl_bytes"]

            with jsonl.open("ab") as handle:
                handle.write(b'{"stale":true}\n')
            self.assertGreater(jsonl.stat().st_size, committed_bytes)

            with patch.object(
                h1,
                "fetch_ledger",
                side_effect=[expanded_ledger(2), expanded_ledger(3)],
            ):
                final_state = h1.scan_to_files(
                    start=1,
                    end=3,
                    endpoints=("https://example.invalid",),
                    jsonl_path=jsonl,
                    csv_path=csv_path,
                    summary_path=summary,
                    checkpoint_path=checkpoint,
                    resume=True,
                    sleep_s=0,
                )

            rows = list(h1.iter_jsonl(jsonl))
            self.assertEqual([row["ledger_index"] for row in rows], [1, 2, 3])
            self.assertEqual(final_state["payment_observations"], 3)
            self.assertEqual(final_state["last_completed_ledger"], 3)
            self.assertTrue(csv_path.exists())
            self.assertTrue(summary.exists())


if __name__ == "__main__":
    unittest.main()
