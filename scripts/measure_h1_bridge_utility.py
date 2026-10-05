#!/usr/bin/env python3
"""Measure conservative H1 bridge-utility observations from validated XRPL ledgers.

This collector is deliberately narrower than the H1 claim. It classifies executed
Payment metadata from consumed Offer state, streams observations to durable JSONL,
and supports exactly-once resume at ledger boundaries. It does not infer execution
from submitted Paths and it does not turn transaction counts into economic value.

AMM/mixed-path reconstruction and corridor-level value normalization are still
required before this project can publish an aggregate XRP bridge-share estimate.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Iterator

USER_AGENT = "XRPTHESIS-h1-bridge-research/0.2"
TIMEOUT = 30
RIPPLE_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)
DEFAULT_ENDPOINTS = (
    "https://s1.ripple.com:51234/",
    "https://s2.ripple.com:51234/",
)
CSV_FIELDS = [
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


def request_with_fallback(
    endpoints: Iterable[str], payload: dict[str, Any]
) -> dict[str, Any]:
    errors: list[str] = []
    for endpoint in endpoints:
        try:
            data = post_json(endpoint, payload)
            result = data.get("result", {})
            if data.get("status") == "success" or result.get("status") == "success":
                return data
            errors.append(
                f"{endpoint}: status={data.get('status') or result.get('status')}"
            )
        except Exception as exc:  # preserve all endpoint failures in final error
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
    """Return Offer-book deltas that are safely consistent with consumption.

    Deleted Offers with no positive amount delta are deliberately ignored because
    cancellation, expiry, unfunded cleanup, and trade consumption are otherwise
    easy to conflate.
    """

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
            gets_delta = positive_amount_delta(
                previous["TakerGets"], final["TakerGets"]
            )
        if "TakerPays" in previous and "TakerPays" in final:
            pays_delta = positive_amount_delta(
                previous["TakerPays"], final["TakerPays"]
            )

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
                "ledger_entry_index": node.get("LedgerIndex"),
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


def classify_payment(
    tx: dict[str, Any], meta: dict[str, Any]
) -> dict[str, Any] | None:
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
    amm_changed = has_amm_object_change(meta)

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
        "delivered_value": (
            format(delivered_value, "f") if delivered_value is not None else None
        ),
        "cross_currency": cross_currency,
        "route_class": route_class,
        "classification_confidence": confidence,
        "submitted_path_mentions_xrp": xrp_in_submitted_paths(tx.get("Paths")),
        "consumed_offer_count": len(consumed_offers),
        "xrp_offer_leg_count": len(xrp_offers),
        "non_xrp_offer_leg_count": len(non_xrp_offers),
        "amm_object_changed": amm_changed,
        "amm_reconstruction_needed": (
            amm_changed
            and cross_currency
            and source_asset != "XRP"
            and destination_asset != "XRP"
        ),
        "consumed_offers": consumed_offers,
    }


def normalize_expanded_transaction(
    item: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    tx = item.get("tx_json")
    meta = item.get("meta") or item.get("metaData")
    if isinstance(tx, dict) and isinstance(meta, dict):
        return tx, meta

    if isinstance(meta, dict):
        tx = {
            key: value
            for key, value in item.items()
            if key not in {"meta", "metaData", "validated"}
        }
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


def observations_from_ledger(
    ledger_index: int, ledger: dict[str, Any]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
    return rows


def initial_checkpoint(start: int, end: int) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "ledger_start": start,
        "ledger_end": end,
        "last_completed_ledger": start - 1,
        "jsonl_bytes": 0,
        "payment_observations": 0,
        "route_class_counts": {},
        "cross_currency_corridor_counts": {},
    }


def load_checkpoint(path: Path, start: int, end: int) -> dict[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Resume requested but checkpoint is missing: {path}") from exc
    if state.get("schema_version") != 1:
        raise RuntimeError("Unsupported H1 checkpoint schema")
    if state.get("ledger_start") != start or state.get("ledger_end") != end:
        raise RuntimeError(
            "Checkpoint ledger range does not match requested --start-ledger/--end-ledger"
        )
    return state


def write_checkpoint_atomic(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def update_checkpoint_counts(state: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    classes = Counter(state.get("route_class_counts", {}))
    corridors = Counter(state.get("cross_currency_corridor_counts", {}))
    for row in rows:
        classes[row["route_class"]] += 1
        if row["cross_currency"]:
            corridors[f"{row['source_asset']}->{row['destination_asset']}"] += 1
    state["payment_observations"] = int(state.get("payment_observations", 0)) + len(rows)
    state["route_class_counts"] = dict(sorted(classes.items()))
    state["cross_currency_corridor_counts"] = dict(sorted(corridors.items()))


def append_ledger_rows(
    handle: Any, rows: list[dict[str, Any]]
) -> int:
    for row in rows:
        payload = (json.dumps(row, sort_keys=True) + "\n").encode("utf-8")
        handle.write(payload)
    handle.flush()
    os.fsync(handle.fileno())
    return handle.tell()


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Malformed JSONL at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise RuntimeError(f"Non-object JSONL row at {path}:{line_number}")
            yield row


def write_csv_from_jsonl(jsonl_path: Path, csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in iter_jsonl(jsonl_path):
            writer.writerow({field: row.get(field) for field in CSV_FIELDS})


def write_summary(path: Path, state: dict[str, Any]) -> None:
    summary = {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ledger_start": state["ledger_start"],
        "ledger_end": state["ledger_end"],
        "last_completed_ledger": state["last_completed_ledger"],
        "payment_observations": state["payment_observations"],
        "route_class_counts": state["route_class_counts"],
        "cross_currency_corridor_counts": state["cross_currency_corridor_counts"],
        "interpretation_guardrail": (
            "Counts are diagnostic only and are not H1 evidence. Aggregate bridge share is withheld "
            "until AMM/mixed-path reconstruction and corridor-level economic-value attribution are validated."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def scan_to_files(
    *,
    start: int,
    end: int,
    endpoints: Iterable[str],
    jsonl_path: Path,
    csv_path: Path,
    summary_path: Path,
    checkpoint_path: Path,
    resume: bool,
    sleep_s: float,
) -> dict[str, Any]:
    if resume:
        state = load_checkpoint(checkpoint_path, start, end)
        if not jsonl_path.exists():
            raise RuntimeError(f"Resume requested but JSONL output is missing: {jsonl_path}")
        mode = "r+b"
    else:
        state = initial_checkpoint(start, end)
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "w+b"

    with jsonl_path.open(mode) as handle:
        if resume:
            committed_bytes = int(state.get("jsonl_bytes", 0))
            handle.truncate(committed_bytes)
            handle.seek(committed_bytes)
        next_ledger = max(start, int(state["last_completed_ledger"]) + 1)

        for ledger_index in range(next_ledger, end + 1):
            ledger = fetch_ledger(ledger_index, endpoints)
            rows = observations_from_ledger(ledger_index, ledger)

            committed_bytes = append_ledger_rows(handle, rows)
            update_checkpoint_counts(state, rows)
            state["last_completed_ledger"] = ledger_index
            state["jsonl_bytes"] = committed_bytes
            write_checkpoint_atomic(checkpoint_path, state)

            if sleep_s > 0 and ledger_index < end:
                time.sleep(sleep_s)

    write_csv_from_jsonl(jsonl_path, csv_path)
    write_summary(summary_path, state)
    return state


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
    parser.add_argument(
        "--checkpoint",
        type=Path,
        help="Checkpoint path; defaults to <out-prefix>.checkpoint.json",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume exactly after the last committed ledger in the checkpoint",
    )
    parser.add_argument(
        "--sleep", type=float, default=0.05, help="Seconds between ledger requests"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.start_ledger < 1 or args.end_ledger < args.start_ledger:
        raise SystemExit("Invalid ledger range")
    if args.sleep < 0:
        raise SystemExit("--sleep must be non-negative")

    endpoints = tuple(args.endpoints or DEFAULT_ENDPOINTS)
    jsonl_path = args.out_prefix.with_suffix(".jsonl")
    csv_path = args.out_prefix.with_suffix(".csv")
    summary_path = args.out_prefix.with_name(args.out_prefix.name + "-summary.json")
    checkpoint_path = args.checkpoint or args.out_prefix.with_name(
        args.out_prefix.name + ".checkpoint.json"
    )

    state = scan_to_files(
        start=args.start_ledger,
        end=args.end_ledger,
        endpoints=endpoints,
        jsonl_path=jsonl_path,
        csv_path=csv_path,
        summary_path=summary_path,
        checkpoint_path=checkpoint_path,
        resume=args.resume,
        sleep_s=args.sleep,
    )
    print(
        f"Completed ledgers {args.start_ledger}-{state['last_completed_ledger']}; "
        f"wrote {state['payment_observations']} Payment observations"
    )


if __name__ == "__main__":
    main()
