# 08 - Schede Allenamento

## Chapter Metadata

- Primary route(s): `/schede`, `/schede/[id]`
- Primary user goal: creare, modificare e mantenere schede coerenti con il cliente
- Related assistant prompts:
  - `> apri schede`
  - `> crea sessione allenamento`

## 1) Cosa puoi fare qui

Gestire programmazione allenamento con builder, sessioni e preview.

## 2) Passi consigliati

1. Vai su `/schede` e crea una nuova scheda.
2. Collega la scheda al cliente quando richiesto.
3. Costruisci le sessioni con esercizi e parametri.
4. Controlla la preview per validare struttura e leggibilita.
5. Salva e aggiorna la scheda dopo ogni revisione.

## 3) Errori comuni

- Errore: salvare scheda con blocchi incompleti.
- Perche succede: modifica rapida senza controllo finale.
- Come risolvere: usa sempre il controllo issue prima del salvataggio definitivo.

## 4) Troubleshooting

- Problema: preview non rispecchia l'output atteso.
- Azione: verifica ordine esercizi, serie/ripetizioni e note sessione.
- Problema: scheda non assegnata correttamente al cliente.
- Azione: controlla `id_cliente` associato nel dettaglio scheda.

## 5) Quick Actions

- Shortcut: `Ctrl+K` -> "Schede Allenamento"
- Related page: `/schede`
- Related assistant example: `> apri schede allenamento`

