# H1 Bridge-Utility Measurement Methodology — 2026-10-05

## Work item

- **WORK_ITEM:** Issue #7 — H1 bridge-routing and direct-settlement utility
- **OWNER:** researcher / H1 bridge-telemetry lane
- **COOPERATING_AGENTS:** manager; H3 value-capture lane
- **DEPENDENCIES:** validated XRPL ledger history; later AMM reconstruction and corridor-level normalization
- **WRITE_SCOPE:** `research/bridge_utility/`, `scripts/measure_h1_bridge_utility.py`; no thesis-score changes in this pass
- **STATUS:** active — methodology + extraction scaffold

## Research question

Does economically meaningful XRPL cross-currency settlement actually route through XRP, or is XRP mostly a technically available option while direct token/stablecoin routes carry the flow?

This lane deliberately does **not** infer executed XRP use from submitted `Paths`, Ripple/XRPL product adoption, or transaction counts.

## Source-grounded protocol facts

1. A Payment can include multiple candidate paths, and the server chooses which paths to use at execution time. Submitted paths are therefore not executed-route evidence.
   - https://xrpl.org/docs/references/protocol/transactions/types/payment
   - https://xrpl.org/docs/concepts/tokens/fungible-tokens/paths

2. Validated transaction metadata describes the actual ledger-state changes caused by the transaction. `AffectedNodes` identifies ledger objects that were created, modified, or deleted, and `delivered_amount` records the amount actually received for successful Payments.
   - https://xrpl.org/docs/references/protocol/transactions/metadata

3. Cross-currency Payments consume existing Offers but do not create Offer objects. Offer state stores remaining `TakerPays` and `TakerGets`, so changes in those fields are direct evidence that order-book liquidity was consumed.
   - https://xrpl.org/docs/concepts/tokens/decentralized-exchange/offers
   - https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/offer

4. OfferCreate crossing can automatically use XRP as an intermediary through auto-bridging. Payment transactions do not auto-bridge by default in the same way, but pathfinding can submit paths with the same economic effect.
   - https://xrpl.org/docs/concepts/tokens/decentralized-exchange/autobridging

5. AMMs are separate liquidity sources and have a special account holding pool assets. `amm_info` can resolve an AMM by its special account, but Payment metadata does not expose a simple one-field statement saying how much of a mixed payment executed through each AMM/order-book path.
   - https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/amm
   - https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/path-and-order-book-methods/amm_info

## Core methodological finding

### Submitted paths are unusable as the primary H1 metric

A transaction can submit several paths and use only some of them, or split execution across several liquidity sources. Therefore:

```text
XRP appears in Paths != XRP was economically used
```

The H1 dataset must be reconstructed from validated execution metadata and balance/offer changes.

### Transaction count is also insufficient

One $50 equivalent payment and one $5,000,000 equivalent payment cannot carry equal weight. The primary metric must be economic value.

However, summing raw destination amounts across unrelated currencies is invalid. The first defensible metric is therefore **corridor-level bridge share**, where numerator and denominator are both denominated in the same destination asset:

```text
bridge_share(corridor, month)
  = destination units attributable to XRP-mediated execution
    / total destination units for cross-currency payments in that corridor
```

A global value-weighted bridge share should be added only after an independently sourced numeraire-conversion layer exists.

## Route classification hierarchy

The extraction scaffold emits observations rather than thesis evidence.

### A. Direct XRP settlement

Successful Payment with XRP as both source and destination asset and no cross-currency conversion.

This measures direct XRP transfer value, not bridge use.

### B. XRP endpoint conversion

Cross-currency Payment where the source or destination asset itself is XRP.

This is economically real XRP usage but is not an intermediate bridge between two non-XRP assets.

### C. XRP bridge candidate from consumed Offers

Both source and destination are non-XRP and metadata shows consumed Offer liquidity for:

```text
source asset <-> XRP
XRP <-> destination asset
```

If non-XRP direct Offers are also consumed, the transaction is marked **mixed**. The full delivered amount must not be attributed to XRP.

### D. Non-XRP liquidity observed

Cross-currency Payment consumes Offer liquidity but no XRP leg is observed.

This is potential bypass evidence, but should not be called definitive bypass until AMM/trust-line execution is reconstructed.

### E. Indeterminate

Cross-currency Payment has insufficient order-book metadata to classify the executed route. This bucket is intentionally preserved rather than forced into bullish or bearish evidence.

## Offer-consumption reconstruction

For an `Offer` node in `AffectedNodes`:

- `FinalFields.TakerGets` / `TakerPays` represent remaining amounts after execution (or immediately before deletion for a deleted node).
- `PreviousFields` contains changed prior values where available.
- A positive decrease in matching `TakerGets` / `TakerPays` is evidence that the Offer was consumed.

The extraction code treats only positive, asset-consistent deltas as consumption. Offer deletion by cancellation, expiry, or unfunded cleanup must not be misclassified as trade volume.

## Known limitation: AMM route reconstruction

The first scanner pass is intentionally conservative. It can classify consumed order-book Offers but does **not yet** claim complete route attribution for AMM execution.

AMM swaps can change the AMM special account and trust-line balances without producing a simple per-path volume field. A complete H1 measurement therefore needs a second-stage resolver that:

1. identifies AMM special accounts touched by a Payment,
2. resolves each AMM's asset pair at the relevant validated ledger,
3. reconstructs pool-side balance deltas,
4. separates pool trading from AMM deposit/withdraw/governance activity,
5. combines AMM and Offer liquidity when a Payment splits across both.

Until this is implemented and fixture-validated, aggregate XRP bridge share is **withheld** rather than guessed.

## False-positive controls

The dataset must not count any of the following as executed XRP bridge value:

- XRP merely appearing in submitted `Paths`;
- transaction fees paid in XRP;
- account reserve changes;
- Offers deleted only because they were expired/unfunded;
- XRPL activity whose source/destination assets never require XRP;
- the entire delivered value of a mixed direct + XRP-mediated payment;
- Ripple Payments or RLUSD volume without ledger-level XRP execution evidence.

## Proposed transaction-level output

Each successful Payment should emit at minimum:

- ledger index / close time
- transaction hash
- source asset
- destination asset
- delivered amount
- cross-currency boolean
- submitted-path-mentions-XRP diagnostic boolean
- consumed Offer legs and asset pairs
- observed XRP Offer-leg count
- observed non-XRP Offer-leg count
- route class
- classification confidence
- AMM-reconstruction-needed boolean

## Validation plan

Before any H1 evidence row is added:

1. Validate parser behavior on synthetic fixtures for direct, bridged, mixed, deleted-unfunded, and partial-payment cases.
2. Validate against known public XRPL transactions where the executed route can be independently reconstructed.
3. Add AMM-account resolution and balance-delta reconstruction.
4. Produce at least one monthly corridor dataset.
5. Compute corridor-level value share, not transaction-count share.
6. Search for the strongest bypass corridors and include them even if they weaken H1.

## Current thesis impact

**No score change in this pass.**

This work changes the measurement standard, not the evidence state. H1 remains mechanism-supported but empirically unresolved until executed-route value is measured.
