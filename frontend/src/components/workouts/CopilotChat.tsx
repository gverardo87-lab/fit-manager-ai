// src/components/workouts/CopilotChat.tsx
"use client";

/**
 * Chat conversazionale con il copilot AI nel workout builder.
 *
 * Pannello collapsabile nella colonna destra (desktop).
 * Gestisce: messaggi, loading, azioni inline, context notes.
 * Serializza lo stato corrente del builder ad ogni chiamata.
 *
 * Timeout 35s per Ollama (gemma2:9b locale, ~10-20s tipici).
 * Graceful degradation: errori mostrati come messaggio nel chat.
 */

import { useState, useCallback, useRef, useEffect } from "react";
import {
  Sparkles,
  ChevronDown,
  ChevronUp,
  Send,
  Loader2,
  Plus,
  ArrowRightLeft,
  Settings2,
  Check,
  BarChart3,
  Search,
  MessageCircle,
  Lightbulb,
  RotateCcw,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import apiClient from "@/lib/api-client";
import type {
  ChatWorkoutState,
  ChatWorkoutSession,
  ChatWorkoutExercise,
  ChatMessage,
  CopilotChatResponse,
  CopilotAction,
  CopilotActionAddExercise,
} from "@/types/api";
import type { SessionCardData } from "./SessionCard";
import { getSectionForCategory } from "@/lib/workout-templates";

// ── Types interni ──

interface ChatBubble {
  id: string;
  role: "user" | "assistant";
  content: string;
  actions?: CopilotAction[];
  appliedActions?: Set<number>; // exercise_id delle azioni gia' applicate
}

interface CopilotChatProps {
  planId: number;
  clientNome?: string;
  /** Sessioni correnti del builder (state locale) */
  sessions: SessionCardData[];
  /** Mappa id → Exercise per arricchire la serializzazione */
  exerciseMap: Map<number, { pattern_movimento: string }>;
  /** Callback: aggiunge esercizio dal copilot */
  onAddExercise: (
    sessionIndex: number,
    exercise: CopilotActionAddExercise,
  ) => void;
}

// ── Helper: serializza state per il backend ──

function serializeWorkoutState(
  sessions: SessionCardData[],
  exerciseMap: Map<number, { pattern_movimento: string }>,
): ChatWorkoutState {
  return {
    sessions: sessions.map((s): ChatWorkoutSession => ({
      nome: s.nome_sessione,
      focus: s.focus_muscolare,
      exercises: s.esercizi.map((e): ChatWorkoutExercise => {
        const section = getSectionForCategory(e.esercizio_categoria);
        const exData = exerciseMap.get(e.id_esercizio);
        return {
          id: e.id_esercizio,
          nome: e.esercizio_nome,
          pattern: exData?.pattern_movimento ?? "unknown",
          sezione: section,
          serie: e.serie,
          ripetizioni: e.ripetizioni,
          riposo: e.tempo_riposo_sec,
        };
      }),
    })),
  };
}

// ── Helper: extract error message ──

function extractChatError(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const response = (err as { response?: { status?: number; data?: { detail?: string } } }).response;
    if (response?.status === 503) {
      return "AI non disponibile. Verifica che Ollama sia attivo.";
    }
    if (response?.data?.detail) {
      return response.data.detail;
    }
  }
  if (err && typeof err === "object" && "code" in err) {
    const code = (err as { code?: string }).code;
    if (code === "ECONNABORTED") {
      return "Il copilota sta impiegando troppo tempo. Riprova tra poco.";
    }
  }
  return "Errore nella comunicazione con il copilota.";
}

// ── Componente ──

const MAX_HISTORY = 10;

// ── Quick prompts contestuali ──

interface QuickPrompt {
  label: string;
  message: string;
  icon: React.ReactNode;
  /** Se presente, il chip viene mostrato solo se la condizione e' vera */
  condition?: (ctx: { hasExercises: boolean; clientNome?: string }) => boolean;
}

const QUICK_PROMPTS: QuickPrompt[] = [
  {
    label: "Suggerisci un esercizio",
    message: "Suggeriscimi un esercizio adatto per questa sessione",
    icon: <Sparkles className="h-3 w-3" />,
  },
  {
    label: "Analizza la scheda",
    message: "Analizza la struttura della scheda e dimmi se e' bilanciata",
    icon: <BarChart3 className="h-3 w-3" />,
    condition: ({ hasExercises }) => hasExercises,
  },
  {
    label: "Che struttura consigli?",
    message: "Che struttura consigli per questa scheda? Quanti esercizi per sessione?",
    icon: <Lightbulb className="h-3 w-3" />,
    condition: ({ hasExercises }) => !hasExercises,
  },
  {
    label: "Cerca per muscolo",
    message: "Cerca un esercizio per i glutei",
    icon: <Search className="h-3 w-3" />,
  },
  {
    label: "Preferenze cliente",
    message: "Il cliente preferisce le macchine",
    icon: <MessageCircle className="h-3 w-3" />,
    condition: ({ clientNome }) => !!clientNome,
  },
];

