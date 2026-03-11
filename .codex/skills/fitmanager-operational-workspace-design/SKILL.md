---
name: fitmanager-operational-workspace-design
description: Use when redesigning FitManager action-first CRM workspaces, worklists, queues, and cockpits such as Oggi, Rinnovi & Incassi, or monitoring boards. Focus on next-best-action, queue dominance, case context, and strong page identity without defaulting to generic dashboard card grids.
---

# FitManager Operational Workspace Design

## When To Use

Use this skill for surfaces whose main job is to help the operator act now:

- `Oggi`;
- `Rinnovi & Incassi`;
- monitoring boards and readiness queues;
- focused cockpits with case selection plus detail context.

Do not use this as the primary skill for:

- top-level overview dashboards;
- record/detail pages centered on one entity;
- static reports.

## Core Objective

A workspace must make the next move obvious:

- what needs attention now;
- why it matters now;
- what action the trainer can take next;
- what context is needed without leaving the page too early.

## Workflow

1. Define the unit of work:
   - case;
   - task;
   - contract/ledger item;
   - session or readiness issue.
2. Make the work queue dominant:
   - the operator should immediately see where the live workload is;
   - summary metrics are supporting signals, not the page's center of gravity.
3. Choose the page archetype intentionally:
   - queue plus sticky detail;
   - stack plus supporting rail;
   - row dossier plus compact lane headers;
   - dense ledger plus dossier;
   - compact mobile action stack.
   These are starting grammars, not locked templates.
   Card grids are allowed only when they genuinely improve workflow.
   If the workspace shows 4 or more live cases at once, start by testing dense rows or dossier strips
   before defaulting to stacked cards, unless another grammar is clearly faster to act through.
4. Keep action and context adjacent:
   - recommended action;
   - why now;
   - key metadata;
   - related entities or recent activity.
   The user should not need multiple drill-down hops to understand a case.
5. Control density and escalation:
   - critical and due-now work must stand apart from waiting/backlog;
   - bucketing is useful when it changes behavior, not just visual grouping;
   - do not duplicate the same entity in multiple equally urgent blocks without a clear dominance rule.
6. Keep domain boundaries clear:
   - do not leak finance detail into non-finance workspaces;
   - do not overload a single workspace with every possible module concern.
7. Verify responsive behavior with workflow intact:
   - selected case remains obvious;
   - action CTA survives above the fold when needed;
   - stacked mobile layouts still preserve queue -> detail logic.
   - desktop should show real work, not mostly wrappers and intros.

## Density Targets

- Workspace headers should stay compact and rarely exceed roughly `80-96px` on desktop.
- Bucket headers should behave like lane labels, not mini-hero blocks.
- Dense operational rows should usually land around `72-96px` desktop height before expansion.
- If the full card is selectable, avoid adding a second generic `Dettaglio` CTA by default.
- Utility surfaces such as agenda, quick capture, or status summaries should have one visual owner on the page.
- When the operator can act directly from the queue, prefer one strong CTA over multiple equal-weight buttons.

## Design Principles

- Job-first beats module-first.
- Queue dominance beats decorative symmetry.
- Context must travel with the case.
- Strong visual identity is good when it sharpens behavior.
- Metrics should support action, not compete with it.
- Row dossier beats tall card repetition when the queue is dense.
- Quick capture should minimize pre-selection friction when the real-world task starts before perfect association.
- Archetypes are tools, not mandates.

## Red Flags

- the workspace feels like a second dashboard;
- KPI cards dominate more space than the actual work queue;
- the operator cannot tell which item is selected or most urgent;
- actions live far away from the case that triggered them;
- the layout preserves symmetry even when it harms flow;
- mobile stacking destroys the queue -> detail relationship;
- one entity appears multiple times with no clear precedence.
- every case is rendered as a standalone tall card even though the workspace is queue-heavy;
- repeated subtitles, helper copy, and wrappers consume more height than the live cases;
- the same utility surface appears in multiple places with equal visual weight;
- a generic `Dettaglio` button duplicates row selection without adding meaning.
