# UPG-2026-03-11-22 - Oggi Decision Path Slimdown v1

## Contesto

Le skill e le spec di `/oggi` hanno aiutato nelle iterazioni precedenti, ma ora parte del materiale
storico rischia di agire come prescrizione viva.

I blocchi principali osservati:

- spec `Oggi` non piu' allineate alla route reale;
- benchmark e refactor storici letti come layout target;
- skill responsive/workspace abbastanza forti da sembrare template invece che strumenti.

## Obiettivo

Ridurre il path decisionale attivo per il prossimo redesign di `/oggi` senza toccare il runtime:

- tenere vive le skill utili;
- renderle meno rigide;
- declassare le spec storiche a contesto o benchmark.

## File toccati

- `AGENTS.md`
- `.codex/skills/fitmanager-operational-workspace-design/SKILL.md`
- `.codex/skills/fitmanager-responsive-adaptive-ui/SKILL.md`
- `.codex/skills/fitmanager-responsive-adaptive-ui/references/responsive-density-matrix.md`
- `docs/upgrades/specs/UPG-2026-03-09-08-workspace-oggi-v2-stack-refactor.md`
- `docs/upgrades/specs/UPG-2026-03-11-16-oggi-v3-launch-workspace-spec.md`
- `docs/upgrades/specs/UPG-2026-03-11-17-oggi-v3-frontend-workspace-refactor.md`
- `docs/upgrades/specs/UPG-2026-03-11-18-oggi-visual-density-pass-v1.md`
- `docs/upgrades/specs/UPG-2026-03-11-19-oggi-zero-based-redesign-benchmark-v1.md`
- `docs/upgrades/specs/UPG-2026-03-11-20-oggi-v4-zero-based-redesign-v1.md`

## Decisioni chiave

1. Le skill restano attive, ma vengono rese piu' chiaramente strumentali e meno template-driven.
2. Le spec `Oggi` storiche non vengono cancellate, ma smettono di essere guida attiva.
3. Le spec upgrade restano storiche di default anche in `AGENTS.md`, salvo task che le richiamano esplicitamente.

## Verifica prevista

- review manuale dei file toccati
- grep mirato su note storiche/benchmark
- `git diff --check`

## Rischi residui

1. Alcune spec storiche `workspace/*` restano comunque nel repository e possono ancora essere aperte per errore.
2. La route reale `/oggi` ha ancora drift rispetto a parte del materiale storico gia scritto.
3. Il vero sblocco richiedera' un task runtime che rilegga la pagina a partire dal codice attuale, non dalle spec storiche.
