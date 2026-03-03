# DoR / DoD Checklist

Checklist operativa per mantenere standard senior senza rallentare il flusso.

## Definition of Ready (DoR)

- [ ] Problema e obiettivo sono espliciti.
- [ ] Scope e fuori scope sono chiari.
- [ ] Invarianti critici identificati (security, data integrity, UX, type sync).
- [ ] File/layer impattati mappati.
- [ ] Rischi principali identificati.
- [ ] Test plan minimo definito.
- [ ] Entry iniziale in `docs/upgrades/UPGRADE_LOG.md` creata.

## Definition of Done (DoD)

- [ ] Implementazione completata secondo spec.
- [ ] Nessuna regressione evidente sui flussi collegati.
- [ ] Build/lint/test previsti eseguiti e verdi.
- [ ] Type sync e invalidazioni query verificate.
- [ ] Log upgrade aggiornato con commit finale e stato.
- [ ] ADR creato se la decisione ha impatto architetturale.
- [ ] Rollback path valido e documentato.
