# H1 Historical Data Access Feasibility

Date: 2026-10-05
Primary claim: H1 — Bridge-asset utility
Purpose: determine whether executed-route telemetry can be built from public/full-history XRPL infrastructure without treating a third-party analytics product as the source of truth.

## Conclusion

A 6–12 month transaction-level H1 run is technically feasible from ledger-native public data.

The best public starting points are full-history XRPL endpoints, especially Clio-backed clusters, because the classifier needs validated historical transactions **with metadata**, not only present ledger state.

This is feasible research infrastructure, but public endpoints are not guaranteed for sustained bulk extraction. The implementation should therefore support checkpointing, multiple compatible endpoints, polite rate limiting, and later migration to a dedicated/paid/full-history server if the historical run becomes too heavy.

## Primary-source findings

### Full history exists as a public service

XRPL's official ledger-history documentation states that some servers retain the full ledger history. It identifies Ripple's `s2.ripple.com` as a public full-history service and notes that community full-history servers are also available.

Source:
- https://xrpl.org/docs/concepts/networks-and-servers/ledger-history

### Official public-server list identifies full-history clusters

The XRPL public-server documentation currently lists:

- Honeycluster mainnet — full history with Clio
- InFTF / xrplcluster — full history
- Ripple `s2.ripple.com` — full-history server cluster

It also warns that Ripple public servers are not intended for sustained or business use and may become unavailable.

Source:
- https://xrpl.org/docs/tutorials/public-servers

### Clio is designed for historical validated read throughput

Official documentation describes Clio as an API server optimized for validated historical ledger and transaction data, with scalable read throughput. It stores transaction metadata and ledger data and returns validated data by default.

Source:
- https://xrpl.org/docs/concepts/networks-and-servers/the-clio-server

This is directly suitable for H1 because the classifier depends on immutable transaction metadata.

### Historical ledgers can be fetched with expanded transactions

The Clio `ledger` method can request a specific historical ledger with:

- `transactions: true`
- `expand: true`

and returns full transaction representations for that ledger. This provides a deterministic ledger-by-ledger extraction path for the H1 classifier.

Source:
- https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/clio-methods/ledger-clio

### Time can be mapped to ledger index

The Clio-only `ledger_index` method maps an ISO timestamp to the last closed ledger at that time. This is useful for reproducible date-bounded studies: convert study start/end timestamps to ledger indexes, then iterate a closed ledger-index range.

Source:
- https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/clio-methods/ledger_index

## Recommended extraction architecture

### Phase 1 — validation sample

Use a Clio-backed full-history public endpoint.

1. Resolve UTC start/end dates to ledger indexes using `ledger_index` where supported.
2. Iterate ledgers in ascending order.
3. Request each ledger with expanded transactions.
4. Persist raw transaction + metadata records for candidate `Payment` and `OfferCreate` transactions.
5. Run execution classification locally.
6. Write periodic checkpoints so a rate-limit or endpoint failure does not restart the study.

Target: 30 consecutive days.

### Phase 2 — historical panel

After classifier validation, expand to 6–12 months.

Implement endpoint abstraction so collection can rotate/fail over among compatible sources without changing the analytical semantics.

Suggested endpoint priority for research testing:

1. Clio-backed full-history community endpoint
2. alternate full-history community endpoint
3. Ripple `s2` as fallback, respecting public-service limits
4. dedicated paid/self-hosted infrastructure for sustained bulk runs

No endpoint should be treated as an independent evidence source when all are serving the same canonical ledger. The **ledger data** is the primary source; endpoints are transport/infrastructure.

## Data-volume implication

Full XRPL history is operationally large. Official XRPL documentation reported approximately 39 TB for full history as of 2026-01-25, growing by roughly 12 GB/day for a self-hosted full-history `xrpld` configuration.

Source:
- https://xrpl.org/docs/infrastructure/configuration/data-retention/configure-full-history

This makes self-hosting full history a later infrastructure decision, not a prerequisite for the first H1 empirical study.

## Reproducibility requirements

For every historical run record:

- endpoint used,
- API version,
- UTC start/end timestamps,
- resolved start/end ledger indexes,
- actual first/last successfully processed ledger,
- gaps / retry failures,
- count of ledgers processed,
- count of candidate transactions,
- count and share of unresolved executions,
- code commit SHA,
- output dataset checksum.

If the endpoint's available range does not fully cover the requested study window, fail loudly or mark the run incomplete. Do not silently analyze a shorter period.

## Evidence quality

The transaction and metadata payloads are canonical ledger data and therefore qualify as Class A evidence under the repository methodology when collected and interpreted correctly.

The fact that a public operator transports the API response does not downgrade the underlying canonical ledger evidence, but reproducibility should include cross-checking sample ledgers/transactions against a second endpoint.

## Immediate implication

No H1 score change.

The unresolved blocker is no longer data existence. It is implementation and classifier validation. The next research/engineering handoff is a checkpointed ledger collector plus transaction fixtures that prove the route classifier can distinguish direct, fully XRP-bridged, mixed, endpoint-XRP, and unresolved executions.