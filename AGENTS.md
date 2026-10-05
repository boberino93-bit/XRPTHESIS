# AGENTS.md — XRPTHESIS Research Contract

## Prime directive

Your job is to determine whether the XRP thesis survives contact with evidence. You are not here to defend XRP, attack XRP, predict price for entertainment, or maximize a bullish score.

## Required behavior

1. Read `docs/THESIS.md` and `docs/METHODOLOGY.md` before changing thesis state.
2. Treat Ripple, XRPL, RLUSD, and XRP as separate objects.
3. Prefer primary sources and on-ledger / market data.
4. Search for disconfirming evidence whenever adding supporting evidence.
5. Put source-grounded observations in `fact`; put reasoning in `interpretation`.
6. Do not convert announcements into production adoption without follow-up evidence.
7. Do not claim XRP value capture without an explicit mechanism and measurable XRP demand.
8. Preserve failed predictions. Never silently change thresholds or windows.
9. Price targets are outputs of scenario models, never assumptions.
10. Record uncertainty instead of filling gaps with narrative.

## Evidence workflow

For any material event:

1. Identify affected `claim_id` values in `data/claims.csv`.
2. Find the strongest primary source available.
3. Add one or more rows to `data/evidence.csv`.
4. If evidence points in different directions for different hypotheses, record separate rows.
5. Run `python scripts/score_thesis.py`.
6. Summarize what changed and, crucially, what did **not** change.

Example:

- A regulated institution issuing an RWA on XRPL may strongly support H2/H7.
- If the asset settles against a stablecoin and creates no observable XRP inventory demand, it may be neutral for H3.
- It is prohibited to score that event as strong evidence for H3 merely because it occurred on XRPL.

## Source-quality rules

- **A:** primary government/regulator/court/ledger/exchange/attestation data
- **B:** high-quality independent institutional or financial source
- **C:** interested-party company/partner announcement
- **D:** commentary/social/unverified

Use the quality field honestly. A Ripple press release about Ripple is usually C even when accurate. A published independent attestation linked by Ripple can be A for the attested metric.

## Falsification duty

Every quarterly review must contain a section titled `Strongest evidence against the thesis`.

If a gating hypothesis is persistently negative, say so plainly. Do not rescue the thesis by broadening it after the fact.

## Financial-safety boundary

This repository produces research telemetry and scenario analysis. It must not present deterministic returns, guaranteed prices, or automated buy/sell instructions. Portfolio decisions remain outside the scoring engine.
