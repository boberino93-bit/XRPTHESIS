# H8 Liquidity Baseline — 2026-10-05

Status: research workstream / first empirical baseline  
Primary claim: H8 — valuation/liquidity mechanics  
Secondary relevance: H3 — XRP-specific value capture

## Research question

Can large recurring XRP demand plausibly produce sustained repricing under realistic market-depth, float, velocity, inventory, and liquidity-replenishment assumptions?

This note does **not** attempt to prove a price target. Its purpose is to establish scale and identify the variables that a defensible H8 model must contain.

The scenario stress-tested here is **$200M USD of genuinely net XRP demand per week for two years**. That is intentionally different from $200M of gross trading volume. Gross volume can recycle the same inventory many times and does not imply net accumulation.

---

## Finding 1 — visible spot depth is small relative to the proposed weekly net-demand stream

CoinGecko's 2026 centralized-exchange liquidity study sampled the most liquid spot XRP ticker on eight exchanges — Binance, Bybit, Bitget, OKX, Kraken, Crypto.com, Coinbase, and MEXC — once daily over 60 days from July 6 through September 3, 2026.

The study reports that median cumulative XRP liquidity across the eight exchanges was approximately:

- **$18M of bids** within the observed downside range;
- **$14M of asks** within the observed upside range;
- approximately **$30M total depth** across the roughly +/-2% range.

CoinGecko also reports that total depth was broadly similar to its 2025 study, although 2026 XRP depth was more buy-side skewed and more widely distributed among venues.

Source (quality B — independent market-data research):  
https://www.coingecko.com/research/publications/crypto-liquidity-report-2026

Methodology / full report:  
https://assets.coingecko.com/reports/2026/CoinGecko-2026-Crypto-Liquidity-on-CEXes-Report.pdf

### Interpretation

A **$200M weekly net purchase stream is about 14.3x the study's median visible sell-side depth inside the first ~2% above market**:

```text
$200M / $14M ~= 14.3x
```

This does **not** mean a $200M buy mechanically moves XRP by 28.6%, or by any other linear multiple of the 2% depth window. The order book is dynamic:

- market makers replenish offers;
- arbitrage imports liquidity from other venues;
- holders place new sell orders as price rises;
- OTC blocks may avoid visible books;
- derivatives can hedge or amplify spot demand;
- the same XRP can turn over repeatedly.

The correct conclusion is narrower: **$200M/week of persistent net demand would be economically large relative to currently visible near-market sell liquidity and therefore cannot be modeled as a frictionless purchase at the current price.**

---

## Finding 2 — the two-year scenario is large relative to today's circulating float, but only if the demand is truly net and sticky

CoinGecko's 2026-10-05 XRP market snapshot reports approximately:

- price: about **$1.52**;
- circulating supply: about **63.093B XRP**;
- market capitalization: about **$95.8B**;
- total supply: about **99.986B XRP**.

Source (quality B):  
https://www.coingecko.com/en/coins/xrp/

The proposed demand stream totals:

```text
$200M/week * 104 weeks = $20.8B nominal net demand
```

At a hypothetical constant acquisition price of $1.52, that cash would purchase about **13.68B XRP**, equal to about **21.7% of today's circulating supply**. A constant price is not realistic if demand is genuinely persistent; the calculation is useful only as a scale check.

### Acquisition sensitivity

| Average acquisition price | XRP acquired by $20.8B | % of current circulating supply |
|---:|---:|---:|
| $1.52 | 13.68B | 21.69% |
| $2 | 10.40B | 16.48% |
| $5 | 4.16B | 6.59% |
| $10 | 2.08B | 3.30% |
| $20 | 1.04B | 1.65% |
| $50 | 0.416B | 0.66% |

### Interpretation

This table shows why a fixed "dollars in -> tokens out" model becomes self-defeating as price rises. Persistent accumulation purchases fewer XRP at higher prices, while higher prices simultaneously entice additional holders to sell.

The central H8 problem is therefore a **dynamic supply curve**, not a static market-cap equation.

---

## Finding 3 — current institutional inventory growth provides a useful empirical comparison, but not a causal model

The existing XRPTHESIS evidence ledger (`E0013`) records SEC-filed holdings for four regulated XRP investment products. Aggregate holdings in those filings rose from approximately **547.5M XRP at 2025-12-31 to 798.5M XRP at 2026-06-30**, an increase of roughly **251.1M XRP** over six months.

That is approximately:

```text
251.1M XRP / ~26 weeks ~= 9.7M XRP per week
```

At a $1.52 spot reference, 9.7M XRP is roughly **$14.7M/week** of inventory-equivalent accumulation. This is not the same as measured cash flow because acquisition prices varied and the SEC holdings snapshots are endpoints rather than weekly flow data.

