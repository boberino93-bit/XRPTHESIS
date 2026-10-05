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
AGENTS.md                     Agent operating rules
README.md                     Project overview
docs/THESIS.md                Formal thesis and causal model
docs/METHODOLOGY.md           Evidence, scoring, falsification rules
data/claims.csv               Canonical claim registry
data/evidence.csv             Evidence ledger
scripts/score_thesis.py       Deterministic claim/thesis scoring
scripts/collect_public_metrics.py  Public-data snapshot collector
reports/BASELINE-2026-10-05.md     Initial evidence baseline
.github/workflows/thesis-monitor.yml Scheduled + manual monitoring
```

## Current baseline

The project begins from a deliberately mixed state:

- Ripple reports RLUSD circulating supply above $2.4B as of 2026-09-24.
- Dubai Land Department real-estate tokenization uses XRPL infrastructure with Ripple custody supporting a project partner.
- The SEC/Ripple appellate litigation was dismissed in August 2025, while the underlying court distinctions around institutional sales remain relevant.
- The U.S. Senate failed to invoke cloture on the CLARITY Act motion to proceed on 2026-09-15 by 49–50; a motion to reconsider was entered.
- These developments support parts of the infrastructure/adoption thesis, but **none alone proves sustained XRP demand or any price target**.

See `reports/BASELINE-2026-10-05.md` for sources and initial interpretation.

## Running locally

```bash
python scripts/score_thesis.py
python scripts/collect_public_metrics.py
```

The monitor is designed to continue gathering evidence while preserving the distinction between adoption and XRP-specific value capture.
