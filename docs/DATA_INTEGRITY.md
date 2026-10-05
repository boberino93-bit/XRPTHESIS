# Research Data Integrity Rules

The thesis score is only as trustworthy as the ledgers that feed it. These rules are enforced by `scripts/validate_research_data.py` and CI.

## Canonical ledgers

- `data/claims.csv` defines the hypothesis registry.
- `data/evidence.csv` defines scored observations.
- `data/predictions.csv` defines preregistered tests and their eventual outcomes.

CSV headers are treated as schemas. Renaming, deleting, or reordering schema fields requires a deliberate validator update in the same change.

## Claims

Each `claim_id` must be unique and every required field must be populated. `gate` accepts only `true` or `false`.

The current mandatory thesis gates are:

- H1 — bridge-asset utility
- H3 — XRP-specific value capture
- H8 — valuation/liquidity mechanics

A change that removes or disables one of these gates fails validation rather than silently changing classification behavior.

## Evidence

Each `evidence_id` must be unique. Every row must reference an existing claim and include a source-grounded fact, interpretation, source URL, date, direction, quality, status, and weight.

Allowed values:

- `direction`: `support`, `neutral`, `contradict`
- `quality`: `A`, `B`, `C`, `D`
- `status`: `confirmed`, `provisional`, `disputed`
- `weight`: numeric value from 1 through 5 inclusive

`observed_date` must be an ISO `YYYY-MM-DD` date and cannot be in the future. Source values may contain multiple HTTP(S) URLs separated by semicolons.

Exact duplicates of the same claim + normalized fact + normalized source are rejected. If two observations are genuinely distinct, the factual distinction must be recorded explicitly rather than double-counting identical prose.

## Predictions

Each `prediction_id` must be unique and reference an existing claim. Registered, start, and evaluation dates must be ISO dates with:

`registered_date <= start_date <= evaluation_date`

Allowed `direction` values are `positive`, `negative`, and `neutral`.

Allowed statuses are:

- `open`
- `met`
- `failed`
- `expired`
- `indeterminate`

An open prediction must not contain a result. A closed prediction must preserve a result rather than silently disappearing or being rewritten.

## Deterministic scoring

`scripts/score_thesis.py` derives scores only from committed claim/evidence rows and produces `reports/latest-score.md` deterministically for a given ledger state. The report uses the latest `observed_date` rather than a wall-clock generation timestamp so identical input ledgers produce identical output.

The generated `Strongest evidence against the thesis` section is also ledger-derived. It includes the highest-weight contradictory observations plus H3-neutral constraints, preventing scheduled automation from replacing adversarial context with generic placeholder text.

## CI and automation order

Pull requests and pushes to `main` must:

1. validate the ledgers;
2. run unit tests;
3. recompute the deterministic report;
4. fail if the recomputed report differs from the committed report.

The scheduled thesis monitor must run validation and tests **before** collecting or committing telemetry. If integrity checks fail, automation stops before any monitoring snapshot or score report is written.

## Research meaning

Passing validation does not make evidence true. It only ensures that the data is structurally coherent, auditable, and scored according to the declared rules. Source quality, causal interpretation, and falsification discipline remain human research responsibilities under `AGENTS.md` and `docs/METHODOLOGY.md`.
