#!/usr/bin/env python3
"""Extract conservative H1 bridge-utility observations from validated XRPL ledgers.

This script is a measurement scaffold, not a thesis scorer. It intentionally does
not infer executed routing from submitted Paths and does not convert route counts
into economic value. The first pass classifies validated Payment execution using
consumed Offer state in transaction metadata; AMM reconstruction remains a
separate required step before aggregate bridge-share claims are made.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

USER_AGENT = "XRPTHESIS-h1-bridge-research/0.1"
TIMEOUT = 30
RIPPLE_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)
DEFAULT_ENDPOINTS = (
    "https://s1.ripple.com:51234/",
    "https://s2.ripple.com:51234/",
)


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def request_with_fallback(endpoints: Iterable[str], payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for endpoint in endpoints:
        try:
            data = post_json(endpoint, payload)
            result = data.get("result", {})
            if data.get("status") == "success" or result.get("status") == "success":
                return data
            errors.append(f"{endpoint}: status={data.get('status') or result.get('status')}")
        except Exception as exc:  # preserve endpoint failures for the caller
            errors.append(f"{endpoint}: {type(exc).__name__}: {exc}")
    raise RuntimeError("All XRPL endpoints failed: " + " | ".join(errors))


def amount_asset(amount: Any) -> str | None:
    if isinstance(amount, str):
        return "XRP"
    if not isinstance(amount, dict):
        return None
    if amount.get("mpt_issuance_id"):
        return f"MPT:{amount['mpt_issuance_id']}"
    currency = amount.get("currency")
    issuer = amount.get("issuer")
    if currency == "XRP":
        return "XRP"
    if not currency:
        return None
    return f"{currency}:{issuer or '?'}"


def amount_value(amount: Any) -> Decimal | None:
    try:
        if isinstance(amount, str):
            return Decimal(amount) / Decimal(1_000_000)
        if isinstance(amount, dict) and "value" in amount:
            return Decimal(str(amount["value"]))
    except (InvalidOperation, ValueError):
        return None
    return None


def xrp_in_submitted_paths(paths: Any) -> bool:
    if not isinstance(paths, list):
        return False
    for path in paths:
        if not isinstance(path, list):
            continue
        for step in path:
            if isinstance(step, dict) and step.get("currency") == "XRP":
                return True
    return False


def node_payload(node: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    for kind in ("ModifiedNode", "DeletedNode", "CreatedNode"):
        payload = node.get(kind)
        if isinstance(payload, dict):
            return kind, payload
    return None, {}


def positive_amount_delta(before: Any, after: Any) -> tuple[str, str] | None:
    before_asset = amount_asset(before)
    after_asset = amount_asset(after)
    if not before_asset or before_asset != after_asset:
        return None
    before_value = amount_value(before)
    after_value = amount_value(after)
    if before_value is None or after_value is None:
        return None
    delta = before_value - after_value
    if delta <= 0:
        return None
    return before_asset, format(delta, "f")


def extract_consumed_offers(meta: dict[str, Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for wrapper in meta.get("AffectedNodes", []):
        if not isinstance(wrapper, dict):
            continue
        kind, node = node_payload(wrapper)
        if kind not in {"ModifiedNode", "DeletedNode"}:
            continue
        if node.get("LedgerEntryType") != "Offer":
            continue

        previous = node.get("PreviousFields") or {}
        final = node.get("FinalFields") or {}
        if not isinstance(previous, dict) or not isinstance(final, dict):
            continue

        gets_delta = None
        pays_delta = None
        if "TakerGets" in previous and "TakerGets" in final:
            gets_delta = positive_amount_delta(previous["TakerGets"], final["TakerGets"])
        if "TakerPays" in previous and "TakerPays" in final:
            pays_delta = positive_amount_delta(previous["TakerPays"], final["TakerPays"])

        # A deleted Offer without positive amount deltas may be cancellation,
        # expiry, unfunded cleanup, or otherwise not safely attributable to trade.
        if not gets_delta and not pays_delta:
            continue

        before_gets = previous.get("TakerGets", final.get("TakerGets"))
        before_pays = previous.get("TakerPays", final.get("TakerPays"))
        asset_gets = amount_asset(before_gets)
        asset_pays = amount_asset(before_pays)
        if not asset_gets or not asset_pays:
            continue

        observations.append(
            {
                "node_kind": kind,
                "ledger_index": node.get("LedgerIndex"),
                "asset_gets": asset_gets,
                "asset_pays": asset_pays,
                "gets_consumed": gets_delta[1] if gets_delta else None,
                "pays_consumed": pays_delta[1] if pays_delta else None,
                "uses_xrp": "XRP" in {asset_gets, asset_pays},
            }
        )
    return observations


def has_amm_object_change(meta: dict[str, Any]) -> bool:
    for wrapper in meta.get("AffectedNodes", []):
        if not isinstance(wrapper, dict):
            continue
        _, node = node_payload(wrapper)
        if node.get("LedgerEntryType") == "AMM":
            return True
    return False


def classify_payment(tx: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any] | None:
    if tx.get("TransactionType") != "Payment":
        return None
    if meta.get("TransactionResult") != "tesSUCCESS":
        return None

    deliver_max = tx.get("DeliverMax", tx.get("Amount"))
    delivered = meta.get("delivered_amount", meta.get("DeliveredAmount", deliver_max))
    send_max = tx.get("SendMax")

    destination_asset = amount_asset(delivered) or amount_asset(deliver_max)
    source_asset = amount_asset(send_max) if send_max is not None else destination_asset
    delivered_value = amount_value(delivered)

    if not source_asset or not destination_asset:
        return None

    cross_currency = source_asset != destination_asset
    consumed_offers = extract_consumed_offers(meta)
    xrp_offers = [row for row in consumed_offers if row["uses_xrp"]]
    non_xrp_offers = [row for row in consumed_offers if not row["uses_xrp"]]

    source_xrp_leg = any(
        {row["asset_gets"], row["asset_pays"]} == {source_asset, "XRP"}
        for row in xrp_offers
    )
    destination_xrp_leg = any(
        {row["asset_gets"], row["asset_pays"]} == {destination_asset, "XRP"}
        for row in xrp_offers
    )
    bridge_candidate = (
        cross_currency
        and source_asset != "XRP"
        and destination_asset != "XRP"
        and source_xrp_leg
        and destination_xrp_leg
    )

    if not cross_currency:
        if destination_asset == "XRP":
            route_class = "direct_xrp_settlement"
            confidence = "high"
        else:
            route_class = "same_asset_payment"
            confidence = "high"
    elif "XRP" in {source_asset, destination_asset}:
        route_class = "xrp_endpoint_conversion"
        confidence = "high"
    elif bridge_candidate and non_xrp_offers:
        route_class = "mixed_xrp_bridge_candidate"
        confidence = "medium"
    elif bridge_candidate:
        route_class = "xrp_bridge_candidate"
        confidence = "medium"
    elif xrp_offers:
        route_class = "partial_xrp_liquidity_candidate"
        confidence = "low"
    elif non_xrp_offers:
        route_class = "non_xrp_offer_liquidity_observed"
        confidence = "low"
    else:
        route_class = "indeterminate_cross_currency"
        confidence = "none"

    return {
        "source_asset": source_asset,
        "destination_asset": destination_asset,
        "delivered_value": format(delivered_value, "f") if delivered_value is not None else None,
        "cross_currency": cross_currency,
        "route_class": route_class,
        "classification_confidence": confidence,
        "submitted_path_mentions_xrp": xrp_in_submitted_paths(tx.get("Paths")),
        "consumed_offer_count": len(consumed_offers),
        "xrp_offer_leg_count": len(xrp_offers),
        "non_xrp_offer_leg_count": len(non_xrp_offers),
        "amm_object_changed": has_amm_object_change(meta),
        "amm_reconstruction_needed": (
            cross_currency and source_asset != "XRP" and destination_asset != "XRP"
        ),
        "consumed_offers": consumed_offers,
    }


def normalize_expanded_transaction(item: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    tx = item.get("tx_json")
    meta = item.get("meta") or item.get("metaData")
    if isinstance(tx, dict) and isinstance(meta, dict):
        return tx, meta

    # Compatibility with older expanded-ledger response shapes where the
    # transaction fields are at the top level and metadata is attached.
    if isinstance(meta, dict):
        tx = {k: v for k, v in item.items() if k not in {"meta", "metaData", "validated"}}
        return tx, meta
    return {}, {}


def fetch_ledger(ledger_index: int, endpoints: Iterable[str]) -> dict[str, Any]:
    payload = {
        "method": "ledger",
        "params": [
            {
                "ledger_index": ledger_index,
                "transactions": True,
                "expand": True,
                "binary": False,
                "api_version": 2,
            }
        ],
    }
    data = request_with_fallback(endpoints, payload)
    result = data["result"]
    ledger = result.get("ledger", result)
    if not isinstance(ledger, dict):
        raise RuntimeError(f"Ledger {ledger_index}: malformed response")
    return ledger


def ripple_time_to_iso(close_time: Any) -> str | None:
    if close_time is None:
        return None
    try:
        return (RIPPLE_EPOCH + timedelta(seconds=int(close_time))).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def scan_ledgers(start: int, end: int, endpoints: Iterable[str], sleep_s: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ledger_index in range(start, end + 1):
        ledger = fetch_ledger(ledger_index, endpoints)
        close_time_iso = ripple_time_to_iso(ledger.get("close_time"))
        for item in ledger.get("transactions", []):
            if not isinstance(item, dict):
                continue
            tx, meta = normalize_expanded_transaction(item)
            observation = classify_payment(tx, meta)
            if observation is None:
                continue
            observation.update(
                {
                    "ledger_index": ledger_index,
                    "close_time_iso": close_time_iso,
                    "transaction_hash": tx.get("hash") or item.get("hash"),
                }
            )
            rows.append(observation)
        if sleep_s > 0 and ledger_index < end:
            time.sleep(sleep_s)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "ledger_index",
        "close_time_iso",
        "transaction_hash",
        "source_asset",
        "destination_asset",
        "delivered_value",
        "cross_currency",
        "route_class",
        "classification_confidence",
        "submitted_path_mentions_xrp",
        "consumed_offer_count",
        "xrp_offer_leg_count",
        "non_xrp_offer_leg_count",
        "amm_object_changed",
        "amm_reconstruction_needed",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fields})


def write_summary(path: Path, rows: list[dict[str, Any]], start: int, end: int) -> None:
    classes = Counter(row["route_class"] for row in rows)
    corridors = Counter(
        f"{row['source_asset']}->{row['destination_asset']}"
        for row in rows
        if row["cross_currency"]
    )
    summary = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ledger_start": start,
        "ledger_end": end,
        "payment_observations": len(rows),
        "route_class_counts": dict(sorted(classes.items())),
        "cross_currency_corridor_counts": dict(sorted(corridors.items())),
        "interpretation_guardrail": (
            "Counts are diagnostic only and are not H1 evidence. Aggregate bridge share is withheld "
            "until AMM/mixed-path reconstruction and corridor-level economic-value attribution are validated."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-ledger", type=int, required=True)
    parser.add_argument("--end-ledger", type=int, required=True)
    parser.add_argument(
        "--endpoint",
        action="append",
        dest="endpoints",
        help="XRPL JSON-RPC endpoint; repeat to provide fallbacks",
    )
    parser.add_argument("--out-prefix", type=Path, required=True)
    parser.add_argument("--sleep", type=float, default=0.05, help="Seconds between ledger requests")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.start_ledger < 1 or args.end_ledger < args.start_ledger:
        raise SystemExit("Invalid ledger range")
    endpoints = tuple(args.endpoints or DEFAULT_ENDPOINTS)
    rows = scan_ledgers(args.start_ledger, args.end_ledger, endpoints, args.sleep)
    write_jsonl(args.out_prefix.with_suffix(".jsonl"), rows)
    write_csv(args.out_prefix.with_suffix(".csv"), rows)
    write_summary(args.out_prefix.with_name(args.out_prefix.name + "-summary.json"), rows, args.start_ledger, args.end_ledger)
    print(f"Wrote {len(rows)} Payment observations for ledgers {args.start_ledger}-{args.end_ledger}")


if __name__ == "__main__":
    main()
