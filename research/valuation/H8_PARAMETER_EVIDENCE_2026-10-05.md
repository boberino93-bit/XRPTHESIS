# H8 valuation/liquidity parameter evidence — 2026-10-05

## Status

Research input memo for **H8: Valuation/liquidity mechanics**. This memo does **not** change thesis scores.

## Research question

What can currently be measured well enough to constrain an XRP valuation/liquidity stress model, and which high-price narratives still depend on unmeasured assumptions?

## Bottom line

1. **Circulating supply is not effective liquid float.** Q1 2026 circulating supply was 61.34B XRP, but there is no defensible public measurement in this pass showing what fraction of that supply is continuously available for sale near the market price.
2. **Trading volume is not market depth.** Q1 2026 centralized-exchange spot volume averaged about $2.68B/day, but turnover does not tell us how much executable liquidity exists within 10 bps, 1%, 5%, etc. of mid-price.
3. **Ripple's escrow is a real future-supply constraint, but releases are not equivalent to immediate market sales.** Ripple reported 32.6B XRP in escrow as of 2026-06-30. Historical changes in Ripple-controlled balances can bound distribution pressure, but the model must not assume every XRP leaving escrow is sold on an exchange.
4. **There are observable inventory sinks, but they are too small and too heterogeneous to justify a low-float assumption by themselves.** U.S. spot ETFs held 775.4M XRP at Q1 close; Messari also reported 388M XRP held by Evernorth, 154.4M XRP bridged as FXRP by 2026-05-18, and 12.85M XRP in XRPL AMMs at Q1 close. These positions should be tracked, not automatically subtracted from float.
5. **A price target must be an output of an execution/liquidity model.** The model should apply persistent demand to an observed or stress-tested depth curve with replenishment, holder sell-side response, and supply distribution. `new inflow = market-cap increase` is invalid.

## Observed supply structure

### Q1 2026 independent snapshot

Messari reported for Q1 2026:

- circulating supply: **61.34B XRP**;
- quarter-end price: **$1.34**;
- circulating market cap: **$82.21B**;
- XRP burned since inception: about **14.3M XRP**;
- U.S. spot XRP ETFs: **775.4M XRP**, or **1.26%** of circulating supply;
- XRPL native AMMs: **12.85M XRP** pooled at quarter-end;
- centralized-exchange XRP spot volume: about **$2.68B/day**;
- decentralized spot volume across tracked venues: about **$11.7M/day**.

Source: Messari, *State of XRP Q1 2026* (2026-05-29): https://messari.io/report/state-of-xrp-q1-2026

Source quality under `AGENTS.md`: **B** (independent institutional research).

### Ripple-controlled supply as of 2026-06-30

Ripple's current XRP page reports:

- total XRP held by Ripple: **37,656,053,914 XRP**;
- total XRP distributed: **62,329,587,596 XRP**;
- XRP placed in escrow: **32,600,000,000 XRP**.

Because the current page's `total held` figure includes the escrowed amount, the implied non-escrow Ripple-controlled balance is:

`37,656,053,914 - 32,600,000,000 = 5,056,053,914 XRP`.

Source: Ripple XRP page, data as of 2026-06-30: https://ripple.com/xrp/

Source quality: **C** under the repository contract because this is Ripple reporting Ripple-controlled inventory.

### Distribution-rate reconstruction

Ripple's Q1 2025 report gave 2025-03-31 balances of:

- available XRP held by Ripple: **4,562,433,147 XRP**;
- XRP subject to escrow: **37,130,000,005 XRP**;
- reconstructed total Ripple-controlled XRP: **41,692,433,152 XRP**.

Comparing that with the 2026-06-30 total held figure of 37,656,053,914 XRP:

- Ripple-controlled inventory decreased by **4,036,379,238 XRP** over 15 months;
- average decrease: about **269.1M XRP/month**;
- escrow itself decreased by **4,530,000,005 XRP**, about **302.0M XRP/month**;
- implied non-escrow Ripple holdings increased by about **493.6M XRP** over the same endpoints.

Source: Ripple, *Q1 2025 XRP Markets Report*: https://ripple.com/insights/q1-2025-xrp-markets-report/

Interpretation limit: this is an **inventory-control change**, not proof of open-market selling. Transfers to partners, investment vehicles, custody arrangements, or other third parties can move XRP outside Ripple control without constituting immediate sell pressure.

## Identified inventory sinks are measurable but not equivalent to locked float

Messari's Q1 2026 report identified several holdings or liquidity allocations:

- U.S. spot ETFs: **775.4M XRP** at Q1 close;
- Evernorth: **388M XRP** reported held as of its March 2026 S-4 filing;
- FXRP on Flare: about **154.4M XRP** as of 2026-05-18;
- XRPL native AMMs: **12.85M XRP** at Q1 close.

Naively summing these gives **1.33065B XRP**, about **2.17%** of Q1 circulating supply. This is useful as an *identified inventory-allocation proxy*, not as a float deduction. The dates differ, redemption/wrapping mechanics differ, some inventory can return to markets, and overlap must be ruled out before aggregation is treated as independent.

