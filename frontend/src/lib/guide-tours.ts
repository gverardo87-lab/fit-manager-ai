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

// ── Tour: Scopri FitManager — Ciclo Operativo Completo (19 passi) ──

export const TOUR_SCOPRI_FITMANAGER: TourDefinition = {
  id: "scopri-fitmanager",
  title: "Scopri FitManager",
  steps: [
    // ── SEZIONE 1: Dashboard ──
    {
      target: "dashboard-header",
      navigateTo: "/",
      title: "La tua Dashboard",
      description:
        "La panoramica operativa della giornata: clienti attivi, appuntamenti in scadenza, completamento sessioni e alert rate scadute. Aprila ogni mattina per partire allineato.",
      placement: "bottom",
    },

    // ── SEZIONE 2: Clienti ──
    {
      target: "clienti-header",
      navigateTo: "/clienti",
      title: "I tuoi Clienti",
      description:
        "Qui gestisci ogni cliente: anagrafica, stato e storico. Ogni riga mostra a colpo d'occhio crediti residui, contratti attivi e ultima sessione. Filtra per stato (attivo, in pausa, archiviato) o cerca per nome.",
      placement: "bottom",
    },
    {
      target: "clienti-new-button",
      title: "Registra un Cliente",
      description:
        "Clicca qui per creare un profilo completo. Dopo il salvataggio accedi al profilo con: anamnesi strutturata (muscoloscheletrica, condizioni mediche, stile di vita), misurazioni periodiche con analisi clinica (range OMS/ACSM, velocita' di cambiamento, composizione corporea) e obiettivi con proiezione temporale.",
      placement: "bottom",
    },
    {
      target: "clienti-kpi",
      title: "KPI e Scudo Clinico",
      description:
        "I KPI mostrano clienti attivi, in pausa, crediti e rate scadute. Dal profilo cliente l'anamnesi alimenta lo Scudo Clinico: 47 condizioni mediche mappate su ogni esercizio con indicatori visivi (rosso = evitare, ambra = cautela, blu = adattare). Mai blocchi — la decisione e' sempre tua.",
      placement: "bottom",
    },

    // ── SEZIONE 3: Contratti ──
    {
      target: "contratti-header",
      navigateTo: "/contratti",
      title: "I tuoi Contratti",
      description:
        "Gestisci contratti, pacchetti e abbonamenti. Ogni contratto ha tipo (PT, sala, corso), prezzo, durata, crediti sessione e piano rateale. Lo stato finanziario si aggiorna automaticamente: attivi, in scadenza, saldati.",
      placement: "bottom",
    },
    {
      target: "contratti-new-button",
      title: "Crea un Contratto",
      description:
        "Crea un contratto con piano rate automatico o personalizzato. Puoi generare rate mensili con un click, o aggiungerle manualmente. Ogni pagamento registrato aggiorna saldo Cassa, stato contratto e crediti cliente in tempo reale.",
      placement: "bottom",
    },
    {
      target: "contratti-kpi",
      title: "Panoramica Finanziaria",
      description:
        "Quattro KPI finanziari: contratti attivi, fatturato totale, incassato e rate scadute. Il dettaglio di ogni contratto mostra piano rate con storico pagamenti, parziali e scadenze. Contratti saldati con crediti esauriti si chiudono automaticamente.",
      placement: "bottom",
    },

    // ── SEZIONE 4: Agenda ──
    {
      target: "agenda-header",
      navigateTo: "/agenda",
      title: "La tua Agenda",
      description:
        "Calendario interattivo con vista giorno, settimana e mese. Slot da 30 minuti, color coding per categoria (PT, sala, corso, amministrazione). Trascina per spostare, ridimensiona per cambiare durata. KPI contestuali: completamento, programmati, cancellati.",
      placement: "bottom",
    },
    {
      target: "agenda-new-button",
      title: "Pianifica Appuntamenti",
      description:
        "Crea appuntamenti con cliente, contratto, data e ora. Puoi anche cliccare uno slot vuoto nel calendario per pre-compilare la data. Ogni sessione completata scala un credito dal contratto collegato. Usa Ctrl+K e digita > per creare eventi in linguaggio naturale.",
      placement: "bottom",
    },

    // ── SEZIONE 5: Cassa ──
    {
      target: "cassa-header",
      navigateTo: "/cassa",
      title: "La tua Cassa",
      description:
        "Il centro di controllo finanziario: saldo attuale, entrate, uscite variabili, uscite fisse e margine netto. Grafico giornaliero con barre entrate/uscite e linea saldo. Filtro per mese e anno. Dati separati dalla dashboard per privacy.",
      placement: "bottom",
    },
    {
      target: "cassa-new-button",
      title: "Registra Movimenti",
      description:
        "Registra entrate e uscite manuali. I pagamenti delle rate generano movimenti automatici. Le spese fisse ricorrenti (affitto, assicurazione, utenze) si confermano mensilmente. Il libro mastro mostra ogni operazione con saldo progressivo.",
      placement: "bottom",
    },

    // ── SEZIONE 6: Esercizi ──
    {
      target: "esercizi-header",
      navigateTo: "/esercizi",
      title: "269 Esercizi Scientifici",
      description:
        "Catalogo professionale con classificazione a 14 dimensioni: pattern movimento (squat, hinge, push, pull, core, rotation, carry), gruppi muscolari, catena cinetica, piano di movimento e tipo contrazione. Ogni esercizio ha foto, progressioni, regressioni e mapping a 47 condizioni mediche.",
      placement: "bottom",
    },
    {
      target: "esercizi-filters",
      title: "Filtri Biomeccanici",
      description:
        "Filtra per categoria, pattern di movimento, gruppo muscolare, attrezzatura, difficolta' e biomeccanica avanzata. I conteggi dinamici mostrano quanti esercizi matchano ogni filtro. Clicca un esercizio per vedere muscoli, classificazione completa, setup e note di sicurezza.",
      placement: "bottom",
    },

    // ── SEZIONE 7: Schede Allenamento ──
    {
      target: "schede-header",
      navigateTo: "/schede",
      title: "Schede Allenamento",
      description:
        "Qui crei e gestisci le schede allenamento. Ogni scheda ha sessioni strutturate con avviamento, parte principale e stretching. Builder professionale con drag & drop, blocchi (circuito, superset, AMRAP, EMOM, tabata, for time), preview live ed export clinico PDF con foto esercizi e logo personalizzato.",
      placement: "bottom",
    },
    {
      target: "schede-new-button",
      title: "Programmazione Intelligente",
      description:
        "Crea da zero, da template o con Smart Programming. Il motore a 14 dimensioni suggerisce gli esercizi ottimali incrociando obiettivo, livello, profilo clinico e copertura muscolare. Lo Scudo Clinico evidenzia compatibilita' con l'anamnesi cliente: rosso, ambra e blu — mai blocchi, sempre la tua decisione.",
      placement: "bottom",
    },

    // ── SEZIONE 8: Monitoraggio ──
    {
      target: "monitoraggio-header",
      navigateTo: "/allenamenti",
      title: "Monitoraggio Compliance",
      description:
        "Attiva un programma impostando date inizio e fine, poi traccia l'aderenza su griglia settimane per sessioni. Registra ogni allenamento e visualizza la compliance in tempo reale: verde sopra l'80%, ambra sopra il 50%, rossa sotto.",
      placement: "bottom",
    },

    // ── SEZIONE 9: Impostazioni ──
    {
      target: "impostazioni-header",
      navigateTo: "/impostazioni",
      title: "Backup e Protezione Dati",
      description:
        "Crea backup atomici del database con checksum SHA-256. Ripristina da backup precedenti con verifica integrita'. Configura il saldo iniziale di cassa. Esporta tutti i dati in JSON (portabilita' GDPR). I tuoi dati restano sempre sul tuo computer.",
      placement: "bottom",
    },

    // ── SEZIONE 10: Ricerca rapida ──
    {
      target: "sidebar-search",
      title: "Cerca ovunque (Ctrl+K)",
      description:
        "Premi Ctrl+K da qualsiasi pagina per cercare clienti, esercizi e navigare ovunque. Digita > per lanciare l'assistente in linguaggio naturale: crea appuntamenti, movimenti e misurazioni con una frase in italiano.",
      placement: "right",
      desktopOnly: true,
    },

    // ── CHIUSURA ──
    {
      target: "guida-hero",
      navigateTo: "/guida",
      title: "Sempre qui per te",
      description:
        "Torna in questa pagina quando vuoi per rilanciare il tour, consultare le FAQ o scoprire le scorciatoie. Buon lavoro!",
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
