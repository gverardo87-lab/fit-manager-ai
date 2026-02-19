# server/pages/09_Impostazioni.py
"""
Impostazioni - Backup, Ripristino e Info Sistema

Funzionalita':
- Genera backup crittografato del database (.fitbackup)
- Ripristina database da backup (con verifica e conferma)
- Info sistema: dimensione DB, conteggio tabelle
"""

import streamlit as st
from datetime import datetime
from core.services.backup_service import BackupService
from core.ui_components import (
    load_custom_css,
    section_divider_component,
    render_metric_box,
    render_success_message,
    render_error_message,
)

# ════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Impostazioni",
    page_icon=":material/settings:",
    layout="wide"
)

load_custom_css()

backup_service = BackupService()

# ════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════

if 'backup_ready' not in st.session_state:
    st.session_state.backup_ready = None  # (bytes, manifest) tuple
if 'restore_manifest' not in st.session_state:
    st.session_state.restore_manifest = None
if 'restore_data' not in st.session_state:
    st.session_state.restore_data = None
if 'restore_password' not in st.session_state:
    st.session_state.restore_password = None
if 'restore_error' not in st.session_state:
    st.session_state.restore_error = None

# ════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════

st.title("Impostazioni")
st.caption("Gestisci backup, ripristino e configurazione del sistema")

# ════════════════════════════════════════════════════════════
# SEZIONE 1: BACKUP DATI
# ════════════════════════════════════════════════════════════

st.markdown(
    section_divider_component("Backup Dati", ""),
    unsafe_allow_html=True
)

st.info(
    "Il backup salva **tutti i dati** del tuo database (clienti, contratti, "
    "sessioni, cassa, assessment, schede) in un file crittografato `.fitbackup`. "
    "Solo chi conosce la password potra' aprirlo."
)

col_bk1, col_bk2 = st.columns(2)

with col_bk1:
    bk_password = st.text_input(
        "Password per il backup",
        type="password",
        key="bk_password",
        help="Minimo 4 caratteri. Scegli una password che ricorderai!"
    )

with col_bk2:
    bk_password_confirm = st.text_input(
        "Conferma password",
        type="password",
        key="bk_password_confirm",
        help="Ripeti la stessa password"
    )

if st.button("Genera Backup", type="primary", use_container_width=True):
    if not bk_password or len(bk_password) < 4:
        st.error("La password deve avere almeno 4 caratteri")
    elif bk_password != bk_password_confirm:
        st.error("Le password non corrispondono")
    else:
        with st.spinner("Creo il backup crittografato..."):
            result = backup_service.create_backup(bk_password)
            if result is not None:
                st.session_state.backup_ready = result
                st.rerun()
            else:
                st.error("Errore nella creazione del backup")

# Mostra download se il backup e' pronto
if st.session_state.backup_ready is not None:
    backup_bytes, manifest = st.session_state.backup_ready

    render_success_message(
        f"Backup pronto! {manifest.total_records} record, "
        f"{len(manifest.tables)} tabelle, "
        f"{backup_service._format_size(len(backup_bytes))}"
    )

    with st.expander("Dettagli backup"):
        for table_name, count in sorted(manifest.tables.items()):
            st.text(f"  {table_name}: {count} record")

    filename = f"FitManager_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.fitbackup"

    st.download_button(
        label="Scarica Backup (.fitbackup)",
        data=backup_bytes,
        file_name=filename,
        mime="application/octet-stream",
        use_container_width=True,
        type="primary",
    )

# ════════════════════════════════════════════════════════════
# SEZIONE 2: RIPRISTINA BACKUP
# ════════════════════════════════════════════════════════════

st.markdown(
    section_divider_component("Ripristina Backup", ""),
    unsafe_allow_html=True
)

st.warning(
    "Il ripristino **sostituisce tutti i dati attuali** con quelli del backup. "
    "Prima del ripristino viene creata automaticamente una copia di sicurezza."
)

uploaded_file = st.file_uploader(
    "Carica file di backup",
    type=["fitbackup"],
    key="restore_uploader",
    help="Seleziona un file .fitbackup creato in precedenza"
)