### Interpretation

The proposed $200M/week scenario is therefore not merely "more ETF demand." At the current spot reference it is more than an order of magnitude larger than the average inventory-growth pace implied by those four existing fund snapshots.

This does not make $200M/week impossible. It means H8 should treat it as a **high-intensity regime** requiring an explicit source of recurring capital and evidence that the demand is net rather than recycled turnover.

---

## Finding 4 — derivatives can materially distort the mapping from spot demand to price

CoinGecko's 2026-10-05 XRP market page reports perpetual-futures open interest of roughly **$4.7B** and a perpetual-to-spot 24-hour volume ratio above **16x** at the time observed.

Source (quality B):  
https://www.coingecko.com/en/coins/xrp/

### Interpretation

This makes a simple spot-only price-impact model incomplete. A large spot accumulation program can interact with:

- leveraged long/short positioning;
- liquidations;
- funding-rate changes;
- basis arbitrage;
- dealer hedging;
- cross-exchange inventory transfers.

These mechanisms can temporarily amplify or dampen spot-driven repricing. They can also create large gross trading volume without corresponding long-term XRP inventory demand.

For H8, derivatives should therefore be modeled as an **amplifier / liquidity-transfer layer**, not counted as net XRP demand unless a position creates persistent spot inventory absorption.

---

## What this baseline establishes

### Supported

1. Current visible near-market XRP spot liquidity is shallow enough that a true $200M/week net purchase stream would be material relative to present order-book depth.
2. A two-year $20.8B net-demand program is large enough to absorb a non-trivial share of today's circulating XRP under low-to-moderate average acquisition prices.
3. Static-price and static-order-book assumptions fail immediately under a persistent-demand scenario.
4. Derivatives and liquidity replenishment are large enough that neither market cap nor a single depth snapshot can map directly to a terminal XRP price.

### Not established

1. That $200M/week of net XRP buying will actually occur.
2. That institutional/Ripple/XRPL activity will create that demand.
3. That visible CEX liquidity represents the full economic supply curve.
4. That a given target price — including $20, $50, $98 CAD, $1,000, or any other figure — follows from the proposed inflow.
5. That current XRP holders will remain unwilling to sell as price rises.

---

## Required H8 model architecture

The next quantitative model should operate in weekly steps and expose at least these variables:

### Demand side

- net new spot demand per week;
- institutional/ETF inventory demand;
- payment / bridge working-capital demand;
- speculative spot demand;
- OTC share versus visible-CEX share;
- demand persistence / decay.

### Supply side

- circulating supply;
- estimated effective liquid float;
- exchange balances;
- holder sell-response as price rises;
- Ripple / escrow-related distribution where economically relevant;
- market-maker inventory recycling;
- new asks entering the book as price moves.

### Market microstructure

- depth at +/-0.1%, 0.5%, 1%, 2%, and 5%;
- venue fragmentation;
- depth replenishment rate;
- realized slippage for standardized orders;
- derivatives OI, funding, basis, and liquidation intensity;
- volatility-dependent market-maker spread widening.

### State transition

A defensible model should estimate a dynamic price impact function of the form:

```text
price_change_t = f(
    net_spot_demand_t,
    available_depth_t,
    replenishment_t,
    holder_sell_response_t,
    derivatives_feedback_t,
    arbitrage_t
)
```

and then update effective float and liquidity for the next period.

The function should be calibrated to observed market data rather than chosen to force a target price.

---

## Falsification tests for the $200M/week scenario

The scenario should be rejected or heavily discounted if any of the following persist:

1. Claimed "inflows" are gross volume rather than verifiable net inventory accumulation.
2. Net XRP inventory demand remains one or two orders of magnitude below the assumed $200M/week level.
3. Increased demand is met by proportionately larger sell-side liquidity with little persistent float reduction.
4. ETF/institutional holdings grow while bridge/payment XRP inventory remains absent, showing that the utility thesis is not causing the demand.
5. Higher prices trigger enough holder distribution that effective liquid supply expands faster than net demand absorbs it.
6. A high-price result depends on holding market depth fixed while demand rises by orders of magnitude.

---

## Initial H8 assessment

**H8 remains open / unscored.**

The baseline does not justify changing the claim score yet. It does establish that a genuine $200M/week net-demand regime would be market-structure significant relative to observed 2026 XRP spot depth. At the same time, the available evidence is nowhere near sufficient to convert that regime into a deterministic price target.

The strongest next test is to build a reproducible, multi-venue depth collector and measure how XRP sell-side liquidity and replenishment behave through actual high-volume episodes. That empirical supply-response curve is more valuable to H8 than another market-cap scenario.
