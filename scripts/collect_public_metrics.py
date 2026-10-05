#!/usr/bin/env python3
"""Collect a small, reproducible public-data snapshot for XRPTHESIS.

The collector intentionally gathers facts only. It does not create evidence rows,
change claim scores, forecast prices, or issue trade instructions.
"""

from __future__ import annotations

import json
import statistics
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "data" / "snapshots"
USER_AGENT = "XRPTHESIS-research-monitor/1.0"
TIMEOUT = 20


def get_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def capture(name: str, fn, errors: dict[str, str]):
    try:
        return fn()
    except Exception as exc:  # preserve partial snapshots rather than hiding outages
        errors[name] = f"{type(exc).__name__}: {exc}"
        return None


def coinbase_price() -> dict[str, Any]:
    data = get_json("https://api.coinbase.com/v2/prices/XRP-USD/spot")
    return {
        "usd": float(data["data"]["amount"]),
        "source": "https://api.coinbase.com/v2/prices/XRP-USD/spot",
    }


def kraken_price() -> dict[str, Any]:
    data = get_json("https://api.kraken.com/0/public/Ticker?pair=XRPUSD")
    if data.get("error"):
        raise RuntimeError(str(data["error"]))
    result = data["result"]
    if not result:
        raise RuntimeError("Kraken returned an empty ticker result")
    ticker = next(iter(result.values()))
    return {
        "usd": float(ticker["c"][0]),
        "source": "https://api.kraken.com/0/public/Ticker?pair=XRPUSD",
    }


def xrpl_validated_ledger() -> dict[str, Any]:
    payload = {
        "method": "ledger",
        "params": [{"ledger_index": "validated", "transactions": False, "expand": False}],
    }
    endpoints = [
        "https://s1.ripple.com:51234/",
        "https://s2.ripple.com:51234/",
    ]
    last_error: Exception | None = None
    for endpoint in endpoints:
        try:
            data = post_json(endpoint, payload)
            result = data["result"]
            if result.get("status") != "success":
                raise RuntimeError(f"XRPL status: {result.get('status')}")
            ledger = result["ledger"]
            return {
                "ledger_index": int(ledger["ledger_index"]),
                "close_time": ledger.get("close_time"),
                "total_coins_drops": int(ledger["total_coins"]),
                "total_xrp": int(ledger["total_coins"]) / 1_000_000,
                "source": endpoint,
            }
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"All XRPL endpoints failed: {last_error}")


def main() -> None:
    now = datetime.now(timezone.utc)
    errors: dict[str, str] = {}

    coinbase = capture("coinbase", coinbase_price, errors)
    kraken = capture("kraken", kraken_price, errors)
    ledger = capture("xrpl_ledger", xrpl_validated_ledger, errors)

    observed_prices = [
        item["usd"] for item in (coinbase, kraken) if isinstance(item, dict) and "usd" in item
    ]

    snapshot = {
        "schema_version": 1,
        "observed_at_utc": now.isoformat(timespec="seconds"),
        "market": {
            "xrp_usd_coinbase": coinbase,
            "xrp_usd_kraken": kraken,
            "xrp_usd_median": statistics.median(observed_prices) if observed_prices else None,
        },
        "xrpl": ledger,
        "errors": errors,
        "research_note": (
            "Raw telemetry only. Price and ledger snapshots do not independently support or contradict "
            "the investment thesis and must not be treated as trading signals."
        ),
    }

    if not observed_prices and ledger is None:
        raise RuntimeError(f"No public source succeeded: {errors}")

    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOTS / f"{now:%Y-%m-%d}.json"
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {path}")
    if errors:
        print("Partial-source errors:")
        for name, error in errors.items():
            print(f"- {name}: {error}")


if __name__ == "__main__":
    main()
