---
name: fitmanager-crm-record-page-design
description: Use when redesigning FitManager CRM record pages, entity hubs, and detail surfaces such as client profiles, contract detail pages, or workout detail pages. Focus on canonical record structure, quick actions, timeline/context, and cross-module continuity without reducing the page to dashboard-style card mosaics.
---

# FitManager CRM Record Page Design

## When To Use

Use this skill for entity-centric surfaces whose main job is to understand and operate on one record:

- client profile and client hub pages;
- contract detail pages;
- workout/program detail pages;
- any other page where one entity is the canonical subject.

Do not use this as the primary skill for:

- top-level dashboards;
- action-first queues and workspaces;
- finance ledgers centered on many rows rather than one record.

## Core Objective

A record page must make the entity legible immediately:

- who or what this record is;
- what state it is in now;
- what the operator can do next;
- what happened recently and what matters around it.

## Workflow

1. Establish the record spine first:
   - identity header;
   - state or status;
   - key summary facts;
   - quick actions close to the header.
2. Organize sections by operator intent:
   - summary first;
   - current operational context second;
   - history, timeline, related objects, and deeper sections after that.
   Tabs are a tool, not a default requirement.
3. Create one canonical history path:
   - timeline;
   - recent activity;
   - linked operational moments;
   - clinically relevant or business-relevant milestones.
   The operator should not have to infer the record story from disconnected cards.
4. Keep actionability near identity:
   - schedule, message, collect, edit, review, renew, or continue should live close to the record header when relevant;
   - avoid hiding the next likely action deep inside tabs or low-priority side panels.
5. Preserve cross-module continuity:
   - related entities should feel connected, not dumped as raw links;
   - if the user arrived from a workspace, preserve origin context and a clean way back.
6. Prefer narrative density over card spray:
   - use cards when they create separation with meaning;
   - otherwise favor stronger section rhythm and aligned metadata blocks.
7. Verify responsive behavior without losing the record shape:
   - identity and actions remain early;
   - timeline/history stays understandable after stacking;
   - the page still reads like a record hub, not a dashboard remix.

## Design Principles

- One canonical subject, one canonical story.
- Identity and state must be obvious before secondary modules.
- Quick actions belong near the record, not scattered across the page.
- Related modules should enrich the record, not fragment it.
- The page can be rich without becoming visually noisy.

## Red Flags

- the detail page looks like a miniature dashboard;
- many equal KPI cards replace a clear record spine;
- the next action is hidden behind tabs by default;
- there is no canonical history or timeline;
- related entities feel disconnected from the main record;
- return context from workspace or search is lost;
- mobile stacking turns the page into an undifferentiated wall of cards.