const FOLLOW_UP_PROMPTS: QuickPrompt[] = [
  {
    label: "Suggerisci un altro",
    message: "Suggeriscimi un altro esercizio",
    icon: <Plus className="h-3 w-3" />,
  },
  {
    label: "Analizza la scheda",
    message: "Analizza la struttura della scheda",
    icon: <BarChart3 className="h-3 w-3" />,
  },
  {
    label: "Dimmi di piu'",
    message: "Puoi approfondire?",
    icon: <RotateCcw className="h-3 w-3" />,
  },
];

export function CopilotChat({
  planId,
  clientNome,
  sessions,
  exerciseMap,
  onAddExercise,
}: CopilotChatProps) {
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState<ChatBubble[]>([]);
  const [contextNotes, setContextNotes] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [hasOpened, setHasOpened] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll ai nuovi messaggi
  useEffect(() => {
    if (expanded && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, expanded]);

  // Focus input quando si espande
  useEffect(() => {
    if (expanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [expanded]);

  // Messaggio di benvenuto alla prima apertura
  const handleToggle = useCallback(() => {
    setExpanded((prev) => {
      const next = !prev;
      if (next && !hasOpened) {
        setHasOpened(true);
        const welcome = clientNome
          ? `Ciao! Sto guardando la scheda${clientNome ? ` di ${clientNome}` : ""}. Come posso aiutarti?`
          : "Ciao! Come posso aiutarti con questa scheda?";
        setMessages([{
          id: "welcome",
          role: "assistant",
          content: welcome,
        }]);
      }
      return next;
    });
  }, [hasOpened, clientNome]);

  // Contesto per i chip contestuali
  const hasExercises = sessions.some((s) => s.esercizi.length > 0);
  const showWelcomeChips = messages.length <= 1 && !isLoading;
  const lastMessage = messages[messages.length - 1];
  const showFollowUp = !isLoading
    && messages.length > 1
    && lastMessage?.role === "assistant"
    && lastMessage?.id !== "welcome";

  // Invia messaggio (overrideText per quick prompts)
  const handleSend = useCallback(async (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || isLoading) return;

    setInput("");

    // Aggiungi messaggio utente
    const userBubble: ChatBubble = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userBubble]);
    setIsLoading(true);

    try {
      // Costruisci conversation history (escludi welcome e messaggi di errore)
      const history: ChatMessage[] = messages
        .filter((m) => m.id !== "welcome")
        .map((m) => ({ role: m.role, content: m.content }))
        .slice(-MAX_HISTORY);

      const res = await apiClient.post<CopilotChatResponse>(
        "/copilot/chat",
        {
          plan_id: planId,
          message: text,
          workout_state: serializeWorkoutState(sessions, exerciseMap),
          conversation_history: history,
          context_notes: contextNotes,
        },
        { timeout: 35_000 },
      );

      const data = res.data;

      // Aggiorna context notes
      if (data.context_notes_update.length > 0) {
        setContextNotes((prev) => {
          const merged = [...prev];
          for (const note of data.context_notes_update) {
            if (!merged.includes(note)) {
              merged.push(note);
            }
          }
          return merged.slice(-20);
        });
      }

      // Aggiungi risposta copilot
      const assistantBubble: ChatBubble = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.message,
        actions: data.actions.length > 0 ? data.actions : undefined,
        appliedActions: new Set(),
      };
      setMessages((prev) => [...prev, assistantBubble]);

    } catch (err: unknown) {
      const errorMsg = extractChatError(err);
      setMessages((prev) => [...prev, {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: errorMsg,
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, planId, sessions, exerciseMap, messages, contextNotes]);

  // Applica azione
  const handleApplyAction = useCallback(
    (bubbleId: string, action: CopilotAction) => {
      if (action.type === "add_exercise") {
        // Trova la sessione giusta (prima sessione, o la prima con esercizi della stessa sezione)
        let targetIdx = 0;
        for (let i = 0; i < sessions.length; i++) {
          const hasSection = sessions[i].esercizi.some(
            (e) => getSectionForCategory(e.esercizio_categoria) === action.sezione,
          );
          if (hasSection || sessions[i].esercizi.length === 0) {
            targetIdx = i;
            break;
          }
        }
        onAddExercise(targetIdx, action);
      }
      // TODO: swap_exercise, modify_params (skeleton backend)

      // Segna azione come applicata
      setMessages((prev) =>
        prev.map((m) => {
          if (m.id !== bubbleId) return m;
          const applied = new Set(m.appliedActions);
          if (action.type === "add_exercise") {
            applied.add(action.exercise_id);
          }
          return { ...m, appliedActions: applied };
        }),
      );
    },
    [sessions, onAddExercise],
  );

  // ── Render ──

  return (
    <div className="rounded-lg border bg-card" data-print-hide>
      {/* Header — toggle */}
      <button
        onClick={handleToggle}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left hover:bg-muted/50 transition-colors rounded-lg"
      >
        <Sparkles className="h-4 w-4 text-primary" />
        <span className="flex-1 text-sm font-semibold">Copilot AI</span>
        {contextNotes.length > 0 && (
          <span className="text-[10px] text-muted-foreground">
            {contextNotes.length} note
          </span>
        )}
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {/* Body — chat */}
      {expanded && (
        <div className="border-t">
          {/* Messages area */}
          <div className="h-[360px] overflow-y-auto px-3 py-2 space-y-3">
            {messages.map((bubble) => (
              <div
                key={bubble.id}
                className={`flex ${bubble.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
                    bubble.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{bubble.content}</p>

                  {/* Azioni inline */}
                  {bubble.actions && bubble.actions.length > 0 && (
                    <div className="mt-2 space-y-1.5 border-t border-foreground/10 pt-2">
                      {bubble.actions.map((action, idx) => {
                        const isApplied = action.type === "add_exercise"
                          && bubble.appliedActions?.has(action.exercise_id);

                        return (
                          <ActionButton
                            key={idx}
                            action={action}
                            applied={!!isApplied}
                            onApply={() => handleApplyAction(bubble.id, action)}
                          />
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Welcome chips — guida l'utente alla prima interazione */}
            {showWelcomeChips && (
              <div className="flex flex-wrap gap-1.5 px-1">
                {QUICK_PROMPTS
                  .filter((p) => !p.condition || p.condition({ hasExercises, clientNome }))
                  .map((p) => (
                    <button
                      key={p.label}
                      onClick={() => handleSend(p.message)}
                      className="flex items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-2.5 py-1 text-[11px] font-medium text-primary hover:bg-primary/10 transition-colors"
                    >
                      {p.icon}
                      {p.label}
                    </button>
                  ))}
              </div>
            )}

            {/* Follow-up chips — dopo ogni risposta, evita il muro bianco */}
            {showFollowUp && (
              <div className="flex flex-wrap gap-1.5 px-1">
                {FOLLOW_UP_PROMPTS.map((p) => (
                  <button
                    key={p.label}
                    onClick={() => handleSend(p.message)}
                    className="flex items-center gap-1 rounded-full border border-muted-foreground/20 px-2 py-0.5 text-[10px] text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                  >
                    {p.icon}
                    {p.label}
                  </button>
                ))}
              </div>
            )}

            {/* Typing indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2">
                  <Loader2 className="h-3 w-3 animate-spin text-primary" />
                  <span className="text-xs text-muted-foreground">
                    Sto pensando...
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t px-3 py-2">
            <form
              onSubmit={(e) => { e.preventDefault(); handleSend(); }}
              className="flex items-center gap-2"
            >
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Chiedi al copilota..."
                disabled={isLoading}
                className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground/60 disabled:opacity-50"
              />
              <Button
                type="submit"
                variant="ghost"
                size="icon"
                className="h-7 w-7 shrink-0"
                disabled={isLoading || !input.trim()}
              >
                <Send className="h-3.5 w-3.5" />
              </Button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sub-componente: bottone azione ──

function ActionButton({
  action,
  applied,
  onApply,
}: {
  action: CopilotAction;
  applied: boolean;
  onApply: () => void;
}) {
  const icon = action.type === "add_exercise"
    ? <Plus className="h-3 w-3" />
    : action.type === "swap_exercise"
      ? <ArrowRightLeft className="h-3 w-3" />
      : <Settings2 className="h-3 w-3" />;

  return (
    <button
      onClick={applied ? undefined : onApply}
      disabled={applied}
      className={`flex w-full items-start gap-1.5 rounded-md px-2 py-1.5 text-left transition-colors ${
        applied
          ? "bg-foreground/5 opacity-60 cursor-default"
          : "bg-foreground/10 hover:bg-foreground/20 cursor-pointer"
      }`}
    >
      {applied ? (
        <Check className="mt-0.5 h-3 w-3 shrink-0 text-emerald-500" />
      ) : (
        <span className="mt-0.5 shrink-0">{icon}</span>
      )}
      <div className="min-w-0">
        <p className="text-[11px] font-medium leading-tight">
          {applied ? `Applicato: ${action.label}` : action.label}
        </p>
        {action.reasoning && (
          <p className="text-[10px] opacity-70 leading-snug mt-0.5">
            {action.reasoning}
          </p>
        )}
      </div>
    </button>
  );
}
