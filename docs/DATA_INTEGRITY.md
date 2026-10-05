# Research Data Integrity

The thesis score is only trustworthy if the research state is structurally valid and reproducible. `scripts/score_thesis.py` therefore validates the committed claims, evidence, and prediction ledgers before rendering or checking `reports/latest-score.md`.

## Claims

`data/claims.csv` must contain the declared claim fields used by the scoring engine. Claim IDs must be unique, required fields must be nonblank, and `gate` must be `true` or `false`.

H1, H3, and H8 are mandatory gates. Validation fails if any is missing or no longer marked as a gate.

## Evidence

`data/evidence.csv` must contain unique `evidence_id` values and every row must reference an existing claim.

Enforced values:

- direction: `support`, `neutral`, `contradict`
- quality: `A`, `B`, `C`, `D`
- status: `confirmed`, `provisional`, `disputed`
- weight: numeric, from 1 through 5 inclusive

Required evidence fields may not be blank. `observed_date` must be a valid ISO date and cannot be in the future. Each source field must contain one or more HTTP(S) URLs; multiple URLs may be separated by semicolons.

Exact normalized source + fact duplicates are rejected so the same observation cannot silently receive weight twice.

## Predictions

`data/predictions.csv` must contain unique `prediction_id` values and every prediction must reference an existing claim.

Enforced directions are `positive`, `negative`, and `two-sided`. Enforced statuses are `open`, `met`, `failed`, `expired`, and `indeterminate`.

Registered, start, and evaluation dates must parse as ISO dates. Registration cannot be in the future, `start_date` cannot precede registration, and `evaluation_date` cannot precede the start date.

## Deterministic report

For a fixed committed research state, `reports/latest-score.md` must be byte-for-byte reproducible. The report uses the maximum evidence `observed_date` as its cutoff rather than a wall-clock generation timestamp.

The `Strongest evidence against the thesis` section is generated from explicit `contradict` evidence rows, with gating claims prioritized. This prevents scheduled automation from replacing adversarial evidence with generic placeholder prose.

Run:

```bash
python scripts/score_thesis.py --check
```

The command validates the ledgers, recomputes the report in memory, and exits non-zero if the committed report is stale or inconsistent.

## Tests and CI

Run the unit suite with:

```bash
python -m unittest discover -s tests -v
```

Pull requests and pushes to `main` run both the unit suite and the deterministic research-state check. The scheduled monitor performs the same integrity checks before collecting or committing telemetry.

Passing these checks does not establish that an observation is economically true; it establishes that the research state is coherent, auditable, and scored according to the declared rules in `AGENTS.md` and `docs/METHODOLOGY.md`.
