# H1 Executed XRP Bridge-Route Measurement Specification

Date: 2026-10-05
Role: research workstream
Primary claim: H1 — Bridge-asset utility
Secondary relevance: H3 — XRP-specific value capture
Status: methodology locked for first empirical implementation; no thesis-score change from this note alone

## Research question

What share of economically meaningful XRPL cross-asset execution actually uses XRP as an intermediary liquidity asset, rather than merely having XRP available as a possible route?

The objective is to measure **executed XRP bridge usage**, not technical capability, submitted path options, transaction counts, or generic XRPL activity.

## Source-grounded findings

### 1. XRP auto-bridging is a real protocol mechanism

Official XRPL documentation states that token-to-token DEX execution can use XRP as an intermediary when doing so is cheaper than direct token-to-token execution. Offer execution can combine direct and XRP-bridged liquidity. Cross-currency payments can achieve the same token→XRP→token effect.

Primary sources:
- https://xrpl.org/docs/concepts/tokens/decentralized-exchange/autobridging
- https://xrpl.org/docs/concepts/payment-types/cross-currency-payments

This establishes mechanism existence, not economic scale.

### 2. Submitted paths are not executed paths

A Payment can provide multiple candidate paths, and the ledger can combine liquidity from different sources. The submitted `Paths` field therefore describes allowed possibilities, not a reliable record of which route supplied the executed liquidity.

Primary source:
- https://xrpl.org/docs/concepts/tokens/fungible-tokens/paths

**Research rule:** never label a transaction `xrp_bridged=true` merely because XRP appears in a submitted path or because an XRP route was available during pathfinding.

### 3. Validated transaction metadata is the execution record

XRPL transaction metadata describes the ledger entries actually created, modified, or deleted by a transaction. `AffectedNodes` is therefore the primary execution-level input. For Payments, `delivered_amount` is the canonical delivered amount and avoids the partial-payment error of assuming the requested Amount was delivered.

Primary source:
- https://xrpl.org/docs/references/protocol/transactions/metadata

**Research rule:** only analyze successful transactions in validated ledgers and use `delivered_amount` for Payment destination value.

### 4. Cross-currency Payments consume DEX liquidity

Official Payment documentation says cross-currency Payments consume offers to connect different currencies and can traverse multiple paths. The source asset is represented by `SendMax` for true cross-currency / cross-issue payments; the destination asset is `Amount` / `DeliverMax`.

Primary source:
- https://xrpl.org/docs/references/protocol/transactions/types/payment

This provides a transaction-level definition of the source/destination asset pair before executed-liquidity reconstruction.

### 5. Offer and AMM liquidity must both be considered

XRPL DEX execution can consume order-book Offers, AMMs, or a combination of both. Cross-currency payments and OfferCreate execution are therefore not fully measured if the classifier only looks at Offer ledger entries.

Primary sources:
- https://xrpl.org/docs/concepts/tokens/decentralized-exchange/offers
- https://xrpl.org/docs/concepts/tokens/decentralized-exchange/automated-market-makers
- https://xrpl.org/docs/references/protocol/ledger-data/ledger-entry-types/amm

### 6. `book_changes` is useful but insufficient for bridge attribution

`book_changes` reports order-book volume and OHLC-style changes per ledger and identifies XRP-token and token-token books. It is excellent for independent DEX-volume/depth telemetry.

However, because it aggregates book activity at the ledger level rather than linking both legs to one economic execution, it cannot by itself distinguish:

- an XRP/token trade that was one leg of token→XRP→token auto-bridging,
- from an unrelated direct XRP/token trade in the same ledger.

Primary source:
- https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/path-and-order-book-methods/book_changes

Therefore `book_changes` must be a **cross-check / liquidity panel**, not the primary H1 bridge classifier.

## Measurement universe

Build two separate panels so different economic behaviors are not silently mixed.

### Panel A — cross-currency Payment execution

Include validated successful `Payment` transactions where source asset and delivered destination asset differ by currency or issuer.

Track separately:
- account-to-account cross-currency Payments,
- circular/currency-conversion Payments where `Account == Destination`,
- partial vs non-partial Payments,
- permissioned-domain executions where present.

Exclude from bridge-share denominator:
- XRP→XRP direct transfers,
- same-asset direct token transfers,
- failed transactions,
- MPT v1 direct transfers that cannot participate in the DEX,
- issuer mint/redeem flows that do not perform a cross-asset conversion.

### Panel B — OfferCreate execution

Auto-bridging also occurs when OfferCreate crosses existing liquidity. This panel measures token-token trading whose executed liquidity is partly or wholly XRP-mediated.

