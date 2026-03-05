---
name: fitmanager-assistant-guide-linking
description: Use when connecting FitManager assistant NLP/NPL flows with guide retrieval and contextual help. Enforces strict separation between read-only help and write operations.
---

# FitManager Assistant Guide Linking

## When To Use

Use this skill for:

- assistant help-intent routing;
- guide retrieval endpoints or adapters;
- command palette help mode integration;
- fallback from failed command parse to guide suggestions.

## Core Safety Contract

- Help requests are read-only.
- Action requests remain explicit parse/commit flows.
- Never auto-execute writes from ambiguous help prompts.
- Preserve ownership and privacy constraints in all returned suggestions.

## Routing Pattern

1. Classify user request:
   - command intent (write-capable flow),
   - guide intent (read-only flow),
   - ambiguous (ask clarifying question).
2. For guide intent:
   - return concise answer,
   - return chapter/section reference,
   - return next best action link.
3. For command intent:
   - keep current parse/preview/confirm guardrails.
4. For parse failure:
   - propose relevant guide chapter instead of dead-end error.

## Integration Checklist

- API schemas remain explicit (`help` vs `command` responses).
- Frontend state clearly distinguishes help result from commitable result.
- React Query invalidation applies only to commit path.
- Assistant UX keeps keyboard flow usable in both modes.

## Verification Checklist

- no write side effects in help mode;
- fallback quality for low-confidence assistant parse;
- no sensitive fields leaked in help snippets;
- links point to valid routes or guide anchors.

## Reference

Use `references/assistant-guide-routing-patterns.md`.

