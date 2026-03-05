---
name: fitmanager-responsive-adaptive-ui
description: Use when optimizing FitManager frontend pages/components for tablet and mobile. Apply to dashboard, CRM lists, cards, forms, and operational boards to preserve touch usability, readable metrics, controlled density, and desktop parity.
---

# FitManager Responsive Adaptive UI

## Core Objective

Deliver CRM screens that stay:

- fast to scan on desktop;
- clear and balanced on tablet;
- touch-usable and compact on mobile.

## Workflow

1. Map screen priorities before changing classes:
   - primary action;
   - primary metric;
   - secondary metadata.
2. Set breakpoint behavior explicitly:
   - mobile (`<640px`): stacked layout, compact spacing, touch-first controls;
   - tablet (`640-1023px`): restore split boards where useful (`md:grid-cols-2`);
   - desktop (`>=1024px`): keep existing density and hierarchy.
3. Apply density rules:
   - keep list-heavy panels at fixed height with internal scroll;
   - reduce spacing before reducing typography;
   - keep operational numbers in `tabular-nums` with strong size contrast;
   - keep interactive controls at least `h-9`, prefer `h-10` for primary actions.
4. Preserve hierarchy:
   - title > primary number > secondary detail;
   - keep status/category visible across breakpoints;
   - avoid pushing critical controls below excessive card content.
5. Verify quickly:
   - inspect at 390px, 768px, and 1024px;
   - ensure no horizontal overflow or clipped controls;
   - lint touched frontend files.

## Reference

Read `references/responsive-density-matrix.md` when tuning spacing and typography.

## Red Flags

- mobile cards that grow without bound because lists are not scroll-contained;
- tiny numeric counters or status labels after breakpoint tweaks;
- tablet layouts collapsing into long single-column pages without reason;
- mobile fixes that degrade desktop readability.
