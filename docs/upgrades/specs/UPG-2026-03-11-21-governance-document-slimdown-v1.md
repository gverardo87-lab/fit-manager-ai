# UPG-2026-03-11-21 - Governance Document Slimdown v1

## Contesto

La governance del repository era diventata difficile da usare per un coding agent:

- `CLAUDE.md` mescolava manifesto, playbook operativo, release notes, snapshot e memoria storica
- `codex.md` e `docs/ai-sync/MULTI_AGENT_SYNC.md` ripetevano regole gia presenti altrove
- il perimetro launch viveva disperso tra `CLAUDE.md` e spec storiche

Il risultato era una superficie troppo larga da leggere prima di agire.

## Obiettivo

Ridurre la superficie autorevole a quattro documenti, separando:

- regole vive di esecuzione
- verita' di prodotto
- scope del lancio
- lezioni storiche

senza toccare backend o frontend.

## File toccati

- `AGENTS.md`
- `MANIFESTO.md`
- `LAUNCH_SCOPE.md`
- `POSTMORTEMS.md`
- `CLAUDE.md`
- `codex.md`
- `docs/ai-sync/MULTI_AGENT_SYNC.md`
- `docs/ai-sync/WORKBOARD.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`

## Decisioni chiave

1. `AGENTS.md` diventa l'unico contratto operativo per gli agenti.
2. `MANIFESTO.md` contiene solo visione e invarianti stabili di prodotto.
3. `LAUNCH_SCOPE.md` contiene solo il perimetro utile al lancio e le anti-scope-creep rules.
4. `POSTMORTEMS.md` raccoglie lezioni concrete senza trasformarle in nuove policy.
5. `CLAUDE.md`, `codex.md` e `docs/ai-sync/MULTI_AGENT_SYNC.md` restano come shim compatibili e non devono piu' accumulare regole.

## Mappa di migrazione

- da `CLAUDE.md`:
  - missione/posizionamento -> `MANIFESTO.md`
  - workflow operativo e guardrail -> `AGENTS.md`
  - launch/distribuzione -> `LAUNCH_SCOPE.md`
  - incidenti e lezioni -> `POSTMORTEMS.md`
- da `codex.md`:
  - metodo operativo ridondante -> consolidato in `AGENTS.md`
- da `docs/ai-sync/MULTI_AGENT_SYNC.md`:
  - regole di coordinamento -> consolidate in `AGENTS.md`

## Verifica prevista

- review manuale dei 4 documenti target
- review manuale degli shim legacy
- review di coerenza tra `WORKBOARD.md`, `UPGRADE_LOG.md` e `README.md`
- `git diff --check`

## Rischi residui

1. I `CLAUDE.md` layer-specifici restano voluminosi, anche se ora sono consultati solo per il layer toccato.
2. Alcuni runbook e spec storiche continuano a esistere e richiedono disciplina per non essere trattati come regole vive.
3. I riferimenti esterni ai vecchi documenti continuano a funzionare grazie agli shim, ma serve evitare che gli shim ricrescano.

## Next step

Se la frizione documentale resta alta, il passo successivo corretto non e' creare altri file,
ma snellire in un secondo momento i `CLAUDE.md` layer-specifici mantenendo invariati i 4 documenti autorevoli.
