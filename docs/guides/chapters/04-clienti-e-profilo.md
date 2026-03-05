# 04 - Clienti e Profilo

## Chapter Metadata

- Primary route(s): `/clienti`, `/clienti/[id]`, `/clienti/[id]/anamnesi`, `/clienti/[id]/misurazioni`, `/clienti/[id]/progressi`
- Primary user goal: gestire anagrafica e storia operativa del cliente
- Related assistant prompts:
  - `> crea cliente marco rossi`
  - `> marco peso 82 massa grassa 18`

## 1) Cosa puoi fare qui

Creare clienti, aggiornarli e monitorare anamnesi, misurazioni e progresso.

## 2) Passi consigliati

1. Vai su `/clienti` e crea il nuovo cliente.
2. Compila i dati obbligatori e salva.
3. Apri il profilo (`/clienti/[id]`) per vedere panoramica, contratti e sessioni.
4. Completa l'anamnesi in tab dedicata.
5. Registra misurazioni iniziali e successive.

## 3) Errori comuni

- Errore: dati cliente incompleti (contatti o stato) e difficolta nei follow-up.
- Perche succede: inserimento veloce senza revisione finale.
- Come risolvere: aggiorna subito i campi chiave e usa note interne in modo ordinato.

## 4) Troubleshooting

- Problema: cliente duplicato in lista.
- Azione: verifica email/telefono e mantieni un solo profilo aggiornato.
- Problema: misurazioni non coerenti.
- Azione: controlla data e metrica selezionata prima del salvataggio.

## 5) Quick Actions

- Shortcut: `Ctrl+K` -> "Nuovo Cliente"
- Related page: `/clienti?new=1`
- Related assistant example: `> aggiungi cliente giulia bianchi`
- Guida illustrata: `../illustrated/flow-04-clienti-profilo.md`
