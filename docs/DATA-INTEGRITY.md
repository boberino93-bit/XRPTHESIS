# Research Data Integrity Rules

The thesis score is only useful if the committed research state is internally consistent and reproducible. `scripts/score_thesis.py` therefore validates claims, evidence, predictions, and the generated score report before CI or scheduled monitoring proceeds.

## Claims

Each claim must have a unique `claim_id` and all required descriptive fields populated. `gate` must be `true` or `false`. H1, H3, and H8 must exist and remain marked as gates because the scoring/classification logic explicitly depends on them.

## Evidence

Each evidence row must:

- have a unique `evidence_id`;
- reference an existing claim;
- use a valid direction (`support`, `neutral`, `contradict`);
- use a declared source-quality class (A-D) and evidence status;
- use a numeric weight from 1 through 5;
- have a valid non-future `observed_date`;
- include nonblank fact, interpretation, and source fields;
- use `http` or `https` source URLs (multiple URLs may be separated by semicolons);
- not duplicate an existing normalized source+fact observation.

Facts and interpretations remain separate. A duplicate source may support multiple distinct observations, but the same source+fact pair must not be counted twice.

## Predictions

Each prediction must have a unique `prediction_id`, reference an existing claim, use declared direction/status values, and contain coherent dates:

```text
registered_date <= start_date <= evaluation_date
```

Registration dates may not be in the future relative to validation time. Failed or expired predictions remain in the registry rather than being silently rewritten.

## Deterministic scoring report

`reports/latest-score.md` is generated from the committed claims, evidence, and predictions. It uses the maximum evidence date as its cutoff instead of a runtime timestamp, so identical research state produces identical output.

Run:

```bash
python scripts/score_thesis.py
```

to regenerate the report, or:

```bash
python scripts/score_thesis.py --check
```

to fail if the research data are malformed or the committed report is stale.

## CI and monitoring

Pull requests and pushes to `main` compile the Python code, run regression tests, and run `score_thesis.py --check`. The scheduled monitoring workflow runs the same integrity checks before collecting or committing telemetry.

Research-state changes should therefore fail before automation can commit new telemetry if the ledger, prediction registry, gate definitions, or generated report become inconsistent.
