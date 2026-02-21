// src/lib/auth.ts
/**
 * Auth Service — gestione JWT token e stato autenticazione.
 *
 * Architettura:
 * - Il token JWT viene salvato in un cookie (js-cookie)
 * - I dati trainer (id, nome, cognome) vengono salvati in un cookie separato
 * - Nessun Context/Provider qui: l'auth state e' derivato dalla presenza del cookie
 * - Le funzioni sono pure: login() chiama l'API e salva, logout() rimuove
 * - I componenti usano getStoredTrainer() per leggere lo stato corrente
 *
 * Perche' cookie e non localStorage?
 * - Persistono tra tab del browser
 * - Accessibili sia lato client che (potenzialmente) lato server
 * - Scadenza controllabile (qui: 8 ore, allineata al JWT_EXPIRE_MINUTES del backend)
 */

import Cookies from "js-cookie";
import apiClient, { TOKEN_COOKIE } from "./api-client";
import type {
  TrainerLogin,
  TrainerRegister,
  TokenResponse,
} from "@/types/api";

// Cookie per i dati del trainer (JSON serializzato)
const TRAINER_COOKIE = "fitmanager_trainer";

// Durata cookie: 8 ore (allineata a JWT_EXPIRE_MINUTES=480 nel backend)
const COOKIE_EXPIRES_DAYS = 8 / 24; // 8 ore in giorni

/** Dati trainer salvati nel cookie dopo il login. */
export interface StoredTrainer {
  id: number;
  nome: string;
  cognome: string;
}

// ════════════════════════════════════════════════════════════
// LOGIN
// ════════════════════════════════════════════════════════════

/**
 * Esegue il login: chiama POST /api/auth/login, salva token e dati trainer.
 * Ritorna i dati del trainer per uso immediato nel componente.
 */
export async function login(credentials: TrainerLogin): Promise<StoredTrainer> {
  const { data } = await apiClient.post<TokenResponse>(
    "/auth/login",
    credentials
  );

  // Salva token nel cookie
  Cookies.set(TOKEN_COOKIE, data.access_token, {
    expires: COOKIE_EXPIRES_DAYS,
    sameSite: "lax",
  });

  // Salva dati trainer
  const trainer: StoredTrainer = {
    id: data.trainer_id,
    nome: data.nome,
    cognome: data.cognome,
  };
  Cookies.set(TRAINER_COOKIE, JSON.stringify(trainer), {
    expires: COOKIE_EXPIRES_DAYS,
    sameSite: "lax",
  });

  return trainer;
}

// ════════════════════════════════════════════════════════════
// REGISTER
// ════════════════════════════════════════════════════════════

/**
 * Registra un nuovo trainer: chiama POST /api/auth/register.
 * Il backend ritorna un JWT — il trainer e' gia' loggato.
 */
export async function register(
  payload: TrainerRegister
): Promise<StoredTrainer> {
  const { data } = await apiClient.post<TokenResponse>(
    "/auth/register",
    payload
  );

  Cookies.set(TOKEN_COOKIE, data.access_token, {
    expires: COOKIE_EXPIRES_DAYS,
    sameSite: "lax",
  });

  const trainer: StoredTrainer = {
    id: data.trainer_id,
    nome: data.nome,
    cognome: data.cognome,
  };
  Cookies.set(TRAINER_COOKIE, JSON.stringify(trainer), {
    expires: COOKIE_EXPIRES_DAYS,
    sameSite: "lax",
  });

  return trainer;
}

// ════════════════════════════════════════════════════════════
// LOGOUT
// ════════════════════════════════════════════════════════════

/** Rimuove token e dati trainer. Redirect opzionale. */
export function logout(redirect = true): void {
  Cookies.remove(TOKEN_COOKIE);
  Cookies.remove(TRAINER_COOKIE);

  if (redirect && typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

// ════════════════════════════════════════════════════════════
// STATO CORRENTE
// ════════════════════════════════════════════════════════════

/** Legge i dati trainer dal cookie. Null se non autenticato. */
export function getStoredTrainer(): StoredTrainer | null {
  const raw = Cookies.get(TRAINER_COOKIE);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as StoredTrainer;
  } catch {
    return null;
  }
}

/** Controlla se l'utente ha un token valido (non scaduto lato cookie). */
export function isAuthenticated(): boolean {
  return !!Cookies.get(TOKEN_COOKIE);
}
