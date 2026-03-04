# UPG-2026-03-04-04 - Assistant API Contract (V1)

## Metadata

- Upgrade ID: UPG-2026-03-04-04
- Date: 2026-03-04
- Owner: Codex
- Area: API
- Priority: high
- Target release: test_react

## Goal

Definire il contratto stabile tra frontend Command Palette e backend Assistant:

- `POST /api/assistant/parse` (read-only)
- `POST /api/assistant/commit` (write esplicito)

## Endpoint 1: Parse

### Request

`POST /api/assistant/parse`

```json
{
  "input_text": "Marco Rossi squat 80kg 4x8 domani alle 18",
  "context": {
    "active_page": "/clienti/12",
    "active_client_id": 12,
    "timezone": "Europe/Rome"
  },
  "options": {
    "max_operations": 5,
    "strict_mode": false
  }
}
```

### Response

```json
{
  "correlation_id": "a9e8d5de-54fe-49c1-bbd6-f8d2f3f08d13",
  "normalized_text": "marco rossi squat 80 kg 4x8 domani alle 18:00",
  "overall_confidence": 0.89,
  "operations": [
    {
      "operation_id": "op_1",
      "domain": "agenda",
      "action": "create_event",
      "confidence": 0.89,
      "status": "ready",
      "payload": {
        "categoria": "PT",
        "titolo": "Sessione PT - Squat",
        "id_cliente": 12,
        "data_inizio": "2026-03-05T18:00:00+01:00",
        "data_fine": "2026-03-05T19:00:00+01:00",
        "note": "Squat 80kg 4x8"
      },
      "entities": [
        {
          "type": "client",
          "value": "Marco Rossi",
          "resolved_id": 12,
          "resolution_score": 0.97
        }
      ],
      "warnings": []
    }
  ],
  "ambiguities": [],
  "missing_fields": [],
  "preview": {
    "title": "1 operazione pronta",
    "items": [
      {
        "label": "Evento",
        "value": "Marco Rossi - 05/03/2026 18:00"
      }
    ]
  }
}
```

### Parse Status Values

- `ready`: operazione pronta al commit.
- `needs_confirmation`: ambiguo ma risolvibile da UI.
- `blocked`: dati insufficienti o non validi.

## Endpoint 2: Commit

### Request

`POST /api/assistant/commit`

```json
{
  "correlation_id": "a9e8d5de-54fe-49c1-bbd6-f8d2f3f08d13",
  "input_text": "Marco Rossi squat 80kg 4x8 domani alle 18",
  "operations": [
    {
      "operation_id": "op_1",
      "domain": "agenda",
      "action": "create_event",
      "payload": {
        "categoria": "PT",
        "titolo": "Sessione PT - Squat",
        "id_cliente": 12,
        "data_inizio": "2026-03-05T18:00:00+01:00",
        "data_fine": "2026-03-05T19:00:00+01:00",
        "note": "Squat 80kg 4x8"
      }
    }
  ],
  "client_resolutions": [
    {
      "token": "marco rossi",
      "id_cliente": 12
    }
  ]
}
```

### Response

```json
{
  "correlation_id": "a9e8d5de-54fe-49c1-bbd6-f8d2f3f08d13",
  "summary": {
    "total": 1,
    "success": 1,
    "failed": 0
  },
  "results": [
    {
      "operation_id": "op_1",
      "status": "success",
      "domain": "agenda",
      "action": "create_event",
      "resource_id": 988,
      "message": "Evento creato"
    }
  ],
  "invalidate_query_keys": [
    ["events"],
    ["dashboard"],
    ["clients"],
    ["contracts"],
    ["contract"]
  ]
}
```

## Error Model

### HTTP Status

- `200`: parse/commit processato con almeno un risultato.
- `400`: payload commit invalido.
- `409`: conflitto dominio (es. overlap agenda).
- `422`: dati semanticamente non validi.
- `500`: errore inatteso.

### Error payload

```json
{
  "correlation_id": "a9e8d5de-54fe-49c1-bbd6-f8d2f3f08d13",
  "error_code": "ASSISTANT_VALIDATION_ERROR",
  "message": "Data fine deve essere dopo data inizio",
  "details": {
    "operation_id": "op_1",
    "field": "data_fine"
  }
}
```

## Compatibility Rules

- Il backend Assistant non espone `trainer_id` in input.
- Il commit non bypassa mai endpoint dominio esistenti.
- Il frontend deve trattare `invalidate_query_keys` come hint; le invalidazioni canoniche restano lato hook.

## Schema Constraints

- `input_text` max 600 char.
- `operations` max 10 in commit.
- `domain` e `action` vincolati a enum server.
- `payload` validato contro schema dominio target prima dell'esecuzione.

## Audit and Traceability

- Ogni parse/commit genera `correlation_id`.
- Ogni result commit include `operation_id`.
- Errori dominio riportano messaggio utente-safe + dettaglio strutturato.
