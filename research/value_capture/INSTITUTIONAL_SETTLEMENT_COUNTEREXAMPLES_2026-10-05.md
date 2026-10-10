# Institutional XRPL activity vs XRP value capture — 2026-10-05

Status: research workstream / Issue #2 support

## Research question

Does real institutional activity on XRPL create persistent demand for **XRP itself**, or can economically meaningful workflows use XRPL while the principal settlement/liquidity leg is handled by fiat, stablecoins, or legacy financial infrastructure?

This note deliberately separates:

1. XRPL institutional adoption (H2), from
2. XRP-specific value capture (H3).

A successful XRPL deployment is not scored as H3 support unless the disclosed workflow creates measurable XRP routing, inventory, liquidity, collateral, or settlement demand beyond ordinary ledger fees/reserves.

## Case 1 — OUSG cross-border redemption: XRPL asset leg, USD bank cash leg

**Date:** 2026-05-06  
**Stage:** pilot  
**Participants:** Ondo Finance, Ripple, Mastercard, Kinexys by J.P. Morgan  
**Primary source:** https://ondo.finance/blog/ondo-jpmorgan-mastercard-ripple-tokenization

### Source-grounded facts

Ondo reported a cross-border, cross-bank redemption pilot involving its OUSG tokenized U.S. Treasury product. Ripple redeemed a portion of its OUSG holdings on XRPL, and the XRPL asset leg processed in under five seconds.

The associated principal cash leg was not described as an XRP settlement. Ondo initiated a fiat payout instruction through Mastercard Multi-Token Network; Kinexys by J.P. Morgan debited Ondo's Blockchain Deposit Account and delivered U.S. dollar proceeds to Ripple's bank account in Singapore through J.P. Morgan's correspondent banking network.

Ondo explicitly describes the architecture as one leg on a public blockchain and the other on bank infrastructure.

### Interpretation

- **H2:** supportive. This is concrete institutional use of XRPL in a multi-party tokenized-asset workflow.
- **H3:** contradictory to the broad inference that institutional XRPL settlement automatically creates material XRP principal demand. The disclosed principal cash path used USD banking infrastructure, and the source does not identify XRP as the bridge or settlement asset.
- **Important limitation:** this does **not** prove that zero XRP was touched. XRPL transactions still have XRP-denominated fee/reserve mechanics. The narrower finding is that no material XRP principal-routing or inventory requirement is disclosed for this workflow.
- **Scale limitation:** the transaction amount was not disclosed and the event is explicitly a pilot, so it should not be treated as scaled production throughput.

## Case 2 — OUSG's live XRPL mint/redemption design uses RLUSD

**Launch date:** 2025-06-11  
**Stage:** live product  
**Primary source:** https://ondo.finance/blog/ondo-finance-brings-tokenized-treasuries-to-the-xrp-ledger-with-seamless-mint-redeem-via-ripples-rlusd-stablecoin

### Source-grounded facts

Ondo launched OUSG on XRPL with round-the-clock subscription/redemption support using RLUSD. Ondo states that users can convert in and out of OUSG and RLUSD and describes RLUSD as a direct bridge into real-world-asset exposure.

### Interpretation

This is a clear production architecture in which a major XRPL tokenized-asset product can use an issued stablecoin as its principal liquidity/settlement rail. That does not make RLUSD growth bearish for XRP by itself: XRP could still capture value through auto-bridging, XRP/RLUSD market-making inventory, reserves, or other mechanisms. But those mechanisms must be **measured**, not inferred from OUSG/RLUSD volume.

This case is retained as context rather than separately scored in this batch to avoid double-counting the same OUSG architecture.

## Case 3 — CSD BR / BTG Pactual: live XRPL record layer while official settlement stays off-ledger

**Announcement:** 2026-09-29  
**Stage:** live first phase  
**Sources:**

- Ripple/CSD BR announcement: https://ripple.com/ripple-press/csdbr-and-ripple-use-the-xrpl-blockchain-to-expand-brazils-financial-market-infrastructure/
- Independent reporting: https://www.coindesk.com/tech/2026/09/30/xrp-ledger-starts-carrying-fund-records-from-brazil-operator-overseeing-usd4-trillion

### Source-grounded facts

CSD BR, a regulated Brazilian registrar, central securities depository, and settlement-system operator, began using XRPL as an additional layer to mirror ownership records for selected BTG Pactual investment fund shares.

Ripple/CSD BR describe the project as moving from controlled testing to live operation. However, CSD BR's existing systems remain the official source of record for registration, deposit/custody, and settlement. Independent reporting further states that the assets are not being moved onto XRPL in this first phase.

### Interpretation

- **H2:** materially supportive. This is live use of public XRPL infrastructure by a regulated capital-markets operator with real fund records.
- **H3:** neutral at present. The live first phase demonstrates XRPL utility for record/audit/reconciliation while the legally operative custody/settlement layer remains outside XRPL. No XRP-specific inventory or principal-routing requirement is disclosed.
- Future direct issuance/trading on XRPL could change the H3 assessment, but it must be evaluated when production route/settlement data exists.

## What this batch changes

The evidence strengthens the proposition that regulated institutions can use XRPL for genuine financial workflows. It simultaneously weakens the shortcut assumption that those workflows necessarily create material XRP demand.

That is not a contradiction in the research system: **H2 can strengthen while H3 remains uncertain or weakens.**

## Strongest evidence against H3 in this batch

The May 2026 OUSG redemption is the clearest counterexample. A real tokenized asset moved/redeemed on XRPL, while the disclosed cash settlement was a USD payment routed through Mastercard MTN, Kinexys by J.P. Morgan, and correspondent banking. The workflow therefore demonstrates institutional XRPL utility without a disclosed XRP principal-settlement requirement.

## Evidence that would overturn or materially weaken this concern

H3 would strengthen if follow-up data showed one or more of the following at meaningful scale:

- persistent XRP share of cross-currency/pathfinding value,
- OUSG/RLUSD or institutional token flows frequently auto-bridging through XRP because it is the cheapest route,
- material growth in XRP/RLUSD or institutional bridge-pair depth attributable to these workflows,
- institutions disclosing XRP working inventory specifically required for settlement/liquidity,
- direct XRP principal settlement selected over stablecoin/fiat alternatives for economic reasons,
- sustained XRP-specific inventory demand growing with institutional XRPL throughput.

## Data limitations

- The OUSG pilot amount was not disclosed.
- Public sources do not expose route-level XRP inventory or pathfinding data for these institutional workflows.
- Absence of a disclosed XRP principal leg is not proof that no XRP was used for fees/reserves or ancillary operations.
- CSD BR's first phase is a mirroring/verification deployment, not direct on-ledger issuance and settlement.

## Watchlist — not scored yet

- Future CSD BR direct issuance/trading phases on XRPL.
- OUSG XRPL-specific notional/turnover versus fund-wide TVL.
- XRP share of OUSG/RLUSD liquidity and pathfinding.
- Production settlement architecture for new stablecoin corridors such as RLUSD/MXNB.
- Any disclosed institutional XRP inventory associated with these workflows.
