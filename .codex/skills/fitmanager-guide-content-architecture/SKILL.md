---
name: fitmanager-guide-content-architecture
description: Use when designing or updating FitManager user guide chapters, sections, and contextual help content. Enforces welcoming but deterministic guidance aligned with real CRM workflows.
---

# FitManager Guide Content Architecture

## When To Use

Use this skill for:

- user guide chapter planning and writing;
- in-app help content definition;
- FAQ and troubleshooting coverage design;
- route-by-route guide completeness reviews.

## Core Principles

- Keep tone welcoming, clear, and action-first.
- Prefer deterministic instructions over abstract advice.
- Tie each section to an explicit route or workflow.
- Keep privacy-safe examples (no real PII, no financial sensitive defaults).
- Cover both first-run and daily operational scenarios.

## Workflow

1. Map user journey and primary tasks.
2. Define chapter set with stable sequence.
3. For each chapter, include required blocks:
   - when to use this page/flow;
   - step-by-step actions;
   - common mistakes;
   - how to recover.
4. Link each chapter to route(s), CTA(s), and related assistant prompts.
5. Run a coverage pass on all core CRM routes before handoff.

## Mandatory Coverage Matrix

Minimum route coverage:

- `/` dashboard
- `/agenda`
- `/clienti` and `/clienti/[id]`
- `/contratti` and `/contratti/[id]`
- `/cassa`
- `/esercizi` and `/esercizi/[id]`
- `/schede` and `/schede/[id]`
- `/allenamenti`
- `/impostazioni`
- `/setup`
- Command Palette and assistant mode behaviors

## Verification Checklist

- every chapter has explicit next action;
- no dead links or stale route names;
- empty/error/loading guidance exists for critical flows;
- content is consistent with current UI labels.

## Reference

Use `references/guide-chapter-template.md` as baseline structure.

