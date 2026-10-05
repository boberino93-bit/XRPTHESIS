# Institutional XRP Inventory — U.S. Spot ETP Cross-Check

Date: 2026-10-05
Status: research session / SEC-filing cross-check
Primary claims: H3, H8

## Research question

Is there directly measurable evidence that regulated investment products are holding materially larger quantities of XRP, rather than merely creating narrative or trading activity around it?

This note uses SEC-filed schedules of investment for four U.S. spot XRP products and compares reported XRP quantities at 2025-12-31 with 2026-06-30.

## Primary-source holdings

| Product | XRP at 2025-12-31 | XRP at 2026-06-30 | Change | Change % |
|---|---:|---:|---:|---:|
| Bitwise XRP ETF | 131,223,200 | 286,838,446 | +155,615,246 | +118.6% |
| Canary XRP ETF | 175,625,441 | 231,279,303 | +55,653,862 | +31.7% |
| Franklin XRP ETF | 118,387,154 | 225,368,821 | +106,981,667 | +90.4% |
| Grayscale XRP Trust ETF | 122,230,386 | 55,035,728 | -67,194,658 | -55.0% |
| **Aggregate** | **547,466,181** | **798,522,298** | **+251,056,116** | **+45.9%** |

Primary sources:
- Bitwise XRP ETF 10-Q: https://www.sec.gov/Archives/edgar/data/2039525/000119312526346245/xrp-20260630.htm
- Canary XRP ETF 10-Q: https://www.sec.gov/Archives/edgar/data/2039505/000199937126017438/xrpc-10q_063026.htm
- Franklin XRP ETF 10-Q: https://www.sec.gov/Archives/edgar/data/2059438/000114036126033198/ef20077164_10-q.htm
- Franklin XRP ETF 2025 quantity source: https://www.sec.gov/Archives/edgar/data/2059438/000114036126005816/ef20065214_10q.htm
- Grayscale XRP Trust ETF 10-Q: https://www.sec.gov/Archives/edgar/data/2037427/000203742726000007/ck0002037427-20260630.htm

## Finding 1 — Aggregate regulated-product inventory increased materially

Across these four products, reported XRP holdings rose by approximately **251.1 million XRP**, from 547.5 million to 798.5 million XRP, a **45.9% increase** over the six-month comparison window.

### Interpretation

This is direct evidence for one H3 mechanism: regulated investment vehicles can create persistent XRP inventory demand because spot products must hold XRP to back shares. The quantity increase is more relevant to XRP-specific value capture than generic XRPL transaction growth because the asset being accumulated is XRP itself.

This does **not** establish bridge-asset utility, payment routing, or non-speculative settlement demand. It is investment-product inventory demand and should be treated as a separate mechanism from H1.

## Finding 2 — The signal is not uniform

Grayscale's reported XRP holdings fell by approximately **67.2 million XRP (-55.0%)** over the same comparison window while Bitwise, Canary, and Franklin increased holdings.

### Interpretation

The aggregate increase is not evidence of one-way institutional accumulation across every product. Product-specific redemptions, fee differences, investor migration, and market structure can move inventory in opposite directions.

This is the strongest contrary observation in the dataset and prevents treating the aggregate increase as an unconditional or irreversible scarcity trend.

## H3 impact

**Supportive, but mechanism-specific.**

The SEC filings demonstrate observable XRP inventory held inside regulated spot investment products. That satisfies an important part of H3's measurement requirement for institutional XRP balances.

However, the evidence does not prove that Ripple/XRPL/RLUSD adoption caused the inflows. It therefore supports the existence and scale of institutional inventory demand without proving the broader ecosystem-to-XRP causal chain.

## H8 impact

**Relevant but insufficient for valuation conclusions.**

Hundreds of millions of XRP held by spot products may reduce freely circulating supply while shares remain outstanding. But a high-price scenario still requires explicit modeling of:
- creations versus redemptions,
- net new cash versus asset transfers,
- effective liquid float,
- market depth and liquidity replenishment,
- ETF arbitrage mechanics,
- and whether holdings persist through adverse price regimes.

The holdings data should become an input to H8, not a shortcut to a price target.

## Recommended telemetry

Track, at minimum, for each U.S. spot XRP product:
1. XRP units held,
2. shares outstanding,
3. daily/weekly creations and redemptions where available,
4. net change in XRP inventory,
5. aggregate XRP held across products,
6. aggregate holdings as a percentage of circulating and estimated liquid supply,
7. product concentration and migration between issuers.

## Research conclusion

The institutional-inventory mechanism is no longer hypothetical. SEC filings show regulated U.S. spot products holding hundreds of millions of XRP and, in aggregate across the four products reviewed, materially more XRP at 2026-06-30 than at 2025-12-31.

The correct conclusion is narrower than “institutional adoption proves the thesis”: **regulated spot products are a measurable source of XRP-specific inventory demand, but that demand is heterogeneous and does not validate bridge utility or any particular price target.**
