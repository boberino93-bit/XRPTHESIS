# Methodology

## Purpose

This project is designed to resist confirmation bias. It scores evidence against predeclared claims and preserves a chronological ledger of both supporting and contradicting observations.

## Evidence classes

| Class | Meaning | Examples |
|---|---|---|
| A | Primary / directly measurable | legislation, court filings, XRPL ledger data, audited/attested supply, exchange order books |
| B | High-quality secondary | institutional research, regulated fund filings, reputable financial reporting |
| C | Company claim / interested party | Ripple press release, partner announcement, vendor case study |
| D | Commentary / social / unverified | influencer posts, anonymous claims, unsourced screenshots |

Class C evidence may prove that an announcement was made, but not necessarily that the claimed economic outcome occurred.

## Evidence ledger fields

Each row in `data/evidence.csv` records:

- `evidence_id`
- `observed_date`
- `claim_id`
- `direction`: support / contradict / neutral
- `weight`: 1–5
- `quality`: A / B / C / D
- `fact`
- `interpretation`
- `source`
- `status`: confirmed / provisional / disputed

The `fact` field must be source-grounded. Interpretation belongs in its own field.

## Claim scoring

Each evidence row receives a signed contribution:

```text
support     = +weight
neutral     = 0
contradict  = -weight
```

Quality multipliers:

```text
A = 1.00
B = 0.80
C = 0.60
D = 0.25
```

Confirmed evidence receives full weight. Provisional evidence receives 50%. Disputed evidence receives 25% until resolved.

For claim `c`:

```text
raw_score(c) = Σ signed_weight × quality_multiplier × status_multiplier
```

The displayed score is bounded to `[-10, +10]`.

This score is intentionally simple and auditable. It is not a probability of future price appreciation.

## Thesis-level gating

A high aggregate score cannot hide a failed causal bottleneck.

The following claims are **gates**:

- H1 bridge-asset utility
- H3 XRP-specific value capture
- H8 valuation/liquidity mechanics for high-price scenarios

If H3 is negative, the overall thesis cannot be classified as `Strengthening` merely because Ripple, RLUSD, or XRPL adoption is strong.

## Prediction registration

Predictions should be entered before the result is known and contain:

- metric,
- direction,
- threshold,
- start date,
- evaluation date/window,
- comparison benchmark,
- failure condition.

Moving the goalposts requires closing the old prediction as failed/expired/indeterminate and opening a new version.

## Event studies

For regulatory or adoption catalysts:

1. Timestamp the event using the earliest public confirmation.
2. Record XRP price and benchmark price at the event.
3. Measure 1d, 7d, 30d, 90d, 180d, 365d, and 540d windows where available.
4. Compare XRP return with BTC and a broad crypto benchmark.
5. Distinguish one-time speculative reaction from persistent liquidity/adoption changes.

## Adoption versus value capture

Every adoption event must answer four separate questions:

1. Did the project actually enter production?
2. Did economically meaningful volume/value appear?
3. Did that activity occur on XRPL or merely use a Ripple product off-ledger?
4. Did it create measurable demand for XRP?

A `yes` to #1–#3 is not automatically a `yes` to #4.

## Price-scenario discipline

Price targets are model outputs, not thesis premises.

Each scenario must expose assumptions for:

- circulating and effective liquid supply,
- market depth / slippage,
- annual or periodic net demand,
- XRP inventory held by institutions,
- velocity / reuse,
- leverage and derivatives,
- broad-crypto market regime,
- competitor substitution,
- Ripple escrow/distribution behavior where relevant.

Sensitivity tables should show which assumptions dominate the result.

## Source hygiene

Prefer, in order:

1. Government, regulator, court, exchange, or ledger source.
2. Audited/attested issuer data.
3. Counterparty confirmation from both sides of a partnership.
4. Reputable secondary reporting.
5. Company marketing.
6. Social claims.

Broken or removed sources remain in the ledger but should be marked accordingly rather than silently deleted.

## Review cadence

- **Weekly:** automated public metrics and data-integrity checks.
- **Event-driven:** legislation, court rulings, ETF/fund changes, production launches, material XRPL/Ripple announcements.
- **Monthly:** claim rescoring and contrary-evidence review.
- **Quarterly:** full thesis review and versioned conclusion.

## Anti-bias checklist

Before changing a claim score, ask:

- Would I count this evidence if it pointed the other direction?
- Is this Ripple success or XRP demand?
- Is this an announcement or measured production usage?
- Is the source financially interested in the conclusion?
- Did I predeclare the metric/window?
- Am I explaining a miss by inventing a new narrative after the fact?
