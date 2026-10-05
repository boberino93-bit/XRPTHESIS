# XRPTHESIS — Manager Status

Date: 2026-10-05
Baseline head reviewed: `4213100b1fc9047d1dbb341c594cd7f33fabb174`

## Management objective

Keep the project focused on falsifying or validating the XRP thesis through measurable causal links, while preventing parallel agents from duplicating work or turning ecosystem adoption into unsupported XRP conclusions.

## Current state

The repository has a sound research contract and a functioning deterministic scoring baseline. The current classification is **Mixed / insufficient — adoption evidence does not yet establish all gating links**.

Current gate state at the reviewed baseline:

- **H1 — Bridge-asset utility:** 0.00; unmeasured gate.
- **H3 — XRP-specific value capture:** 0.00; neutral evidence only; core bottleneck.
- **H8 — Valuation/liquidity mechanics:** 0.00; model not yet built.

H2 and H7 have positive evidence, but they cannot substitute for the three gating links above.

## Completed foundation

PR #1 merged the adversarial XRP value-capture mechanism map. It establishes eight candidate mechanisms and makes bridge share, direct XRP settlement, inventory demand, market depth, and effective liquid supply the highest-value measurements.

This is a **measurement framework**, not validation of H3 or H8.

## Active execution queue

### P0 — gates and system integrity

1. **Issue #8 — Research integrity / CI guardrails**
   - Add schema validation and tests before the evidence ledger expands materially.
   - Prevent unknown claim IDs, duplicate IDs, invalid weights, malformed predictions, and unreproducible scoring.
   - Harden generated reporting so automation does not overwrite reviewed contrary-evidence analysis with placeholder text.

2. **Issue #7 — H1 bridge-routing and direct-settlement utility**
   - Measure actual XRP-routed economic value, not technical capability or raw transaction counts.
   - Establish a reproducible bridge-share dataset and bypass cases.

3. **Issue #2 — H3 XRP-specific value capture**
   - Convert the mechanism map into empirical measurements.
   - Highest-value targets: XRP bridge share, direct XRP settlement, XRP/RLUSD depth, institutional XRP inventory, and XRPL value that explicitly bypasses XRP.

4. **Issue #3 — H8 liquidity/valuation stress test**
   - Build only after initial market-depth/effective-float inputs are defined well enough to avoid market-cap shortcuts.
   - The user-defined recurring-inflow scenarios belong here as stress tests, not assumptions.

### P1 — adoption and event validation

5. **Issue #4 — H2/H7 production adoption dataset**
   - Separate announcement, pilot, production, scaled, migrated, and discontinued projects.
   - This dataset should feed H3 only when XRP-specific demand is independently demonstrated.

6. **Issue #5 — H5 preregistered event studies**
   - Build the event registry and analysis code now; do not score immature windows as evidence.

### P2 — conditional macro thesis

7. **Issue #6 — H6 macro/liquidity interaction**
   - Preregister regimes and compare against broad crypto beta.
   - Null and contradictory periods are required observations, not exceptions to explain away.

## Dependency map

```text
Issue #8 integrity guardrails
        |
        +-------------------------------+
        |                               |
Issue #7 H1 measurements        Issue #4 H2/H7 dataset
        |                               |
        +-------------+-----------------+
                      |
              Issue #2 H3 value capture
                      |
          market depth / float inputs
                      |
              Issue #3 H8 stress model

Issue #4 + preregistered event rules --> Issue #5 H5 event studies
Issue #5 + macro regime definitions ---> Issue #6 H6 conditional analysis
```

The dependencies are directional, not blocking in the software sense. Parallel agents may scaffold downstream code, but conclusions must not outrun upstream measurements.

## Merge / evidence policy

- Prefer workstream-specific files and directories to reduce collisions.
- Research reports and datasets may be developed in parallel.
- Changes to `data/evidence.csv`, `data/claims.csv`, `data/predictions.csv`, or scoring logic deserve extra review because they directly alter thesis state.
- Every supportive evidence addition should trigger an explicit search for disconfirming evidence.
- Ripple, XRPL, RLUSD, and XRP remain separate objects in every dataset and conclusion.
- Do not treat an announcement as production usage.
- Do not treat XRPL production usage as XRP value capture without a measured mechanism.
- Do not translate gross volume into net buying.
- Do not use market-cap arithmetic as a price model.

## Immediate management risks

### 1. Gate imbalance
Positive H2/H7 evidence can make the project feel bullish while H1/H3/H8 remain unmeasured. The score correctly prevents this from becoming a strengthening classification, but human summaries must preserve the same discipline.

### 2. Data-integrity debt
The scoring script currently checks a few enums but there is no dedicated schema/test gate. As multiple agents begin writing evidence, this becomes a material research risk.

### 3. Report overwrite risk
`score_thesis.py` generates a generic `Strongest evidence against the thesis` paragraph. A scheduled monitoring run can therefore replace a reviewed, source-grounded version of that section unless reporting is separated or hardened.

### 4. H1 blind spot
The project already identified bridge routing as one of the strongest native XRP utility mechanisms, yet H1 had no dedicated issue before this review. Issue #7 closes the coordination gap; the empirical work is still outstanding.

### 5. False precision
The deterministic score is useful telemetry, not a probability. Sparse evidence can produce apparently precise decimals. Conclusions should cite the underlying evidence count, quality, and gate coverage alongside the score.

## Definition of a meaningful thesis upgrade

The project should not materially upgrade the XRP investment thesis merely because more institutions use Ripple products, RLUSD grows, or tokenized assets appear on XRPL.

A meaningful upgrade requires evidence that crosses at least one XRP-specific mechanism boundary, such as:

- rising share of meaningful cross-asset flow actually routed through XRP,
- persistent direct XRP settlement demand,
- demonstrably larger institutional or market-maker XRP inventory,
- durable XRP-pair depth/liquidity growth attributable to economic usage,
- or a valuation model showing high-price scenarios survive realistic float, depth, velocity, sell-side response, and net-demand assumptions.

Until that evidence exists, the correct managerial posture is **promising infrastructure/adoption evidence, unresolved XRP value capture**.
