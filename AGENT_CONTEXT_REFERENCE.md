# XRP Thesis Agent Context Reference

Status: orientation only; not authorization.

Project ID: `xrp-thesis`  
Repository: `boberino93-bit/XRPTHESIS`

## Purpose

This project tests and attempts to falsify a thesis about XRP, XRPL, Ripple, RLUSD, institutional adoption, bridge-asset routing/value capture, tokenization, market structure, and relevant macro conditions.

## Startup order

1. Load `AGENT_BOOTSTRAP.json`.
2. Load `AUTHORITY_SECURITY_OVERLAY.json` and the pinned central governance.
3. Resolve current project HOLD state before new work and recheck it between bounded work units.
4. Load `MASTER_HANDOFF.json` and `AGENTS.md`.
5. Read `docs/THESIS.md` and `docs/METHODOLOGY.md` before changing thesis state.
6. Inspect current evidence/data/reports and exact repository revision before selecting work.

## Core epistemic rules

Keep Ripple, XRPL, RLUSD, and XRP distinct. Prefer primary evidence. Actively seek disconfirming evidence. Do not infer XRP-specific value capture from ecosystem adoption without an explicit measurable mechanism. Preserve failed predictions and uncertainty.

## Continuation and holds

An ordinary human status/question interruption is not cancellation; resume the prior execution cursor automatically after responding. If one branch needs human input, block only that branch and continue other safe work. A valid authenticated project HOLD is different: checkpoint useful partial state and stop XRP work until the governed resume condition is satisfied.

This file never grants mutation authority, authenticates a human, creates a task, or overrides current human instructions.