if uploaded_file is not None:
    restore_pwd = st.text_input(
        "Password del backup",
        type="password",
        key="restore_pwd_input",
        help="La password usata quando hai creato questo backup"
    )

    if st.button("Verifica Backup", use_container_width=True):
        if not restore_pwd:
            st.error("Inserisci la password del backup")
        else:
            with st.spinner("Verifico il backup..."):
                raw_data = uploaded_file.getvalue()

                if len(raw_data) > 100 * 1024 * 1024:
                    st.session_state.restore_error = (
                        "Il file supera la dimensione massima consentita (100 MB)"
                    )
                    st.session_state.restore_manifest = None
                else:
                    try:
                        manifest = backup_service.validate_backup(raw_data, restore_pwd)
                        if manifest is not None:
                            st.session_state.restore_manifest = manifest
                            st.session_state.restore_data = raw_data
                            st.session_state.restore_password = restore_pwd
                            st.session_state.restore_error = None
                        else:
                            st.session_state.restore_error = (
                                "Password non corretta o file corrotto"
                            )
                            st.session_state.restore_manifest = None
                    except ValueError as e:
                        st.session_state.restore_error = str(e)
                        st.session_state.restore_manifest = None
                    except Exception as e:
                        st.session_state.restore_error = f"Errore imprevisto: {str(e)}"
                        st.session_state.restore_manifest = None

                st.rerun()

    # Mostra errore se presente
    if st.session_state.restore_error:
        render_error_message(st.session_state.restore_error)

    # Mostra confronto se il manifest e' stato validato
    if st.session_state.restore_manifest is not None:
        manifest = st.session_state.restore_manifest

        render_success_message("Backup verificato con successo!")

        # Confronto: DB attuale vs backup
        st.subheader("Confronto: Dati Attuali vs Backup")

        current_stats = backup_service.get_current_db_stats()
        current_total = sum(current_stats.values()) if current_stats else 0

        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.markdown("**Database Attuale**")
            st.metric("Record totali", current_total)
            with st.expander("Dettaglio tabelle attuali"):
                for t, c in sorted(current_stats.items()):
                    st.text(f"  {t}: {c}")

        with col_c2:
            st.markdown(
                f"**Backup del {manifest.backup_date.strftime('%d/%m/%Y %H:%M')}**"
            )
            st.metric("Record totali", manifest.total_records)
            with st.expander("Dettaglio tabelle backup"):
                for t, c in sorted(manifest.tables.items()):
                    st.text(f"  {t}: {c}")

        st.markdown("---")

        # Conferma CRITICA: checkbox + bottone disabilitato
        st.error("### Conferma Ripristino")
        st.warning(
            "**ATTENZIONE**: Tutti i dati attuali saranno SOSTITUITI "
            "con quelli del backup. Una copia di sicurezza sara' salvata "
            "automaticamente in `data/crm_pre_restore.db.bak`.\n\n"
            "**Questa azione NON puo' essere annullata!**"
        )

        conferma_restore = st.checkbox(
            "Sono sicuro di voler ripristinare il database dal backup",
            key="conferma_restore_check"
        )

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            if st.button(
                "Ripristina Database",
                type="primary",
                use_container_width=True,
                disabled=not conferma_restore,
                key="btn_restore_confirm"
            ):
                with st.spinner("Ripristino in corso..."):
                    try:
                        success = backup_service.restore_backup(
                            st.session_state.restore_data,
                            st.session_state.restore_password
                        )
                    except Exception:
                        success = False

                    if success:
                        # Reset stato
                        st.session_state.restore_manifest = None
                        st.session_state.restore_data = None
                        st.session_state.restore_password = None
                        st.session_state.restore_error = None
                        st.session_state.backup_ready = None
                        st.success(
                            "Database ripristinato con successo! "
                            "La pagina si ricarichera' tra pochi secondi."
                        )
                        st.balloons()
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(
                            "Errore durante il ripristino. "
                            "I dati originali sono stati preservati."
                        )

        with col_r2:
            if st.button(
                "Annulla",
                use_container_width=True,
                key="btn_restore_cancel"
            ):
                st.session_state.restore_manifest = None
                st.session_state.restore_data = None
                st.session_state.restore_password = None
                st.session_state.restore_error = None
                st.rerun()

# ════════════════════════════════════════════════════════════
# SEZIONE 3: INFO SISTEMA
# ════════════════════════════════════════════════════════════

st.markdown(
    section_divider_component("Info Sistema", ""),
    unsafe_allow_html=True
)

db_info = backup_service.get_db_info()

if db_info.get("exists"):
    current_stats = backup_service.get_current_db_stats()
    total = sum(current_stats.values()) if current_stats else 0

    col_i1, col_i2, col_i3 = st.columns(3)

    with col_i1:
        render_metric_box(
            "Dimensione DB",
            db_info["size_display"],
            db_info["path"],
        )

    with col_i2:
        render_metric_box(
            "Record Totali",
            str(total),
            f"{len(current_stats)} tabelle",
        )

    with col_i3:
        render_metric_box(
            "Ultima Modifica",
            db_info["last_modified"].strftime("%d/%m/%Y %H:%M"),
        )

    with st.expander("Dettaglio tabelle database"):
        if current_stats:
            for table_name, count in sorted(current_stats.items()):
                col_t1, col_t2 = st.columns([3, 1])
                col_t1.text(table_name)
                col_t2.text(str(count))
        else:
            st.info("Nessuna tabella trovata")
else:
    st.error("Database non trovato!")
