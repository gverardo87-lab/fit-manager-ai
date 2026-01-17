#!/usr/bin/env python3
# core/ui_components.py
"""
Componenti UI Riusabili - Libreria di componenti Streamlit premium
Per mantenere coerenza visiva e migliorare lo sviluppo
"""

import streamlit as st
from typing import Dict, List, Any, Optional
import pandas as pd

# ════════════════════════════════════════════════════════════
# CARD COMPONENTS
# ════════════════════════════════════════════════════════════

def render_card(
    title: str,
    content: str,
    icon: str = "📌",
    card_type: str = "primary",
    height: Optional[int] = None
) -> None:
    """
    Renderizza una card stilizzata.
    
    Args:
        title: Titolo della card
        content: Contenuto HTML o Markdown
        icon: Emoji per il titolo
        card_type: "primary" | "success" | "accent" | "default"
        height: Altezza opzionale
    """
    card_class = f"card card-{card_type}" if card_type != "default" else "card"
    height_css = f"min-height: {height}px;" if height else ""
    
    st.markdown(f"""
    <div class="{card_class}" style="{height_css}">
        <h3 style="margin-top: 0;">{icon} {title}</h3>
        <div style="color: var(--text-primary); line-height: 1.6;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_box(
    label: str,
    value: str,
    subtext: str = "",
    icon: str = "📊",
    card_type: str = "default"
) -> None:
    """Renderizza una metrica in stile box."""
    card_class = f"card card-{card_type}" if card_type != "default" else "card"
    
    st.markdown(f"""
    <div class="{card_class}">
        <div class="metric-box">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {f'<small style="color: var(--text-secondary);">{subtext}</small>' if subtext else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# BADGE COMPONENTS
# ════════════════════════════════════════════════════════════

def render_badge(
    text: str,
    badge_type: str = "primary",
    inline: bool = False
) -> str:
    """
    Crea un badge stilizzato.
    
    Returns:
        HTML string per il badge
    """
    return f'<span class="badge badge-{badge_type}">{text}</span>'


def render_badges(
    items: List[str],
    badge_type: str = "primary"
) -> None:
    """Renderizza una lista di badge."""
    badges_html = "".join([render_badge(item, badge_type) for item in items])
    st.markdown(badges_html, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# PROGRESS & STATUS COMPONENTS
# ════════════════════════════════════════════════════════════

def render_progress_bar(
    label: str,
    value: float,
    max_value: float = 100,
    show_percentage: bool = True,
    color: str = "var(--primary)"
) -> None:
    """Renderizza una progress bar personalizzata."""
    percentage = (value / max_value) * 100
    
    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; color: var(--text-primary);">{label}</span>
            {f'<span style="color: var(--text-secondary);">{percentage:.0f}%</span>' if show_percentage else ''}
        </div>
        <div style="background: var(--border); height: 8px; border-radius: 4px; overflow: hidden;">
            <div style="background: {color}; height: 100%; width: {percentage}%; border-radius: 4px; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_status_indicator(
    status: str,
    text: str = ""
) -> None:
    """Renderizza un indicatore di status colorato."""
    status_colors = {
        "active": "#00a86b",
        "inactive": "#95a5a6",
        "pending": "#f39c12",
        "error": "#e74c3c",
        "success": "#00a86b"
    }
    
    color = status_colors.get(status.lower(), "#7f8c8d")
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.5rem; margin: 0.5rem 0;">
        <div style="width: 12px; height: 12px; background: {color}; border-radius: 50%; box-shadow: 0 0 4px {color}99;"></div>
        <span style="color: var(--text-secondary);">{text or status}</span>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# DATA DISPLAY COMPONENTS
# ════════════════════════════════════════════════════════════

def render_stats_grid(
    stats: Dict[str, Dict[str, str]],
    columns: int = 4
) -> None:
    """
    Renderizza una griglia di statistiche.
    
    Args:
        stats: Dict con {label: {value: str, subtext: str, icon: str}}
        columns: Numero di colonne
    """
    cols = st.columns(columns, gap="medium")
    
    for idx, (label, data) in enumerate(stats.items()):
        with cols[idx % columns]:
            render_metric_box(
                label=label,
                value=data.get("value", "-"),
                subtext=data.get("subtext", ""),
                icon=data.get("icon", "📊")
            )


def render_client_card(
    name: str,
    goals: List[str],
    level: str,
    active_programs: int,
    on_click_callback = None
) -> None:
    """Renderizza una card per cliente con info rapide."""
    st.markdown(f"""
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
            <div>
                <h4 style="margin: 0; color: var(--primary);">{name}</h4>
                <small style="color: var(--text-secondary);">{level}</small>
            </div>
            <span class="badge badge-primary">{active_programs} Programmi</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
            {" ".join([f'<span class="badge badge-success">{goal}</span>' for goal in goals])}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# INTERACTIVE COMPONENTS
# ════════════════════════════════════════════════════════════

def render_exercise_card(
    exercise_name: str,
    sets: int,
    reps: str,
    weight: str = "",
    notes: str = "",
    expandable: bool = False
) -> None:
    """Renderizza una card per esercizio con dettagli."""
    content = f"""
    <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 1rem; margin-bottom: 0.5rem;">
        <div><strong>{exercise_name}</strong></div>
        <div style="text-align: center;"><small>🔄 {sets}x{reps}</small></div>
        {f'<div style="text-align: center;"><small>⚖️ {weight}</small></div>' if weight else '<div></div>'}
    </div>
    {f'<small style="color: var(--text-secondary); display: block; margin-top: 0.5rem;">{notes}</small>' if notes else ''}
    """
    
    render_card(
        title=exercise_name,
        content=content,
        icon="💪",
        card_type="default"
    )


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
        <h3 style="margin-top: 0; color: var(--primary);">📋 Riepilogo Workout</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <small style="color: var(--text-secondary); text-transform: uppercase;">Goal</small>
                <p style="margin: 0.5rem 0; font-weight: 600;">{goal}</p>
            </div>
            <div>
                <small style="color: var(--text-secondary); text-transform: uppercase;">Livello</small>
                <p style="margin: 0.5rem 0; font-weight: 600;">{level}</p>
            </div>
            <div>
                <small style="color: var(--text-secondary); text-transform: uppercase;">Durata</small>
                <p style="margin: 0.5rem 0; font-weight: 600;">{duration}</p>
            </div>
            <div>
                <small style="color: var(--text-secondary); text-transform: uppercase;">Frequenza</small>
                <p style="margin: 0.5rem 0; font-weight: 600;">{frequency}</p>
            </div>
            <div style="grid-column: 1 / -1;">
                <small style="color: var(--text-secondary); text-transform: uppercase;">Esercizi</small>
                <p style="margin: 0.5rem 0; font-weight: 600;">{exercises} esercizi</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# LAYOUT HELPERS
# ════════════════════════════════════════════════════════════

def create_section_header(
    title: str,
    description: str = "",
    icon: str = "📌"
) -> None:
    """Crea un header di sezione stilizzato."""
    st.markdown(f"""
    <div style="margin: 2rem 0 1rem 0;">
        <h2 style="margin: 0; color: var(--dark);">
            {icon} {title}
        </h2>
        {f'<p style="margin: 0.5rem 0 0 0; color: var(--text-secondary);">{description}</p>' if description else ''}
    </div>
    """, unsafe_allow_html=True)


def render_divider(style: str = "normal") -> None:
    """Renderizza un divider stilizzato."""
    if style == "normal":
        st.divider()
    elif style == "thin":
        st.markdown("<hr style='margin: 0.5rem 0; border: none; height: 1px; background: var(--border);'>", unsafe_allow_html=True)
    elif style == "gradient":
        st.markdown("<hr style='margin: 1rem 0; border: none; height: 2px; background: linear-gradient(90deg, transparent, var(--primary), transparent);'>", unsafe_allow_html=True)


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
    <div style="margin: 1rem 0;">
        <label style="display: block; margin-bottom: 0.5rem; font-weight: 600; color: var(--text-primary);">
            {label}
        </label>
    </div>
    """, unsafe_allow_html=True)
    
    if input_type == "text":
        return st.text_input("", placeholder=placeholder, key=key, help=help_text, label_visibility="collapsed")
    elif input_type == "number":
        return st.number_input("", key=key, help=help_text, label_visibility="collapsed")
    elif input_type == "textarea":
        return st.text_area("", placeholder=placeholder, key=key, help=help_text, label_visibility="collapsed")


# ════════════════════════════════════════════════════════════
# ANIMATION & STYLING HELPERS
# ════════════════════════════════════════════════════════════

def render_success_message(text: str) -> None:
    """Messaggio di successo stilizzato."""
    st.markdown(f"""
    <div style="background: var(--secondary-light); border-left: 4px solid var(--secondary); border-radius: 6px; padding: 1rem; margin: 1rem 0;">
        <strong style="color: var(--secondary);">✅ {text}</strong>
    </div>
    """, unsafe_allow_html=True)


def render_error_message(text: str) -> None:
    """Messaggio di errore stilizzato."""
    st.markdown(f"""
    <div style="background: #ffe6e6; border-left: 4px solid var(--danger); border-radius: 6px; padding: 1rem; margin: 1rem 0;">
        <strong style="color: var(--danger);">❌ {text}</strong>
    </div>
    """, unsafe_allow_html=True)


def render_info_message(text: str) -> None:
    """Messaggio informativo stilizzato."""
    st.markdown(f"""
    <div style="background: var(--primary-light); border-left: 4px solid var(--primary); border-radius: 6px; padding: 1rem; margin: 1rem 0;">
        <strong style="color: var(--primary);">ℹ️ {text}</strong>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    # Test components
    st.title("🎨 UI Components Preview")
    
    st.header("Cards")
    col1, col2 = st.columns(2)
    with col1:
        render_card("Test Card", "Questo è un contenuto di test", "📌", "primary")
    with col2:
        render_metric_box("Clienti", "42", "Attivi questa settimana", "👥", "success")
    
    st.header("Badges")
    render_badges(["Ipertrofia", "Forza", "Resistenza"], "primary")
    
    st.header("Progress")
    render_progress_bar("Allenamenti Completati", 7, 10)
    
    st.header("Status")
    render_status_indicator("active", "Sistema Operativo")
    
    st.header("Messages")
    render_success_message("Programma salvato con successo!")
    render_error_message("Errore nel salvataggio")
    render_info_message("Questa è un'informazione importante")
