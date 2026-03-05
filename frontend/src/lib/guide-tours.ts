// ════════════════════════════════════════════════════════════
// GUIDE TOURS — Definizioni tour, FAQ e scorciatoie
// File puro dati. Zero React, zero side-effect.
// ════════════════════════════════════════════════════════════

// ── Types ──

export interface TourStep {
  /** Matcha data-guide="..." sull'elemento target */
  target: string;
  title: string;
  description: string;
  placement: "top" | "bottom" | "left" | "right";
  /** Se true, lo step viene mostrato solo su desktop (>= 1024px) */
  desktopOnly?: boolean;
}

export interface TourDefinition {
  id: string;
  title: string;
  steps: TourStep[];
}

// ── Tour: Scopri FitManager ──

export const TOUR_SCOPRI_FITMANAGER: TourDefinition = {
  id: "scopri-fitmanager",
  title: "Scopri FitManager",
  steps: [
    {
      target: "dashboard-header",
      title: "La tua Dashboard",
      description:
        "Qui trovi la panoramica operativa della giornata: KPI, appuntamenti, alert e azioni rapide. Aprila ogni mattina per partire allineato.",
      placement: "bottom",
    },
    {
      target: "sidebar-nav",
      title: "Navigazione",
      description:
        "La sidebar ti porta in ogni area del CRM: clienti, contratti, cassa, esercizi e schede allenamento. Ogni sezione e' indipendente e raggiungibile in un click.",
      placement: "right",
      desktopOnly: true,
    },
    {
      target: "sidebar-search",
      title: "Ricerca rapida (Ctrl+K)",
      description:
        "Premi Ctrl+K da qualsiasi pagina per cercare clienti, esercizi, navigare ovunque. Digita > per lanciare l'assistente in linguaggio naturale.",
      placement: "right",
      desktopOnly: true,
    },
    {
      target: "sidebar-clienti",
      title: "I tuoi Clienti",
      description:
        "Gestisci anagrafica, anamnesi, misurazioni e obiettivi. Ogni cliente ha un profilo completo con analisi cliniche e storico progressi.",
      placement: "right",
      desktopOnly: true,
    },
    {
      target: "sidebar-schede",
      title: "Schede Allenamento",
      description:
        "Il builder professionale con 269 esercizi, blocchi strutturati, analisi smart a 14 dimensioni e export clinico PDF con foto.",
      placement: "right",
      desktopOnly: true,
    },
    {
      target: "sidebar-guida",
      title: "Guida e Supporto",
      description:
        "Questa pagina! Qui trovi scorciatoie, FAQ e puoi rilanciare questo tour quando vuoi. Buon lavoro!",
      placement: "right",
      desktopOnly: true,
    },
  ],
};

// ── FAQ ──

export interface GuideFaq {
  question: string;
  answer: string;
}

export const GUIDE_FAQ: GuideFaq[] = [
  {
    question: "Come creo il primo cliente?",
    answer:
      "Dalla sidebar clicca Clienti, poi \"Nuovo Cliente\" in alto a destra. Compila nome, cognome e almeno un contatto (email o telefono). Dopo il salvataggio potrai accedere al profilo completo con anamnesi e misurazioni.",
  },
  {
    question: "Come registro un pagamento?",
    answer:
      "Vai in Contratti, apri il dettaglio del contratto, scorri alle rate. Clicca \"Paga\" sulla rata desiderata. Puoi pagare l'intero importo o un importo parziale. Il saldo in Cassa si aggiorna automaticamente.",
  },
  {
    question: "Come uso l'assistente (>)?",
    answer:
      "Premi Ctrl+K per aprire la Command Palette, poi digita > seguito dal tuo comando in italiano. Ad esempio: \"> Marco Rossi domani alle 18 PT\" crea un appuntamento. Controlla sempre la preview prima di confermare con Invio.",
  },
  {
    question: "Come esporto una scheda allenamento?",
    answer:
      "Apri la scheda nel builder, clicca \"Esporta\" in alto a destra. Scegli tra anteprima rapida (stampa dal browser) e scarica clinico (file HTML ottimizzato per PDF con foto esercizi e logo personalizzato).",
  },
  {
    question: "Come faccio un backup dei dati?",
    answer:
      "Vai in Impostazioni, sezione Backup. Clicca \"Crea Backup\" per una copia atomica del database con checksum SHA-256. Verifica l'integrita' prima di archiviare. Per ripristinare, usa \"Ripristina\" e carica il file.",
  },
  {
    question: "Cosa significano i colori nella scheda allenamento?",
    answer:
      "Rosso (Evitare): esercizio controindicato per l'anamnesi del cliente. Ambra (Cautela): richiede attenzione generica. Blu (Adattare): modificare ROM, grip o carico. Il sistema non blocca nulla — la decisione e' sempre del professionista.",
  },
  {
    question: "Perche' i dati economici non sono nella dashboard?",
    answer:
      "Per privacy. La dashboard mostra KPI operativi (clienti attivi, appuntamenti, completamento). I dati finanziari (saldo, entrate, uscite, forecast) sono nella sezione Cassa, accessibile solo quando serve.",
  },
];

// ── Scorciatoie da tastiera ──

export interface KeyboardShortcut {
  keys: string[];
  label: string;
}

export const KEYBOARD_SHORTCUTS: KeyboardShortcut[] = [
  { keys: ["Ctrl", "K"], label: "Ricerca rapida e navigazione" },
  { keys: [">"], label: "Attiva assistente nella palette" },
  { keys: ["Esc"], label: "Chiudi finestre e palette" },
  { keys: ["←", "→"], label: "Naviga tra i passi del tour" },
  { keys: ["Invio"], label: "Conferma azione o passo successivo" },
];

// ── Feature Discovery ──

export interface FeatureCard {
  id: string;
  title: string;
  description: string;
  href: string;
  iconName: "bot" | "brain" | "shield" | "file-down";
}

export const FEATURE_CARDS: FeatureCard[] = [
  {
    id: "assistant",
    title: "Assistente CRM",
    description:
      "Crea appuntamenti, movimenti e misurazioni in linguaggio naturale dalla Command Palette.",
    href: "/",
    iconName: "bot",
  },
  {
    id: "smart-programming",
    title: "Smart Programming",
    description:
      "Genera schede allenamento personalizzate incrociando 14 dimensioni cliniche e biomeccaniche.",
    href: "/schede",
    iconName: "brain",
  },
  {
    id: "safety-engine",
    title: "Scudo Clinico",
    description:
      "47 condizioni mediche mappate su ogni esercizio. Indicatori visivi, mai blocchi.",
    href: "/esercizi",
    iconName: "shield",
  },
  {
    id: "export-clinico",
    title: "Export Clinico",
    description:
      "Schede PDF professionali con foto esercizi, copertina e logo personalizzato.",
    href: "/schede",
    iconName: "file-down",
  },
];
