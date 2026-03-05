---
name: fitmanager-dashboard-crm-design
description: Use when redesigning or refining FitManager dashboard and overview UI in frontend dashboard pages/components. Focus on CRM-grade visual hierarchy, metric readability, privacy-safe non-financial presentation, and responsive layout decisions for agenda, alerts, and operational cards.
---

# FitManager Dashboard CRM Design

## Core Objective

Design dashboard blocks that let the operator scan in 3 seconds:

- what needs action now;
- which numbers matter first;
- where to click next.

## Workflow

1. Map information hierarchy before moving elements:
   - primary metric (largest number)
   - secondary breakdown (supporting counters)
   - action control (button/link)
2. Build balanced layout:
   - avoid single full-width repetitive rows for alerts
   - prefer card grids or two-column boards with clear rhythm
   - keep agenda and operational numbers in the first viewport
3. Apply metric typography scale:
   - primary metric: `text-2xl` or `text-3xl`, `font-extrabold`, `tabular-nums`
   - secondary metric: `text-lg` or `text-xl`, `font-bold`
   - labels/meta: `text-xs` or `text-[11px]` with muted color
4. Improve table-like blocks (agenda):
   - separate the time block from content block
   - keep event title stronger than notes/client subtitle
   - show category badge on desktop and compact fallback on mobile
5. Preserve product constraints:
   - no financial amounts in default dashboard overview
   - explicit loading/error/empty states remain visible
6. Verify:
   - lint touched frontend files
   - check desktop and mobile readability
   - confirm no key metric truncation or overflow

## Layout Patterns to Prefer

- Board layout: left column for plan/agenda, right column for alerts/todo.
- Alert panel: compact cards with severity badge and CTA; avoid long row lists.
- KPI cards: one dominant value and one short subtitle.
- Weekly breakdown cards: total prominent, sub-counters in small tiles.

## Red Flags

- Primary numbers rendered at `text-sm` or below.
- More than three visual hierarchies inside one card.
- Dense horizontal rows with tiny status text.
- Category/status hidden on mobile.
- UI changes that violate privacy-safe dashboard policy.
