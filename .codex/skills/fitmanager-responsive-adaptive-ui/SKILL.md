---
name: fitmanager-responsive-adaptive-ui
description: Use when optimizing FitManager frontend pages/components for tablet and mobile. Apply to dashboard, CRM lists, cards, forms, record pages, and operational workspaces to preserve touch usability, readable metrics, controlled density, and the page's chosen desktop identity.
---

# FitManager Responsive Adaptive UI

## Core Objective

Deliver CRM screens that stay:

- fast to scan on desktop;
- clear and balanced on tablet;
- touch-usable and compact on mobile;
- recognizably the same surface across breakpoints.

## Workflow

1. Map screen priorities before changing classes:
   - page archetype (`overview`, `workspace`, `record page`, `finance dossier`);
   - primary action;
   - primary metric;
   - secondary metadata.
2. Set breakpoint behavior explicitly:
   - mobile (`<640px`): stacked layout, compact spacing, touch-first controls;
   - tablet (`640-1023px`): restore split boards, queue/detail pairs, or dossier layouts only when they strengthen the chosen page archetype;
   - desktop (`>=1024px`): keep existing density, hierarchy, and page identity.
3. Apply density rules:
   - keep list-heavy panels at fixed height with internal scroll when it protects scan speed or selection continuity;
   - reduce spacing before reducing typography;
   - keep operational numbers in `tabular-nums` with strong size contrast;
   - keep interactive controls at least `h-9`, prefer `h-10` for primary actions.
4. Preserve hierarchy:
   - title > primary number > secondary detail;
   - keep status/category visible across breakpoints;
   - avoid pushing critical controls below excessive card content;
   - keep selected case, active record context, or current action obvious after stacking.
5. Verify quickly:
   - inspect at 390px, 768px, and 1024px;
   - ensure no horizontal overflow or clipped controls;
   - ensure the mobile version still feels like the same product surface, not a generic pile of cards;
   - lint touched frontend files.

## Reference

Read `references/responsive-density-matrix.md` when tuning spacing and typography.

Pair this skill with the surface-specific skill that matches the page:

- `fitmanager-dashboard-crm-design` for overview pages;
- `fitmanager-operational-workspace-design` for action-first workspaces and queues;
- `fitmanager-crm-record-page-design` for record/detail/hub pages.

## Red Flags

- mobile cards that grow without bound because lists are not scroll-contained;
- tiny numeric counters or status labels after breakpoint tweaks;
- tablet layouts collapsing into long single-column pages without reason;
- responsive cleanup that erases the identity of a workspace or record page;
- mobile fixes that degrade desktop readability.
