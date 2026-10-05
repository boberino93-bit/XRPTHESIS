# XRPTHESIS

An evidence-driven project for testing — not defending — the XRP investment thesis.

## Mission

Convert the thesis into falsifiable claims, continuously collect evidence, score each claim independently, and distinguish:

1. **Facts** — directly supported by primary or high-quality sources.
2. **Interpretations** — plausible implications of those facts.
3. **Price mechanisms** — an explicit causal path from adoption/regulation/liquidity to demand for XRP.
4. **Predictions** — measurable outcomes with deadlines or thresholds.
5. **Falsifiers** — observations that weaken or invalidate a claim.

The project must be willing to conclude that the thesis is wrong, partly wrong, mistimed, or correct for reasons different from the original narrative.

## Core hypothesis families

- **H1 — Bridge-asset utility:** XRP becomes economically relevant as a neutral bridge/liquidity asset.
- **H2 — XRPL institutional adoption:** tokenized assets, stablecoins, custody, payments, and institutional products grow materially on XRPL.
- **H3 — XRP value capture:** XRPL/Ripple adoption creates measurable demand for XRP rather than bypassing it through fiat, stablecoins, or other assets.
- **H4 — Regulatory catalyst:** clearer U.S. digital-asset rules materially lower barriers to XRP adoption.
- **H5 — Adoption-to-price lag:** fundamental adoption precedes sustained price repricing by roughly 6–18 months.
- **H6 — Macro/liquidity interaction:** global liquidity and carry-trade conditions amplify or suppress the adoption thesis.
- **H7 — Tokenized-RWA expansion:** real estate, commodities, credit, treasuries, and other RWAs become meaningful XRPL activity.
- **H8 — Valuation/liquidity mechanics:** large inflows and institutional demand can support the user-defined price scenarios under realistic market-depth, circulating-supply, velocity, and liquidity assumptions.

## Non-negotiable research rules

- Never infer XRP value capture merely because Ripple succeeds.
- Never infer XRP value capture merely because XRPL activity rises.
- Separate **Ripple**, **XRPL**, **RLUSD**, and **XRP** as distinct objects.
- Prefer primary sources, filings, legislation, on-ledger data, and reproducible market data.
- Record contrary evidence with the same priority as supporting evidence.
- No market-cap shortcut: price scenarios must model liquidity and marginal price formation.
- Every material claim needs a falsifier.
- A thesis score is research telemetry, **not financial advice or a trade signal**.

## Repository structure

```text
AGENTS.md                              Agent operating rules
README.md                              Project overview
docs/THESIS.md                         Formal thesis and causal model
docs/METHODOLOGY.md                    Evidence, scoring, falsification rules
docs/SCHEMA.md                         Canonical research-state integrity rules
data/claims.csv                        Canonical claim registry
data/evidence.csv                      Evidence ledger
data/predictions.csv                   Preregistered prediction registry
scripts/score_thesis.py                Validation + deterministic claim/thesis scoring
scripts/collect_public_metrics.py      Public-data snapshot collector
tests/test_score_thesis.py             Research-state/scoring regression tests
reports/BASELINE-2026-10-05.md         Initial evidence baseline
reports/PRIMARY-STATUS-2026-10-05.md   Reviewed primary integration status
reports/latest-score.md                Generated deterministic score telemetry
.github/workflows/research-integrity.yml PR/main integrity CI
.github/workflows/thesis-monitor.yml   Scheduled + manual monitoring
```

Research workstreams live under `research/`. The reviewed primary report preserves integrated interpretation; `reports/latest-score.md` is deliberately reproducible generated telemetry.

## Current state

The current accepted classification is deliberately constrained:

**Mixed / insufficient — adoption evidence does not yet establish all gating links.**

Current gate telemetry:

- **H1 — Bridge-asset utility: +2.00.** XRP bridging is mechanically real and historically measurable from validated XRPL metadata, but material production route share has not yet been measured.
- **H3 — XRP-specific value capture: +2.40.** SEC-filed regulated spot products provide direct XRP-specific institutional-inventory evidence, while current Ripple Payments architecture can also settle through fiat/stablecoins without structurally requiring XRP.
- **H8 — Valuation/liquidity mechanics: +0.00.** The first empirical liquidity baseline exists, but a dynamic market-depth/effective-float model is not yet validated.

Positive H2/H7 adoption evidence cannot substitute for unresolved gates. See `reports/PRIMARY-STATUS-2026-10-05.md` for the current integrated interpretation and `reports/latest-score.md` for deterministic score telemetry.

## Running locally

Regenerate the deterministic score after a valid research-state change:

```bash
python scripts/score_thesis.py
```

Verify that the committed generated report exactly matches the canonical datasets:

```bash
python scripts/score_thesis.py --check
```

Run integrity/scoring tests:

```bash
python -m unittest discover -s tests -v
```

Collect raw public telemetry:

```bash
python scripts/collect_public_metrics.py
```

The scheduled monitor runs tests and state validation before collecting or committing telemetry. Raw telemetry does not automatically become thesis evidence; evidence affecting the thesis still requires source-grounded classification under `AGENTS.md`, `docs/METHODOLOGY.md`, and `docs/SCHEMA.md`.