Do **not** combine Panel B volume with Payment volume unless duplicate economic execution has been ruled out. Report them independently first.

## Canonical asset identifier

Represent every asset as one of:

- `XRP`
- `IOU:<currency>:<issuer>`
- later extensions only when the asset is actually DEX-tradable under the active amendment set

Do not collapse same currency code across issuers. `USD:rIssuerA` and `USD:rIssuerB` are distinct XRPL assets.

## Per-transaction classifier

Each included transaction receives one of the following mutually exclusive classifications:

1. `direct_non_xrp`
   - source and destination assets differ,
   - executed liquidity shows no XRP intermediate leg.

2. `xrp_bridged_full`
   - source and destination are both non-XRP assets,
   - executed liquidity contains source↔XRP and XRP↔destination legs,
   - no material direct source↔destination execution is observed for the same transaction.

3. `xrp_bridged_mixed`
   - source and destination are both non-XRP assets,
   - transaction executes using a combination of direct source↔destination liquidity and XRP-mediated legs.

4. `xrp_endpoint`
   - XRP is the source or destination asset itself.
   - This is economically relevant XRP settlement/trading but **not** bridge usage and must not inflate bridge share.

5. `unresolved_execution`
   - transaction is cross-asset, but metadata cannot be classified without unsafe assumptions.

Never force an unresolved transaction into a directional category.

## Execution reconstruction — Offers

For every `Offer` entry in transaction `AffectedNodes`:

1. Read the Offer's `TakerPays` and `TakerGets` asset identities.
2. Compare prior vs final values for modified offers, and prior values vs zero for fully consumed/deleted offers.
3. Derive the amount consumed from each side using metadata deltas.
4. Record an executed edge between the two assets.
5. Aggregate all executed edges for the transaction.

A token→XRP edge plus an XRP→token edge in the same economic execution is candidate evidence of XRP bridging.

### Guardrail: offer deletion is not always trade volume

Offers can be removed because they are unfunded or expired when encountered. The parser must distinguish actual balance/amount consumption from administrative cleanup and must not count a deleted stale offer's full historical size as executed volume.

Primary source:
- https://xrpl.org/docs/concepts/tokens/decentralized-exchange/offers

## Execution reconstruction — AMMs

A transaction can execute against an AMM instead of, or alongside, order-book Offers.

For AMM-related execution:

1. identify affected AMM pseudo-accounts / AMM state,
2. recover the AMM asset pair,
3. compute transaction-attributable changes in the pool-held assets from affected ledger entries,
4. record the executed asset edge,
5. distinguish trade-induced pool changes from AMMDeposit, AMMWithdraw, AMMCreate, governance, or auction operations.

An XRP/token AMM leg can satisfy one side of an XRP bridge. A complete bridge may use:
- Offer + Offer,
- AMM + AMM,
- Offer + AMM.

The classifier must support all three combinations.

## Bridge decision rule

For a non-XRP source asset `S` and non-XRP destination asset `D`:

`xrp_bridged=true` only if transaction-level executed-liquidity reconstruction contains economically consistent execution edges:

`S ↔ XRP` and `XRP ↔ D`

within the same transaction.

If a direct `S ↔ D` edge is also consumed, classify as `xrp_bridged_mixed`.

The presence of XRP balance changes alone is not sufficient because every transaction destroys an XRP fee and accounts may have unrelated XRP balance effects.

## First metrics

### Core count metrics

For each day and month:

- `cross_asset_tx_count`
- `resolved_cross_asset_tx_count`
- `xrp_bridged_full_count`
- `xrp_bridged_mixed_count`
- `direct_non_xrp_count`
- `xrp_endpoint_count`
- `unresolved_execution_count`

Derived:

`resolved_bridge_share_count = (xrp_bridged_full_count + xrp_bridged_mixed_count) / resolved_non_endpoint_cross_asset_count`

Count share is diagnostic only; H1 should not be scored from transaction count alone.

### Economic-value metrics

For each resolved transaction record:

- delivered destination amount and asset,
- source amount consumed where reconstructable,
- XRP amount passing through bridge legs where present,
- direct source↔destination amount where present,
- a normalization quote and timestamp when converting heterogeneous assets into a common economic unit.

Primary H1 metric:

`bridge_share_value = normalized_value_attributable_to_xrp_bridge / normalized_total_resolved_non_endpoint_cross_asset_value`

Where mixed executions occur, only the bridge-attributable fraction belongs in the numerator.

## Normalization hierarchy

Do not invent USD values for illiquid issued tokens.

Use a tiered approach:

1. reliable same-window external market or issuer redemption reference,
2. robust XRPL market quote with minimum-depth requirement,
3. stablecoin face value only when redemption/peg assumptions are explicitly defensible,
4. otherwise mark normalized value unavailable.