## Market depth: current hard data gap

Kaiko's market-liquidity methodology distinguishes volume from executable depth and commonly measures order-book depth within **0.1%** and **1%** of the mid-price. It also models slippage for hypothetical order sizes. Those are the appropriate primitives for H8.

Source: Kaiko, *Understanding Centralized Exchange Liquidity Data*: https://www.kaiko.com/resources/understanding-centralized-exchange-liquidity-data

Kaiko has separately reported that XRP became one of the more liquid large altcoins by average 1% depth, but the public material reviewed here does not expose a sufficiently current XRP-specific multi-venue depth time series for direct model ingestion.

Source: Kaiko, *XRP's Liquidity Race As Crypto ETFs Deadlines Loom*: https://www.kaiko.com/resources/xrps-liquidity-race-as-crypto-etfs-deadlines-loom

Therefore the first H8 implementation must **not** infer depth from daily volume or market capitalization.

## Required H8 model architecture

### 1. Supply state

Track separately:

- circulating supply;
- Ripple escrow;
- Ripple non-escrow controlled inventory;
- identified long-duration or structurally allocated inventory (ETFs, treasury vehicles, wrapped/bridged XRP, AMM liquidity);
- exchange/custodian balances when source quality permits;
- burned XRP.

`effective_float` must remain a scenario variable until a reproducible holder/liquidity methodology is implemented.

### 2. Sell-side liquidity curve

For each observation interval, ingest multi-venue L2 order books and compute cumulative ask liquidity at minimum:

- 10 bps;
- 50 bps;
- 1%;
- 2%;
- 5%;
- 10%.

Aggregate only after normalizing quote currency and excluding clearly unreliable venues. Preserve venue-level data so concentration risk is visible.

### 3. Replenishment / resilience

A static order-book snapshot overstates permanent impact if market makers replenish offers and understates stress impact if liquidity withdraws during volatility. Measure:

- time to restore 50% and 90% of pre-shock depth;
- depth change conditional on volatility;
- spread widening;
- cross-venue arbitrage response.

### 4. Persistent net demand

Apply net demand sequentially to the liquidity curve. Do not multiply inflow by a market-cap coefficient.

Demand sources should be separable:

- spot ETF creations/redemptions;
- treasury accumulation/distribution;
- speculative spot demand;
- H1/H3 settlement inventory demand;
- AMM/DeFi inventory demand;
- other attributable sinks.

### 5. Settlement velocity / inventory reuse

H1/H3 telemetry should feed H8 rather than be guessed. For XRP-routed settlement value `V` and reuse rate `k`, inventory demand should be stress-tested as a function of `V/k`, plus risk buffers and corridor timing mismatches. High velocity reduces required standing inventory; fragmented liquidity, volatility limits, or regulatory segmentation can increase it.

### 6. Supply response

Stress the demand path against:

- continued Ripple-controlled inventory distribution;
- ETF or treasury redemptions;
- profit-taking from existing holders as price rises;
- liquidity-provider inventory expansion;
- derivatives-driven hedging that can add or absorb spot demand.

## Falsification / bearish cases the model must preserve

H8 should weaken if high target prices require one or more of the following:

- assuming most circulating XRP is permanently unavailable without holder evidence;
- treating gross payment throughput as new XRP demand despite rapid inventory reuse;
- equating daily trading volume with executable depth;
- converting every dollar of net inflow into multiple dollars of market cap using a fixed multiplier;
- ignoring Ripple distribution, ETF redemptions, or holder sell-side response;
- assuming liquidity remains static while price moves by orders of magnitude;
- using current thin depth to extrapolate permanent scarcity even though market makers can replenish at higher prices.

## Bullish cases the model is allowed to discover

H8 can strengthen if measured data show that:

- persistent net XRP demand repeatedly exceeds nearby sell-side depth;
- order-book replenishment fails to keep pace with sustained demand;
- effective float is demonstrably much smaller than circulating supply for durable, independently measured reasons;
- H1/H3 telemetry shows growing standing XRP inventory demand rather than only high-velocity pass-through;
- institutional inventory sinks rise faster than newly distributed supply and holder sell-side response.

## Immediate handoff / next data work

1. Acquire a reproducible historical XRP multi-venue L2 depth dataset (or build exchange-native collectors) for at least 0.1%, 1%, 2%, 5%, and 10% bands.
2. Build a labeled XRP inventory dataset for ETFs, treasury companies, bridges/wrappers, AMMs, Ripple-controlled inventory, and known exchange/custody balances.
3. Feed measured H1 bridge-routing value into standing-inventory scenarios rather than inventing settlement demand.
4. Run sensitivity ranges for effective float and velocity, but mark them explicitly as assumptions until measured.
5. Preserve the user's recurring-inflow scenario as a scenario input, not as evidence and not as a guaranteed flow.

## Research-state conclusion

**No H8 score change is justified yet.** The supply and inventory observations constrain the model, but the central causal question — how persistent net demand interacts with *actual executable depth, replenishment, and holder supply response* — remains unmeasured. The next highest-value H8 work is market-depth telemetry, not another market-cap arithmetic exercise.
