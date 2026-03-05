# 05 - Contratti e Pagamenti

## Chapter Metadata

- Primary route(s): `/contratti`, `/contratti/[id]`
- Primary user goal: gestire pacchetti, rate e stato economico contrattuale
- Related assistant prompts:
  - `> registra pagamento contanti 80 euro`
  - `> crea movimento entrata 120 euro`

## 1) Cosa puoi fare qui

Creare contratti, monitorare rate e mantenere ordine sui pagamenti.

## 2) Passi consigliati

1. Vai su `/contratti` e crea un nuovo contratto.
2. Collega il contratto al cliente corretto.
3. Definisci prezzo, date e piano rate.
4. Apri il dettaglio contratto (`/contratti/[id]`) per pagare, modificare o revocare pagamenti.
5. Controlla badge stato (in corso, in ritardo, saldato, insolvente).

## 3) Errori comuni

- Errore: pagamento registrato sulla rata sbagliata.
- Perche succede: selezione rapida senza controllo scadenza/importo residuo.
- Come risolvere: verifica sempre scadenza, residuo e storico prima di confermare.

## 4) Troubleshooting

- Problema: rata appare non allineata dopo una revoca.
- Azione: ricarica dettaglio contratto e verifica storico pagamenti.
- Problema: cliente senza contratto attivo ma con richieste agenda PT.
- Azione: crea o riattiva contratto prima di saturare planning.

## 5) Quick Actions

- Shortcut: `Ctrl+K` -> "Nuovo Contratto"
- Related page: `/contratti?new=1`
- Related assistant example: `> registra entrata 100 euro contanti`
- Guida illustrata: `../illustrated/flow-05-contratti-rate.md`