Publish both:
- a value-normalized panel for economically priceable assets,
- and an unpriced / excluded-value coverage panel.

Coverage must be visible so priceable flows are not silently treated as the whole ledger.

## Corridor dimensions

For each resolved transaction retain:

- source asset,
- destination asset,
- source issuer,
- destination issuer,
- transaction type / subtype,
- account == destination flag,
- permissioned domain identifier if present,
- date/month,
- liquidity mechanism: offer / AMM / mixed,
- bridge classification,
- normalized-value coverage flag.

Only add institution/account labels when supported by a defensible public attribution source. Unknown accounts remain unknown.

## Independent liquidity panel

In parallel with the transaction classifier, collect `book_changes` by validated ledger to build:

- XRP-token DEX volume,
- token-token direct DEX volume,
- XRP/RLUSD volume,
- XRP/RLUSD realized price range,
- active XRP pair count,
- concentration by issuer/pair.

Use periodic `book_offers` / AMM state snapshots for depth and slippage studies.

This panel tests whether growing bridge usage is accompanied by deeper XRP liquidity, but it must not be used to infer bridge execution on its own.

## Known false positives / false negatives

### False positives to prevent

- XRP appears in submitted `Paths` but is not used.
- XRP appears in an account's fee/balance change but is not liquidity.
- `book_changes` XRP volume is assumed to be bridge volume.
- stale/unfunded Offer deletion is counted as trade execution.
- XRP is an endpoint asset and is mislabeled as an intermediary bridge.
- AMM deposit/withdraw liquidity movement is mislabeled as swap volume.

### False negatives to prevent

- bridge leg executes against AMM rather than Offer book.
- one bridge leg uses an Offer and the other an AMM.
- transaction splits flow across multiple paths.
- transaction combines direct and XRP-bridged liquidity.
- partial payment is dropped because requested and delivered values differ.

## Validation strategy

Before producing historical results:

1. create or identify known transactions representing each class,
2. manually inspect transaction metadata,
3. verify classifier output for:
   - direct token→token,
   - full XRP auto-bridge,
   - mixed direct + XRP bridge,
   - XRP endpoint,
   - Offer + AMM execution if available,
   - partial Payment,
4. keep fixtures in-repo,
5. fail tests on unresolved schema changes instead of silently reclassifying.

## Minimum publishable historical run

The first empirical H1 result should cover at least:

- 30 consecutive days as a pipeline-validation sample,
- then 6–12 months if archival access and runtime permit,
- monthly bridge share by count,
- monthly bridge share by economically normalized value,
- resolved/unresolved coverage,
- top asset pairs,
- separate Payment and OfferCreate panels,
- XRP/RLUSD and major XRP-pair liquidity context.

A one-day snapshot is not enough to score H1 materially.

## Evidence thresholds for H1

The exact preregistered numerical thresholds should be frozen **before** looking at historical output. At minimum, the scoring decision must consider:

- bridge share by economic value, not just count,
- persistence across multiple months,
- concentration in one pair vs breadth across independent pairs,
- whether bridge share is rising/falling,
- whether XRP pair depth grows alongside usage,
- how much value remains unresolved/unpriced.

### Stronger H1 evidence

- persistent, economically non-trivial XRP-mediated share,
- multiple independent asset pairs/corridors,
- rising or durable share across time,
- deeper XRP pair liquidity consistent with the flow,
- evidence that XRP routes are selected because they improve execution economics.

### Weaker / contradicting H1 evidence

- cross-asset XRPL volume grows while resolved XRP bridge share remains trivial,
- direct token-token / stablecoin routes dominate economically meaningful flow,
- bridge share falls over time despite broader XRPL adoption,
- XRP endpoint/speculative trading is large but intermediary bridge usage is small,
- headline transaction growth comes mainly from activity unrelated to settlement routing.

## Immediate implementation outputs

Recommended next files:

- `scripts/collect_h1_bridge_routes.py` — validated-ledger transaction extraction
- `scripts/classify_h1_execution.py` — metadata → executed-edge classifier
- `data/h1_bridge_routes_monthly.csv` — aggregated results
- `data/h1_bridge_route_samples.csv` — manually verified transaction fixtures
- `research/bridge_utility/H1_CLASSIFIER_NOTES.md` — evolving edge cases

## Thesis impact of this research session

**No score change.**

This session strengthens the measurement design, not the investment thesis. It establishes that H1 is measurable from ledger-native data but that aggregate DEX metrics and submitted payment paths are insufficient proxies for executed XRP bridge usage.

The next valid H1 evidence must come from executed-route telemetry.