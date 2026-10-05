# Research-State Schema and Integrity Rules

## Purpose

The XRPTHESIS evidence ledger is part of the analytical model, not free-form notes. A malformed row can change deterministic claim scores, so canonical research state must pass validation before it is accepted or automated.

Validation is implemented in `scripts/score_thesis.py` and enforced by CI.

## Canonical datasets

### `data/claims.csv`

Required fields:

- `claim_id`
- `title`
- `gate`
- `mechanism`
- `primary_metric`
- `bullish_condition`
- `bearish_or_falsifying_condition`
- `review_cadence`
- `status`

Rules:

- `claim_id` values are unique and non-empty.
- `gate` is `true` or `false`.
- H1, H3, and H8 must exist and must remain marked as gates unless the methodology itself is explicitly versioned.
- Required fields may not be blank.

### `data/evidence.csv`

Required fields:

- `evidence_id`
- `observed_date`
- `claim_id`
- `direction`
- `weight`
- `quality`
- `fact`
- `interpretation`
- `source`
- `status`

Rules:

- `evidence_id` values are unique and non-empty.
- `claim_id` must exist in `data/claims.csv`.
- `direction` is one of `support`, `neutral`, or `contradict`.
- `weight` is numeric and in the inclusive range 1–5.
- `quality` is one of `A`, `B`, `C`, or `D`.
- `status` is one of `confirmed`, `provisional`, or `disputed`.
- `observed_date` is an ISO `YYYY-MM-DD` date and may not be in the future relative to the validation run.
- `source` must contain one or more valid `http` or `https` URLs. Multiple URLs may be separated with semicolons.
- Required fields may not be blank.
- Exact normalized `source` + `fact` duplicates fail validation. Distinct claims about one source remain valid when the facts differ.
- Source-grounded observation belongs in `fact`; analytical reasoning belongs in `interpretation`.

### `data/predictions.csv`

Required fields:

- `prediction_id`
- `claim_id`
- `registered_date`
- `metric`
- `direction`
- `threshold`
- `start_date`
- `evaluation_date`
- `benchmark`
- `failure_condition`
- `status`

Rules:

- `prediction_id` values are unique and non-empty.
- `claim_id` must exist in `data/claims.csv`.
- `registered_date`, `start_date`, and `evaluation_date` use ISO `YYYY-MM-DD`.
- `registered_date` may not be in the future relative to the validation run.
- `start_date` may not precede `registered_date`.
- `evaluation_date` may not precede `start_date`.
- `direction` is one of `positive`, `negative`, or `two-sided`.
- `status` is one of `open`, `met`, `failed`, `expired`, or `indeterminate`.
- Required fields may not be blank.

## Scoring rules

Evidence contributes:

```text
weight × direction multiplier × quality multiplier × status multiplier
```

Direction multipliers:

```text
support = +1
neutral = 0
contradict = -1
```

Quality multipliers:

```text
A = 1.00
B = 0.80
C = 0.60
D = 0.25
```

Status multipliers:

```text
confirmed = 1.00
provisional = 0.50
disputed = 0.25
```

Each claim score is clamped to `[-10, +10]`.

H1, H3, and H8 are gating claims. A positive aggregate score cannot hide a failed gate. In particular, H3 at or below -2.0 forces a weakening classification under the current scoring contract.

## Deterministic report contract

`reports/latest-score.md` is generated telemetry. Its content must be reproducible from the committed claim, evidence, and prediction data.

The report uses the maximum committed `observed_date` as its evidence cutoff instead of a wall-clock generation timestamp. Explicit `contradict` rows are used to generate the automated `Strongest evidence against the thesis` section, with gating claims ranked first.

Reviewed interpretation and integration decisions belong in versioned human reports such as `reports/PRIMARY-STATUS-2026-10-05.md`. Automation may regenerate `reports/latest-score.md`; it must not overwrite the reviewed primary report.

## Required local checks

Regenerate the deterministic score:

```bash
python scripts/score_thesis.py
```

Validate that the committed report exactly matches the current research state:

```bash
python scripts/score_thesis.py --check
```

Run the integrity/scoring test suite:

```bash
python -m unittest discover -s tests -v
```

Collect raw public telemetry separately:

```bash
python scripts/collect_public_metrics.py
```

A telemetry snapshot does not become thesis evidence merely because it was collected. Evidence classification still follows `docs/METHODOLOGY.md` and `AGENTS.md`.

## Change discipline

Changes to `data/claims.csv`, `data/evidence.csv`, `data/predictions.csv`, or scoring logic directly alter research state and deserve heightened review.

When adding supportive evidence, explicitly search for disconfirming evidence. Do not convert Ripple-company success, XRPL adoption, RLUSD growth, or gross market volume into XRP-specific value capture without a measured XRP mechanism.
