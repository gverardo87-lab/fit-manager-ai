# UPG-2026-03-11-14 - CRM UX Skill Pack Launch Refactor

## Contesto

La skill iniziale `fitmanager-dashboard-crm-design` era nata per fermare il drift dei primi
microstep dashboard. Ha funzionato nella fase iniziale, ma il prodotto e' cambiato:

- `Dashboard` e `Oggi` non hanno piu la stessa natura;
- `Rinnovi & Incassi` ha gia dimostrato di richiedere una grammatica propria;
- il profilo cliente sta diventando un vero hub CRM, non una mini-dashboard.

Con la crescita del CRM, una sola skill visuale centrata su card grid, KPI e board simmetriche
rischia di alzare l'ordine ma abbassare il livello, perche' spinge ogni pagina verso lo stesso
schema.

## Obiettivo

Rifondare il pacchetto skill UX del launch in modo che:

- la dashboard resti forte come overview;
- i workspace operativi abbiano una skill dedicata action-first;
- le record page CRM abbiano una skill dedicata entity-first;
- la skill responsive adatti le pagine senza appiattirne l'identita';
- `AGENTS.md` instradi gli agenti verso la skill giusta senza congelare il design in pattern
  limitanti.

## Ambito

### Skill da restringere o aggiornare

- `.codex/skills/fitmanager-dashboard-crm-design/`
- `.codex/skills/fitmanager-responsive-adaptive-ui/`

### Nuove skill da introdurre

- `.codex/skills/fitmanager-operational-workspace-design/`
- `.codex/skills/fitmanager-crm-record-page-design/`

### Governance e sync

- `AGENTS.md`
- `docs/upgrades/UPGRADE_LOG.md`
- `docs/upgrades/README.md`
- `docs/ai-sync/WORKBOARD.md`

## Non-obiettivi

- nessun cambio runtime frontend o backend;
- nessun redesign di pagine CRM in questo microstep;
- nessuna nuova policy di query/cache o type sync, perche' il lavoro resta docs-first;
- nessun validator Python delle skill forzato con workaround opachi.

## Decisioni chiave

- `fitmanager-dashboard-crm-design` viene ristretto alle vere surface overview/post-login;
- le board operative non devono piu ereditare automaticamente grammatica dashboard;
- le record page CRM devono essere trattate come hub/entity pages, non come mosaici KPI;
- la responsive skill deve preservare l'archetipo della pagina (`overview`, `workspace`,
  `record page`, `finance dossier`) invece di trasformare tutto nello stesso stack.

## Verifica attesa

- review manuale delle skill e dei manifest `agents/openai.yaml`;
- controllo cross-doc su `AGENTS.md`, `UPGRADE_LOG.md`, `README.md` e `WORKBOARD.md`;
- grep mirato sulle nuove skill e sui nuovi nomi skill;
- `git diff --check`.

## Limite ambientale noto

Il bootstrap/validator Python delle skill non e' affidabile in questo ambiente Windows:
la `venv` locale resolve verso il launcher Microsoft Store e non garantisce l'esecuzione
corretta degli script `skill-creator`. Il microstep quindi crea e aggiorna i file skill
manualmente, documentando esplicitamente il limite invece di fingere una validazione completa.

## Rischio Residuo

Dopo questo refactor resta un rischio sano ma reale: avere piu skill aumenta la liberta'
compositiva e quindi anche il rischio di scegliere la skill sbagliata. La mitigazione e'
doppia:

- routing piu esplicito in `AGENTS.md`;
- definizione chiara del tipo di surface dentro ogni skill.
