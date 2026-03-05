# Multi-Agent Workboard

Tabella operativa condivisa tra agenti AI.
Aggiornare prima di iniziare e alla chiusura di ogni task.

## Active

_Nessun task attivo. Wave 4 (UX hardening) da avviare._

## Completed

| Work ID | Owner | Branch | Scope | Commit | Checks | Closed (UTC) | Notes |
|---|---|---|---|---|---|---|---|
| AGT-2026-03-05-13 | Codex | `codex_02` | Dashboard reliability microstep: fix date rollover/local-time safety (no UTC shift su range giorno), refresh automatico a mezzanotte e allineamento label dinamiche header/agenda/settimana | `ddcf2e6` | `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"` | 2026-03-05 | Riduce rischio errori invisibili su dashboard lasciata aperta molte ore, soprattutto fascia notturna |
| AGT-2026-03-05-12 | Codex | `codex_02` | Dashboard responsive microstep: ottimizzazione grafica tablet/mobile (gerarchia, densita, spacing), altezza compatta agenda/live con scroll interno, creazione skill cross-app `fitmanager-responsive-adaptive-ui` e routing in `AGENTS.md` | `ddcf2e6` | `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"` | 2026-03-05 | Foundation riusabile per prossimi redesign mobile/tablet su tutte le pagine CRM, non solo dashboard |
| AGT-2026-03-05-11 | Codex | `codex_02` | Dashboard corrective microstep: ripristino altezza compatta per agenda/live panel con scroll interno agenda sempre attivo (gestione 8/20+ appuntamenti senza allungare pagina) | `afa056a` | `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"` | 2026-03-05 | Corretto regressione UX di densita': pannelli tornati a comportamento operativo compatto |
| AGT-2026-03-05-10 | Codex | `codex_02` | Dashboard microstep 5: bilanciamento visuale professionale (chip categoria settimanale piu' grandi, identita' cromatica per card, live panel con colori legati allo stato operativo) | `4abb9c6` | `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"` | 2026-03-05 | Migliorata scansione a colpo d'occhio: piu' originalita' senza perdere intuizione e pulizia CRM |
| AGT-2026-03-05-09 | Codex | `codex_02` | Dashboard microstep 4: stato appuntamenti modificabile direttamente nelle righe Agenda con select inline e feedback update | `c1afca0` | `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"` | 2026-03-05 | Dashboard evoluta da monitor a strumento operativo: completamento/rinvio/cancellazione senza entrare in Agenda completa |
| AGT-2026-03-05-08 | Codex | `codex_02` | Dashboard microstep 3: area agenda divisa in 2 riquadri con nuovo pannello live (clock realtime, countdown prossimo slot, stato occupato/in progress/libero) | `ae707a3` | `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"` | 2026-03-05 | Incrementata densita' informativa: spazio prima vuoto convertito in controllo operativo istantaneo |
| AGT-2026-03-05-07 | Codex | `codex_02` | Governance pre-UX: creazione skill `.codex/skills/fitmanager-dashboard-crm-design` + routing esplicito in `AGENTS.md` per microstep dashboard ad alta leggibilita' | `7adcd26` | check manuale frontmatter/openai metadata + tentativo `quick_validate.py` (blocco locale `pyyaml` mancante) | 2026-03-05 | Standardizzato playbook visuale CRM prima delle prossime iterazioni dashboard |
| AGT-2026-03-05-06 | Codex | `codex_02` | Dashboard microstep 2: nuova sezione "Lezioni della settimana" con breakdown per categoria/stato e link rapido agenda | `531f16d` | `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"` | 2026-03-05 | Da dashboard passiva a cockpit operativo: visione settimanale per carico PT/personale/colloqui/sala/corsi |
| AGT-2026-03-05-05 | Codex | `codex_02` | Dashboard efficacia operativa: KPI estesi da 2 a 4 (clienti, appuntamenti, sessioni imminenti, alert operativi) senza reintrodurre dati economici | `9accefa` | `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"` | 2026-03-05 | Primo microstep UX dashboard centrato sul lavoro reale del chinesiologo |
| AGT-2026-03-05-04 | Codex | `codex_02` | Skill pack progetto in `.codex/skills` (5 skill baseline con metadata agent) per attivazione automatica workflow specializzati | `614cc72` | no placeholder TODO nelle skill + verifica presenza 5 `agents/openai.yaml` | 2026-03-05 | Base pronta per loop continuo: nuove skill verticali incrementali su esigenze reali |
| AGT-2026-03-05-03 | Codex | `codex_02` | Governance agent-first: `AGENTS.md` root, override `frontend/api`, bootstrap `agents/`, config `.codex/config.toml` MCP-ready | `34f2db3` | manual review file consistency + docs sync (`UPGRADE_LOG`, spec, README upgrades) | 2026-03-05 | Base pronta per step successivo: override aggiuntivi per cartelle sensibili e setup MCP locale |
| AGT-2026-03-05-02 | Codex | `codex_01` | Dashboard privacy hardening: overview neutra per uso client-facing (no KPI/importi economici), rimozione blocchi finanziari, alert operativi filtrati | `b353ec8` | `npm --prefix frontend run lint -- "src/app/(dashboard)/page.tsx"` | 2026-03-05 | Mergeato anche su `main`; dashboard pronta per fase UX operativa |
| AGT-2026-03-05-01 | Claude Code | `codex_01` | Fix installer post-smoke-test: path PyInstaller, seed media/relazioni, backup restore WAL+schema+cookie | `e5cd7f4..275312c` (7 commit) | check-all.sh green, installer 83MB testato | 2026-03-05 | Installer funzionante: install → login → esercizi con foto → backup/restore OK |
| AGT-2026-03-04-06 | Codex + Claude Code | `codex_01` | UPG-2026-03-04-06 Wave 1-3: license pipeline + setup wizard + build distribution | `516f9d0..484376e` | check-all.sh green, smoke test install OK | 2026-03-04 | Wave 1 (S1.1-S1.6), Wave 2 (S2.1-S2.2), Wave 3 (S3.1-S3.4) |
| AGT-2026-03-04-04 | Codex + Claude Code | `codex_01` | Assistant CRM V0.5: parser deterministico + Command Palette UX | `e0e9415, 3653992` | check-all.sh green | 2026-03-04 | 6 moduli parser + CommandPalette 1170 LOC |
| AGT-2026-03-04-02 | Codex | `codex_01` | Export clinico schede: file scaricabile HTML->PDF con logo cliente + foto esercizi embedded, mantenendo anteprima separata | `d49b3d0` | eslint frontend file toccati | 2026-03-04 | ExportButtons + WorkoutPreview + export-workout-pdf + persistenza logo trainer |
| AGT-2026-03-04-03 | Codex | `codex_01` | Hardening stampa clinico: paginazione A4, colori print, riduzione densita foto/padding per meno pagine | `2cf8cd4, a502f71` | `npm --prefix frontend run lint -- "src/lib/export-workout-pdf.ts"` | 2026-03-04 | Fix page-break blocchi + compattazione proporzioni media |
| AGT-2026-03-04-01 | Claude Code | `codex_01` | Dual-DB architecture + Backup v2.0 bank-grade (5 pilastri) + restore fix WAL | `818e602` | check-all.sh green, test dev+prod PASS | 2026-03-04 | 14 file: database.py, config.py, backup.py, exercises.py, safety_engine.py, measurements.py, goals.py, main.py, types/api.ts, useBackup.ts, impostazioni/page.tsx |
| AGT-2026-03-03-08 | Claude Code | `codex_01` | Riallineamento Safety Engine — 80 pattern rules, 0 condizioni morte, severity avoid>modify>caution | `43e5010` | check-all.sh green, verify_qa_clinical 150 PASS 0 FAIL | 2026-03-03 | populate_conditions.py + safety_engine.py + RiskBodyMap.tsx + seed/verify QA |
| AGT-2026-03-03-11 | Claude Code | `codex_01` | Smart Programming Engine tuning 3 round: language mismatch, accessori 2-pass affinita', credito diluted, safety actionable, naming PPL | `97ab0a1, 82bf14f, 77e9961` | check-all.sh green | 2026-03-03 | smart-programming.ts + SmartAnalysisPanel.tsx |
| AGT-2026-03-03-06 | Codex | `codex_01` | Protezione Cassa + fix flusso spese fisse (reale vs previsto) | `54aa785, 9477fc0, 9735b29, 7739d8e` | check-all.sh green | 2026-03-03 | UPG-2026-03-03-06 + UPG-2026-03-03-07 |

## Quick rules

1. `Locked files` deve riflettere i file realmente in editing.
2. Se la task si blocca, usare stato `blocked` + nota chiara.
3. Alla chiusura, spostare la riga da `Active` a `Completed`.
