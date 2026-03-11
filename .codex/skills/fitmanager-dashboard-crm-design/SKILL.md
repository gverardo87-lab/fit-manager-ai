---
name: fitmanager-dashboard-crm-design
description: Use when redesigning or refining FitManager dashboard overviews and post-login summary screens. Focus on scan speed, trustworthy summary, privacy-safe overview, and clean next-click paths without forcing the dashboard to absorb full workflows.
---

# FitManager Dashboard CRM Design

## When To Use

Use this skill for overview surfaces whose main job is to orient the operator quickly:

- post-login dashboards;
- summary strips or overview sections inside broader CRM pages;
- KPI plus agenda/alerts surfaces that summarize work rather than execute it.

Do not use this as the primary skill for:

- action-first workspaces or queues such as `Oggi`, `Rinnovi & Incassi`, or monitoring boards;
- CRM record/detail/hub pages such as client profiles or contract detail screens;
- finance ledgers or dossier-style detail surfaces.

For those cases, route to `fitmanager-operational-workspace-design` or
`fitmanager-crm-record-page-design` instead.

## Core Objective

The dashboard must answer, within about three seconds:

- what is the state of the business day;
- what requires attention soon;
- where the operator should click next.

It is an overview map, not the full workplace.

## Workflow

1. Clarify the page promise before drawing layout:
   - what the operator must understand immediately;
   - which deeper workflows this page should hand off to;
   - which sensitive domains must stay out of default view.
2. Choose overview zones deliberately:
   - top summary or health;
   - immediate operational picture;
   - upcoming commitments;
   - alerts, readiness, or opportunities.
   Not every dashboard needs every zone.
3. Choose layout by content, not by habit:
   - cards, split boards, asymmetric bands, and summary rails are all allowed;
   - use two-column boards only when they improve scan and comparison;
   - keep the first viewport focused on orientation, not on exhaustive detail.
4. Keep metrics honest and privacy-safe:
   - do not derive fake confidence from partial datasets;
   - avoid financial detail in generic overview surfaces unless the page is explicitly finance-only;
   - keep statuses and counts more prominent than decorative chrome.
5. Keep CTA discipline strong:
   - overview actions should route cleanly into the correct working surface;
   - avoid turning dashboard widgets into miniature versions of full modules unless the action is truly lightweight.
6. Verify responsive behavior without flattening the page:
   - preserve the page's summary hierarchy;
   - let the most important overview block stay visible early on mobile;
   - keep the dashboard distinct from workspaces even after stacking.

## Design Principles

- Summary first, detail second.
- A small number of strong signals beats many equal cards.
- Visual originality is allowed, but only if scan speed improves.
- Repeated dashboard motifs are patterns, not requirements.
- The dashboard should point toward work, not trap the user inside summary widgets.

## Red Flags

- the page starts feeling like a second `Oggi`;
- every section becomes an equal-sized card regardless of importance;
- a symmetry-first layout forces unrelated blocks into a generic board;
- the operator cannot tell what matters now versus what is simply informative;
- financial or client-sensitive detail leaks into a generic overview;
- the only way to complete real work becomes staying inside the dashboard.
