# Assistant Guide Routing Patterns

## Intent Split

- `command_intent`: candidate for parse/commit path.
- `guide_intent`: answer + chapter link + route hint.
- `uncertain_intent`: clarification prompt before any operation.

## Response Shape (Suggested)

```json
{
  "mode": "guide",
  "answer": "Per registrare un cliente, apri la pagina Clienti e usa Nuovo Cliente.",
  "guide_ref": "clienti.creazione",
  "next_action": {
    "label": "Apri Clienti",
    "href": "/clienti?new=1"
  }
}
```

## Fallback Rules

- If parse confidence < threshold, return guide suggestion.
- If required entities missing, return guide + missing fields summary.
- If ambiguity remains unresolved, stay read-only and ask user to disambiguate.

## Audit and Observability

- track guide-intent count vs command-intent count;
- track fallback-to-guide rate on parse failures;
- do not log user raw text with PII in plain form.

