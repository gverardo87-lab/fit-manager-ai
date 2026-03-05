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
  /** Se presente, naviga a questa route prima di cercare il target */
  navigateTo?: string;
}

export interface TourDefinition {
  id: string;
  title: string;
  steps: TourStep[];
}

// ── Tour: Scopri FitManager — Ciclo Cliente Completo ──

export const TOUR_SCOPRI_FITMANAGER: TourDefinition = {
  id: "scopri-fitmanager",
  title: "Scopri FitManager",
  steps: [
    // 1. Dashboard
    {
      target: "dashboard-header",
      title: "La tua Dashboard",
      description:
        "La panoramica operativa della giornata: KPI, appuntamenti in scadenza, alert e azioni rapide. Aprila ogni mattina per partire allineato.",
      placement: "bottom",
    },
    // 2. Clienti — navigazione automatica
    {
      target: "clienti-header",
      navigateTo: "/clienti",
      title: "I tuoi Clienti",
      description:
        "Qui gestisci ogni cliente: anagrafica, stato e storico. Ogni card mostra a colpo d'occhio crediti residui, contratti attivi e ultima sessione.",
      placement: "bottom",
    },
    // 3. Nuovo cliente
    {
      target: "clienti-new-button",
      title: "Registra un Cliente",
      description:
        "Clicca qui per creare un profilo completo. Dopo il salvataggio potrai compilare anamnesi strutturata, inserire misurazioni periodiche e definire obiettivi personalizzati.",
      placement: "bottom",
    },
    // 4. Profilo clinico (spiegazione da KPI)
    {
      target: "clienti-kpi",
      title: "Profilo Clinico Completo",
      description:
        "Ogni cliente ha un profilo clinico: anamnesi strutturata (muscoloscheletrica, condizioni mediche, stile di vita), misurazioni con analisi scientifica (range OMS/ACSM, velocita' di cambiamento, composizione corporea) e obiettivi con proiezione temporale. L'anamnesi alimenta lo Scudo Clinico che protegge il cliente durante la programmazione.",
      placement: "bottom",
    },
    // 5. Esercizi — navigazione automatica
    {
      target: "esercizi-header",
      navigateTo: "/esercizi",
      title: "269 Esercizi Scientifici",
      description:
        "Catalogo professionale con classificazione a 14 dimensioni: pattern movimento, gruppi muscolari, catena cinetica, piano di movimento e tipo contrazione. Ogni esercizio ha foto, relazioni (progressioni e regressioni) e mapping a 47 condizioni mediche.",
      placement: "bottom",
    },
    // 6. Filtri esercizi
    {
      target: "esercizi-filters",
      title: "Filtri Biomeccanici",
      description:
        "Filtra per pattern (squat, hinge, push, pull, core, rotation, carry), gruppo muscolare, attrezzatura, difficolta' e biomeccanica avanzata (catena cinetica, lateralita'). I conteggi dinamici mostrano quanti esercizi matchano ogni filtro.",
      placement: "bottom",
    },
    // 7. Schede — navigazione automatica
    {
      target: "schede-header",
      navigateTo: "/schede",
      title: "Schede Allenamento",
      description:
        "Il builder professionale: sessioni strutturate con drag & drop, blocchi (circuito, superset, AMRAP, EMOM, tabata, for time), preview live ed export clinico PDF con foto esercizi e logo personalizzato.",
      placement: "bottom",
    },
    // 8. Smart + Safety
    {
      target: "schede-new-button",
      title: "Programmazione Intelligente",
      description:
        "Crea da zero, da template o con Smart Programming. Lo Scudo Clinico incrocia l'anamnesi del cliente con 47 condizioni mediche su ogni esercizio: indicatori visivi rosso, ambra e blu — mai blocchi. Il motore a 14 dimensioni suggerisce gli esercizi ottimali per obiettivo, livello e profilo clinico.",
      placement: "bottom",
    },
    // 9. Monitoraggio — navigazione automatica
    {
      target: "monitoraggio-header",
      navigateTo: "/allenamenti",
      title: "Monitoraggio Compliance",
      description:
        "Attiva un programma e traccia l'aderenza su griglia settimane per sessioni. Il cliente registra ogni allenamento, tu vedi la compliance in tempo reale con barra colorata: verde sopra l'80%, ambra sopra il 50%, rossa sotto.",
      placement: "bottom",
    },
    // 10. Ricerca rapida
    {
      target: "sidebar-search",
      title: "Cerca ovunque (Ctrl+K)",
      description:
        "Premi Ctrl+K da qualsiasi pagina per cercare clienti, esercizi e navigare ovunque. Digita > per lanciare l'assistente in linguaggio naturale: crea appuntamenti, movimenti e misurazioni con una frase in italiano.",
      placement: "right",
      desktopOnly: true,
    },
    // 11. Guida — navigazione automatica
    {
      target: "guida-hero",
      navigateTo: "/guida",
      title: "Sempre qui per te",
      description:
        "Torna in questa pagina quando vuoi per rilanciare il tour, consultare le FAQ o scoprire le feature avanzate. Buon lavoro!",
      placement: "bottom",
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
