# 03 - Agenda e Appuntamenti

## Chapter Metadata

- Primary route(s): `/agenda`
- Primary user goal: pianificare, aggiornare e chiudere appuntamenti in modo veloce
- Related assistant prompts:
  - `> luca domani alle 17 pt`
  - `> crea appuntamento colloquio oggi alle 19`

## 1) Cosa puoi fare qui

Gestire calendario, eventi e stati appuntamenti senza uscire dal flusso operativo.

## 2) Passi consigliati

1. Apri `/agenda` e scegli la vista (giorno/settimana/mese).
2. Crea un evento da bottone "Nuovo" o da slot calendario.
3. Imposta categoria, cliente (se presente), orario e stato.
4. Aggiorna lo stato al termine della sessione.
5. Usa i filtri categoria/stato per focalizzare il planning.

## 3) Errori comuni

- Errore: evento PT senza cliente associato.
- Perche succede: creazione rapida con campi incompleti.
- Come risolvere: modifica evento e collega il cliente corretto.

## 4) Troubleshooting

- Problema: evento non visibile nel range atteso.
- Azione: verifica range data corrente, filtri attivi e stato evento.
- Problema: conflitti di orario.
- Azione: sposta evento via drag and drop o modifica orario nel form.

## 5) Quick Actions

- Shortcut: `Ctrl+K` -> "Agenda" / "Nuova Sessione"
- Related page: `/agenda?newEvent=1`
- Related assistant example: `> anna venerdi alle 18 pt`

