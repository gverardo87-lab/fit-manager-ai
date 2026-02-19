#!/usr/bin/env python3
# core/ui_components.py
"""
Componenti UI Riusabili - Libreria di componenti Streamlit premium.
Tutti i colori usano variabili CSS dal design system (server/assets/styles.css).
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd
from pathlib import Path
from core.error_handler import safe_operation, ErrorSeverity


# ════════════════════════════════════════════════════════════
# CSS LOADER (MUST be called at top of every page)
# ════════════════════════════════════════════════════════════

@safe_operation(
    operation_name="Carica CSS Centralizzato",
    severity=ErrorSeverity.LOW,
    fallback_return=None
)
def load_custom_css() -> None:
    """
    Carica il CSS centralizzato da server/assets/styles.css.
    Chiamare all'inizio di ogni pagina Streamlit.
    """
    css_path = Path(__file__).resolve().parents[1] / "server" / "assets" / "styles.css"

    if not css_path.exists():
        return

    with open(css_path, encoding='utf-8') as f:
        css_content = f.read()

    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# BADGE & STATUS COMPONENTS
# ════════════════════════════════════════════════════════════

def badge(text: str, variant: str = "info", icon: str = "") -> str:
    """
    Badge colorato semantico. Usa classi CSS dal design system.

    Args:
        text: Testo da mostrare
        variant: success, warning, danger, info, neutral, primary, accent
        icon: Emoji opzionale
    """
    # Map variant names to CSS classes
    css_map = {
        'success': 'badge-success',
        'warning': 'badge-accent',
        'danger': 'badge-danger',
        'info': 'badge-info',
        'neutral': 'badge-neutral',
        'primary': 'badge-primary',
        'accent': 'badge-accent',
    }
    css_class = css_map.get(variant, 'badge-primary')
    icon_html = f'{icon} ' if icon else ''
    return f'<span class="badge {css_class}">{icon_html}{text}</span>'


def status_badge(status: str) -> str:
    """Badge automatico per stati comuni (pagamenti, contratti, etc)."""
    status_map = {
        'SALDATO': ('success', ''), 'PAGATO': ('success', ''),
        'COMPLETATO': ('success', ''), 'ATTIVO': ('success', ''),
        'PARZIALE': ('warning', ''), 'IN CORSO': ('warning', ''),
        'SCADUTO': ('warning', ''),
        'PENDENTE': ('danger', ''), 'NON PAGATO': ('danger', ''),
        'IN RITARDO': ('danger', ''), 'SCADUTA': ('danger', ''),
        'ANNULLATO': ('neutral', ''), 'ARCHIVIATO': ('neutral', ''),
    }

    variant, icon = status_map.get(status.upper(), ('primary', ''))
    return badge(status, variant, icon)


# ════════════════════════════════════════════════════════════
# CURRENCY FORMATTING
# ════════════════════════════════════════════════════════════

def format_currency(value: float, decimals: int = 2, symbol: str = "\u20ac") -> str:
    """Formatta valore monetario in stile europeo: € 1.234,56"""
    if value is None:
        return f"{symbol} 0,00"
    formatted = f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{symbol} {formatted}"


def format_currency_colored(value: float, positive_good: bool = True) -> str:
    """Currency con colore semantico (verde positivo, rosso negativo)."""
    formatted = format_currency(value)

    if value > 0:
        css_class = "positive" if positive_good else "negative"
    elif value < 0:
        css_class = "negative" if positive_good else "positive"
    else:
        css_class = "neutral"

    return f'<span class="{css_class}" style="font-weight: 600;">{formatted}</span>'


# ════════════════════════════════════════════════════════════
# EMPTY STATES & LOADING
# ════════════════════════════════════════════════════════════

def empty_state_component(title: str, description: str, icon: str = "", action_text: str = None) -> str:
    """Empty state quando non ci sono dati."""
    action_html = ''
    if action_text:
        action_html = f'<div style="margin-top: 20px;"><span style="background: var(--primary); color: white; padding: 10px 20px; border-radius: var(--radius-sm); font-weight: 600; display: inline-block;">{action_text}</span></div>'

    return f"""
    <div style="text-align: center; padding: 48px 20px; background: var(--bg-card); border-radius: var(--radius); border: 1px dashed var(--border-color); margin: 24px 0;">
        <div style="font-size: 3rem; margin-bottom: 12px;">{icon}</div>
        <h3 style="margin-bottom: 8px; font-size: 1.25rem;">{title}</h3>
        <p style="color: var(--text-secondary); font-size: 0.95rem; max-width: 400px; margin: 0 auto;">{description}</p>
        {action_html}
    </div>
    """


def loading_message(message: str = "Carico i tuoi dati", icon: str = "") -> str:
    """Messaggio loading per st.spinner()."""
    return f"{icon} {message}..."


# ════════════════════════════════════════════════════════════
# SECTION HEADERS & DIVIDERS
# ════════════════════════════════════════════════════════════

def section_divider_component(title: str = None, icon: str = None) -> str:
    """Divider tra sezioni con titolo opzionale."""
    if title:
        icon_html = f'{icon} ' if icon else ''
        return f"""
        <div style="display: flex; align-items: center; margin: 28px 0 20px 0; gap: 12px;">
            <div style="flex: 1; height: 1px; background: linear-gradient(90deg, transparent, var(--border-color), transparent);"></div>
            <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-primary); white-space: nowrap;">{icon_html}{title}</div>
            <div style="flex: 1; height: 1px; background: linear-gradient(90deg, transparent, var(--border-color), transparent);"></div>
        </div>
        """
    return '<div style="height: 1px; background: var(--border-color); margin: 20px 0;"></div>'


def create_section_header(title: str, description: str = "", icon: str = "") -> None:
    """Crea un header di sezione stilizzato."""
    icon_html = f'{icon} ' if icon else ''
    desc_html = f'<p style="margin: 0.25rem 0 0 0; color: var(--text-secondary); font-size: 0.9rem;">{description}</p>' if description else ''
    st.markdown(f"""
    <div style="margin: 1.5rem 0 1rem 0;">
        <h2 style="margin: 0;">{icon_html}{title}</h2>
        {desc_html}
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# CARD COMPONENTS
# ════════════════════════════════════════════════════════════

