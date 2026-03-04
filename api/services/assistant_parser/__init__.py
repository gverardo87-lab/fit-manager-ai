"""
Assistant Parser — NLP deterministico per comandi CRM in italiano.

Pipeline: normalize -> classify -> extract -> resolve -> score -> assemble.
Commit: dispatch a funzioni di dominio esistenti (zero duplicazione logica).

Moduli:
  normalizer        — normalizzazione testo italiano
  intent_classifier — classificazione intent via regex
  entity_extractor  — estrazione entita' (date, importi, nomi, metriche)
  entity_resolver   — risoluzione entita' vs DB (fuzzy client match)
  confidence        — scoring confidenza + rilevamento ambiguita'
  orchestrator      — pipeline principale
  commit_dispatcher — dispatch a funzioni di dominio esistenti
"""

from api.services.assistant_parser.orchestrator import orchestrate

__all__ = ["orchestrate"]
