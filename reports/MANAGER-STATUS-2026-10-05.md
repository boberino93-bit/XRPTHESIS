# XRPTHESIS — Manager Status

Date: 2026-10-05
Current head reviewed: `a3a4e91cc04a4b32a7b518c0d21ed57b1aba9e68`

## Management objective

Keep the project focused on falsifying or validating the XRP thesis through measurable causal links, while preventing parallel agents from duplicating work or turning ecosystem adoption into unsupported XRP conclusions.

## Current state

The repository has a sound research contract and a functioning deterministic scoring baseline. The current classification remains **Mixed / insufficient — adoption evidence does not yet establish all gating links**.

Current gate state:

- **H1 — Bridge-asset utility:** **+2.00.** Official XRPL documentation establishes a real native auto-bridging mechanism, but no material executed-route volume has yet been measured.
- **H3 — XRP-specific value capture:** **-0.60.** Current architecture evidence is mixed: Ripple still documents an XRP ODL path, while current Ripple Payments architecture can settle through fiat/stablecoins without structurally requiring XRP.
- **H8 — Valuation/liquidity mechanics:** **0.00.** The stress-test model is not yet built.

H2 and H7 remain positive, but they cannot substitute for the three gating links above.

## Completed foundation

### PR #1 — adversarial value-capture mechanism map

Merged the eight-mechanism H3/H8 framework covering fee burn, reserves, auto-bridging, direct settlement, RLUSD spillover, institutional inventory, market-depth price formation, and supply concentration.

This is a **measurement framework**, not validation of H3 or H8.

### Payments-architecture research — 2026-10-05

A concurrent research lane added `research/value_capture/PAYMENTS_ARCHITECTURE_2026-10-05.md` and three evidence rows:

- H1 receives modest mechanism-level support because XRP can be selected as the intermediary when it gives the cheapest executable path.
- H3 receives weak support from documented XRP-based ODL capability.
- H3 receives stronger contrary evidence from current Ripple Payments architecture supporting fiat/stablecoin settlement without forcing XRP.

Managerial conclusion: this work is useful and internally consistent, but it **does not close H1 or H3**. It sharpens the next measurement target: executed-route telemetry and persistent XRP inventory/depth.

## Active execution queue

### P0 — gates and system integrity

1. **Issue #8 — Research integrity / CI guardrails**
   - Add schema validation and tests before the evidence ledger expands materially.
   - Prevent unknown claim IDs, duplicate IDs, invalid weights, malformed predictions, and unreproducible scoring.
   - Harden generated reporting so automation does not overwrite reviewed contrary-evidence analysis with placeholder text.

2. **Issue #7 — H1 bridge-routing and direct-settlement utility**
   - H1 is no longer empty, but present support proves capability rather than economically material usage.
   - Measure actual XRP-routed economic value, not technical capability or raw transaction counts.
   - Establish a reproducible bridge-share dataset and bypass cases from validated execution metadata.

3. **Issue #2 — H3 XRP-specific value capture**
   - Convert the mechanism map and payments-architecture research into empirical measurements.
   - Highest-value targets: XRP bridge share, direct XRP settlement, XRP/RLUSD depth, institutional XRP inventory, and XRPL/payment value that explicitly bypasses XRP.

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
- Do not infer executed XRP routing merely because XRP appeared in submitted path options; use validated execution metadata and consumed liquidity.
- Do not translate gross volume into net buying.
- Do not use market-cap arithmetic as a price model.

## Immediate management risks

### 1. Gate imbalance
Positive H2/H7 evidence can make the project feel bullish while H1 remains only mechanism-level, H3 is slightly negative/unresolved, and H8 is unmeasured. Human summaries must preserve the same gate discipline as the score.

### 2. Architecture-versus-usage confusion
The project now has good evidence that XRP **can** bridge and that Ripple Payments **can** bypass XRP. Neither tells us the production mix. The decisive next work is executed-route and inventory telemetry.

### 3. Data-integrity debt
The scoring script checks a few enums but there is no dedicated schema/test gate. As multiple agents begin writing evidence, this is now a material research risk.

### 4. Report overwrite risk
`score_thesis.py` currently generates a generic `Strongest evidence against the thesis` paragraph. A scheduled monitoring run can replace reviewed, source-grounded analysis unless reporting is separated or hardened.

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

Until that evidence exists, the correct managerial posture is **promising infrastructure/adoption evidence, but unresolved and currently slightly negative XRP-specific value capture**.