def render_card(
    title: str,
    content: str,
    icon: str = "",
    card_type: str = "primary",
    height: Optional[int] = None
) -> None:
    """Renderizza una card stilizzata."""
    card_class = f"card card-{card_type}" if card_type != "default" else "card"
    height_css = f"min-height: {height}px;" if height else ""
    icon_html = f'{icon} ' if icon else ''

    st.markdown(f"""
    <div class="{card_class}" style="{height_css}">
        <h3>{icon_html}{title}</h3>
        <div style="line-height: 1.6;">{content}</div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_box(
    label: str,
    value: str,
    subtext: str = "",
    icon: str = "",
    card_type: str = "default",
    value_color: str = "",
    trend_class: str = "neutral"
) -> None:
    """Renderizza una metrica in stile KPI box.

    Args:
        value_color: colore CSS per il valore, es. "var(--primary)". Default: colore tema.
        trend_class: classe CSS per il trend: "positive", "negative", "neutral".
    """
    color_style = f' style="color: {value_color};"' if value_color else ''
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value"{color_style}>{value}</div>
        {f'<div class="kpi-trend {trend_class}">{subtext}</div>' if subtext else ''}
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# BADGE RENDERING
# ════════════════════════════════════════════════════════════

def render_badge(text: str, badge_type: str = "primary", inline: bool = False) -> str:
    """Crea un badge HTML."""
    return f'<span class="badge badge-{badge_type}">{text}</span>'


def render_badges(items: List[str], badge_type: str = "primary") -> None:
    """Renderizza una lista di badge."""
    badges_html = "".join([render_badge(item, badge_type) for item in items])
    st.markdown(badges_html, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PROGRESS & STATUS
# ════════════════════════════════════════════════════════════

def progress_bar_component(percentage: float, label: str = "", show_text: bool = True, height: int = 8) -> str:
    """Progress bar con colore dinamico."""
    pct = max(0, min(100, percentage))

    if pct >= 80:
        color = "var(--secondary)"
    elif pct >= 50:
        color = "var(--accent)"
    else:
        color = "var(--danger)"

    label_html = f'<div style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 6px; font-weight: 500;">{label}</div>' if label else ''
    text_html = f'<div style="font-size: 0.85rem; color: var(--text-primary); margin-top: 4px; font-weight: 600;">{pct:.0f}%</div>' if show_text else ''

    return f"""
    <div style="width: 100%;">
        {label_html}
        <div style="background: var(--bg-elevated); border-radius: {height}px; height: {height}px; overflow: hidden;">
            <div style="background: {color}; height: 100%; width: {pct}%; border-radius: {height}px; transition: width 0.5s ease;"></div>
        </div>
        {text_html}
    </div>
    """


def render_progress_bar(
    label: str,
    value: float,
    max_value: float = 100,
    show_percentage: bool = True,
    color: str = "var(--primary)"
) -> None:
    """Renderizza una progress bar."""
    percentage = (value / max_value) * 100 if max_value > 0 else 0

    st.markdown(f"""
    <div style="margin: 0.75rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
            <span style="font-weight: 600; color: var(--text-primary); font-size: 0.9rem;">{label}</span>
            {f'<span style="color: var(--text-secondary); font-size: 0.85rem;">{percentage:.0f}%</span>' if show_percentage else ''}
        </div>
        <div style="background: var(--bg-elevated); height: 6px; border-radius: 3px; overflow: hidden;">
            <div style="background: {color}; height: 100%; width: {percentage}%; border-radius: 3px; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_indicator(status: str, text: str = "") -> None:
    """Renderizza un indicatore di status con dot colorato."""
    status_colors = {
        "active": "var(--secondary)",
        "inactive": "var(--text-muted)",
        "pending": "var(--accent)",
        "error": "var(--danger)",
        "success": "var(--secondary)"
    }
    color = status_colors.get(status.lower(), "var(--text-muted)")

    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.25rem 0;">
        <div style="width: 10px; height: 10px; background: {color}; border-radius: 50%; box-shadow: 0 0 6px {color};"></div>
        <span style="color: var(--text-secondary); font-size: 0.9rem;">{text or status}</span>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# DATA DISPLAY
# ════════════════════════════════════════════════════════════

def render_stats_grid(stats: Dict[str, Dict[str, str]], columns: int = 4) -> None:
    """Renderizza una griglia di KPI statistiche."""
    cols = st.columns(columns, gap="medium")

    for idx, (label, data) in enumerate(stats.items()):
        with cols[idx % columns]:
            render_metric_box(
                label=label,
                value=data.get("value", "-"),
                subtext=data.get("subtext", ""),
                icon=data.get("icon", "")
            )


def render_client_card(
    name: str,
    goals: List[str],
    level: str,
    active_programs: int,
    on_click_callback=None
) -> None:
    """Renderizza una card per cliente."""
    goals_html = " ".join([f'<span class="badge badge-success">{goal}</span>' for goal in goals])
    st.markdown(f"""
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.75rem;">
            <div>
                <h4 style="margin: 0; color: var(--primary);">{name}</h4>
                <small style="color: var(--text-secondary);">{level}</small>
            </div>
            <span class="badge badge-primary">{active_programs} Programmi</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.4rem;">{goals_html}</div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# WORKOUT COMPONENTS
# ════════════════════════════════════════════════════════════

def render_exercise_card(
    exercise_name: str,
    sets: int,
    reps: str,
    weight: str = "",
    notes: str = "",
    expandable: bool = False
) -> None:
    """Renderizza una card per esercizio."""
    weight_html = f'<div style="text-align: center; color: var(--accent);"><small>{weight}</small></div>' if weight else '<div></div>'
    notes_html = f'<small style="color: var(--text-muted); display: block; margin-top: 0.4rem;">{notes}</small>' if notes else ''

    st.markdown(f"""
    <div class="card" style="padding: 1rem;">
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 0.75rem; align-items: center;">
            <div><strong style="color: var(--text-primary);">{exercise_name}</strong></div>
            <div style="text-align: center; color: var(--text-secondary);"><small>{sets}x{reps}</small></div>
            {weight_html}
        </div>
        {notes_html}
    </div>
    """, unsafe_allow_html=True)


def render_workout_summary(
    goal: str,
    level: str,
    duration: str,
    frequency: str,
    exercises: int
) -> None:
    """Renderizza un riepilogo di workout."""
    st.markdown(f"""
    <div class="card card-primary">
        <h3 style="color: var(--primary);">Riepilogo Workout</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <small style="color: var(--text-muted); text-transform: uppercase; font-size: 0.7rem;">Goal</small>
                <p style="margin: 0.25rem 0; font-weight: 600;">{goal}</p>
            </div>
            <div>
                <small style="color: var(--text-muted); text-transform: uppercase; font-size: 0.7rem;">Livello</small>
                <p style="margin: 0.25rem 0; font-weight: 600;">{level}</p>
            </div>
            <div>
                <small style="color: var(--text-muted); text-transform: uppercase; font-size: 0.7rem;">Durata</small>
                <p style="margin: 0.25rem 0; font-weight: 600;">{duration}</p>
            </div>
            <div>
                <small style="color: var(--text-muted); text-transform: uppercase; font-size: 0.7rem;">Frequenza</small>
                <p style="margin: 0.25rem 0; font-weight: 600;">{frequency}</p>
            </div>
            <div style="grid-column: 1 / -1;">
                <small style="color: var(--text-muted); text-transform: uppercase; font-size: 0.7rem;">Esercizi</small>
                <p style="margin: 0.25rem 0; font-weight: 600;">{exercises} esercizi</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# MESSAGE COMPONENTS
# ════════════════════════════════════════════════════════════

def render_success_message(text: str) -> None:
    """Messaggio di successo."""
    st.markdown(f"""
    <div style="background: var(--secondary-light); border-left: 4px solid var(--secondary); border-radius: var(--radius-sm); padding: 1rem; margin: 0.75rem 0;">
        <strong style="color: var(--secondary);">{text}</strong>
    </div>
    """, unsafe_allow_html=True)


def render_error_message(text: str) -> None:
    """Messaggio di errore."""
    st.markdown(f"""
    <div style="background: var(--danger-light); border-left: 4px solid var(--danger); border-radius: var(--radius-sm); padding: 1rem; margin: 0.75rem 0;">
        <strong style="color: var(--danger);">{text}</strong>
    </div>
    """, unsafe_allow_html=True)


def render_info_message(text: str) -> None:
    """Messaggio informativo."""
    st.markdown(f"""
    <div style="background: var(--primary-light); border-left: 4px solid var(--primary); border-radius: var(--radius-sm); padding: 1rem; margin: 0.75rem 0;">
        <strong style="color: var(--primary);">{text}</strong>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# DIVIDER HELPER
# ════════════════════════════════════════════════════════════

def render_divider(style: str = "normal") -> None:
    """Renderizza un divider stilizzato."""
    if style == "normal":
        st.divider()
    elif style == "thin":
        st.markdown("<hr style='margin: 0.5rem 0; border: none; height: 1px; background: var(--border-color);'>", unsafe_allow_html=True)
    elif style == "gradient":
        st.markdown("<hr style='margin: 1rem 0; border: none; height: 1px; background: linear-gradient(90deg, transparent, var(--primary), transparent);'>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# CONFIRMATION DIALOGS
# ════════════════════════════════════════════════════════════

def render_confirm_delete(
    item_id: Any,
    session_key: str,
    details: str,
    confirm_callback,
    key_prefix: str = "confirm_del"
) -> None:
    """
    Pannello conferma eliminazione CRITICA (checkbox + bottone disabilitato).
    Usato per azioni irreversibili come delete contract, delete event.

    Args:
        item_id: ID dell'elemento da eliminare
        session_key: Chiave session_state che controlla la visibilita' (es. 'deleting_plan_id')
        details: Testo markdown con i dettagli dell'elemento
        confirm_callback: Funzione da chiamare alla conferma (riceve item_id)
        key_prefix: Prefisso per le chiavi Streamlit (deve essere unico per pagina)
    """
    st.markdown("---")
    st.error("### ⚠️ Conferma Eliminazione")
    st.warning(f"{details}\n\n⚠️ **Questa azione NON può essere annullata!**")

    conferma = st.checkbox(
        "✓ Sono sicuro di voler procedere con l'eliminazione",
        key=f"{key_prefix}_check_{item_id}"
    )

    col_del, col_cancel = st.columns(2)
    with col_del:
        if st.button(
            "🗑️ Elimina Definitivamente",
            use_container_width=True,
            type="primary",
            disabled=not conferma,
            key=f"{key_prefix}_btn_{item_id}"
        ):
            confirm_callback(item_id)
            st.session_state[session_key] = None
            st.rerun()
    with col_cancel:
        if st.button("❌ Annulla", use_container_width=True, key=f"{key_prefix}_cancel_{item_id}"):
            st.session_state[session_key] = None
            st.rerun()


def render_confirm_action(
    item_id: Any,
    session_key: str,
    message: str,
    confirm_label: str,
    confirm_callback,
    key_prefix: str = "confirm_act"
) -> None:
    """
    Pannello conferma LEGGERA (solo warning + 2 bottoni, senza checkbox).
    Usato per azioni reversibili o a basso impatto come cancel event, delete rate.

    Args:
        item_id: ID dell'elemento
        session_key: Chiave session_state che controlla la visibilita'
        message: Messaggio di warning
        confirm_label: Testo del bottone conferma (es. "Cancella Sessione")
        confirm_callback: Funzione da chiamare alla conferma (riceve item_id)
        key_prefix: Prefisso per le chiavi Streamlit
    """
    st.warning(message)

    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button(
            confirm_label,
            use_container_width=True,
            type="primary",
            key=f"{key_prefix}_btn_{item_id}"
        ):
            confirm_callback(item_id)
            st.session_state[session_key] = None
            st.rerun()
    with col_no:
        if st.button("❌ Annulla", use_container_width=True, key=f"{key_prefix}_cancel_{item_id}"):
            st.session_state[session_key] = None
            st.rerun()


# ════════════════════════════════════════════════════════════
# FORM HELPERS
# ════════════════════════════════════════════════════════════

def render_input_group(
    label: str,
    input_type: str = "text",
    placeholder: str = "",
    key: str = "",
    help_text: str = ""
) -> Any:
    """Renderizza un input group stilizzato."""
    st.markdown(f"""
    <div style="margin: 0.75rem 0 0.25rem 0;">
        <label style="display: block; font-weight: 600; color: var(--text-secondary); font-size: 0.9rem;">{label}</label>
    </div>
    """, unsafe_allow_html=True)

    if input_type == "text":
        return st.text_input("", placeholder=placeholder, key=key, help=help_text, label_visibility="collapsed")
    elif input_type == "number":
        return st.number_input("", key=key, help=help_text, label_visibility="collapsed")
    elif input_type == "textarea":
        return st.text_area("", placeholder=placeholder, key=key, help=help_text, label_visibility="collapsed")
