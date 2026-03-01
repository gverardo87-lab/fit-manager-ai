"""Script temporaneo per compilare campi mancanti sui nuovi esercizi attivati."""
import sqlite3
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

exercise_fills = {
    176: {
        "esecuzione": (
            "1. In piedi, piedi uniti, braccia lungo i fianchi.\n"
            "2. Salta divaricando le gambe e portando le braccia sopra la testa.\n"
            "3. Salta di nuovo riportando piedi uniti e braccia ai fianchi.\n"
            "4. Mantieni un ritmo costante e controllato per 20-30 ripetizioni."
        ),
        "note_sicurezza": (
            "Basso impatto: piegare leggermente le ginocchia. "
            "Evitare con problemi alle ginocchia o pavimento pelvico. "
            "Alternativa low-impact: step-out laterale senza salto."
        ),
    },
    181: {
        "esecuzione": (
            "1. In piedi, posizione eretta, core attivo.\n"
            "2. Fai un passo lungo in avanti con il piede destro.\n"
            "3. Scendi fino a portare il ginocchio posteriore vicino al pavimento.\n"
            "4. Spingi con il piede anteriore e porta avanti il piede sinistro.\n"
            "5. Alterna per 10-12 passi totali."
        ),
        "note_sicurezza": (
            "Mantenere il busto eretto e il core attivo. "
            "Ginocchio anteriore non supera la punta del piede. "
            "Evitare con dolore acuto alle ginocchia."
        ),
    },
    184: {
        "esecuzione": (
            "1. In piedi, piedi larghezza spalle, punte leggermente extra-ruotate.\n"
            "2. Spingi i fianchi indietro come per sedersi.\n"
            "3. Scendi mantenendo il peso sui talloni e il petto alto.\n"
            "4. Raggiungi almeno il parallelo.\n"
            "5. Spingi attraverso i talloni per tornare in piedi. Ripeti 12-15 volte."
        ),
        "note_sicurezza": (
            "Schiena neutra durante tutto il movimento. "
            "Ginocchia in linea con le punte. Adatto a tutti i livelli."
        ),
    },
    185: {
        "esecuzione": (
            "1. In piedi, posizione eretta.\n"
            "2. Solleva il ginocchio destro verso il petto, afferrandolo con le mani.\n"
            "3. Mantieni 1-2 secondi.\n"
            "4. Rilascia e ripeti con la gamba sinistra.\n"
            "5. Alterna per 10 ripetizioni per lato."
        ),
        "note_sicurezza": (
            "Mantenere la postura eretta. Non oscillare il busto. "
            "Adatto come riscaldamento per tutti i livelli."
        ),
    },
    202: {
        "esecuzione": (
            "1. Seduti a terra, gamba anteriore piegata a 90 gradi, posteriore a 90 dietro.\n"
            "2. Mantenere il busto eretto, anche a contatto col pavimento.\n"
            "3. Sentire allungamento nell'anca posteriore e rotazione esterna anteriore.\n"
            "4. Mantenere 30-45 secondi, poi cambiare lato.\n"
            "5. Progressione: inclinarsi in avanti sul ginocchio anteriore."
        ),
        "note_sicurezza": (
            "Non forzare se dolore al ginocchio. Iniziare con range ridotto. "
            "Controindicato con protesi d'anca recente."
        ),
    },
    203: {
        "esecuzione": (
            "1. Affondo profondo, mani a terra all'interno del piede anteriore.\n"
            "2. Ruota il busto verso il ginocchio anteriore, braccio verso il soffitto.\n"
            "3. Riporta la mano a terra e distendi la gamba anteriore.\n"
            "4. Ritorna nella posizione di affondo.\n"
            "5. Ripeti 5 volte per lato."
        ),
        "note_sicurezza": (
            "Movimento fluido e controllato. Non forzare la rotazione toracica. "
            "Adattare il range alla propria mobilita'."
        ),
    },
    204: {
        "esecuzione": (
            "1. In piedi, piedi uniti. Piegati in avanti e tocca le punte dei piedi.\n"
            "2. Piega le ginocchia e scendi in squat profondo mantenendo le mani alle caviglie.\n"
            "3. Solleva il petto, distendi la schiena restando in squat.\n"
            "4. Distendi le ginocchia tornando piegati in avanti.\n"
            "5. Arrotola la schiena tornando in piedi. Ripeti 6-8 volte."
        ),
        "note_sicurezza": (
            "Non forzare la discesa se mobilita' limitata. "
            "Talloni a terra nello squat. Evitare con ernia discale acuta."
        ),
    },
    207: {
        "esecuzione": (
            "1. Sdraiati su un fianco, ginocchia piegate a 90 gradi, braccia distese davanti unite.\n"
            "2. Mantieni ginocchia e anche ferme.\n"
            "3. Apri il braccio superiore ruotando il busto verso il pavimento.\n"
            "4. Segui la mano con lo sguardo. Mantieni 2-3 secondi.\n"
            "5. Ritorna lentamente. Ripeti 8-10 volte per lato."
        ),
        "note_sicurezza": (
            "Non forzare la rotazione. Anche impilate. "
            "Ideale per chi lavora seduto. Controindicato con instabilita' della spalla."
        ),
    },
    209: {
        "esecuzione": (
            "1. Parti in plank alta (mani sotto le spalle).\n"
            "2. Porta il piede destro all'esterno della mano destra in affondo profondo.\n"
            "3. Mantieni 2-3 secondi sentendo l'apertura dell'anca.\n"
            "4. Opzionale: ruota il busto verso il ginocchio estendendo il braccio.\n"
            "5. Riporta il piede e ripeti dall'altro lato. 6-8 ripetizioni per lato."
        ),
        "note_sicurezza": (
            "Adattare il range alla mobilita'. Non forzare l'affondo. "
            "Ottimo pre-allenamento."
        ),
    },
    190: {
        "esecuzione": (
            "1. In quadrupedia (mani sotto le spalle, ginocchia sotto le anche).\n"
            "2. Spingi i fianchi indietro fino a sederti sui talloni.\n"
            "3. Distendi le braccia in avanti, fronte a terra.\n"
            "4. Rilassa completamente schiena, spalle e collo.\n"
            "5. Mantieni 30-60 secondi respirando profondamente."
        ),
        "note_sicurezza": (
            "Posizione di riposo e rilassamento. Sicuro per quasi tutti. "
            "Cuscino sotto i fianchi se ginocchia rigide."
        ),
    },
    193: {
        "esecuzione": (
            "1. Seduti a terra, piante dei piedi unite e ginocchia aperte (farfalla).\n"
            "2. Afferra le caviglie o i piedi.\n"
            "3. Schiena dritta, petto alto.\n"
            "4. Premi le ginocchia verso il pavimento usando i gomiti.\n"
            "5. Mantieni 30-45 secondi. Progressione: inclina il busto in avanti."
        ),
        "note_sicurezza": (
            "Non forzare le ginocchia verso il basso. Movimento dolce e progressivo. "
            "Evitare con pubalgia."
        ),
    },
    194: {
        "esecuzione": (
            "1. Sdraiati supini, ginocchia piegate, piedi a terra.\n"
            "2. Porta la caviglia destra sul ginocchio sinistro (posizione a 4).\n"
            "3. Afferra la coscia sinistra dietro il ginocchio e tirala verso il petto.\n"
            "4. Mantieni 30-45 secondi sentendo l'allungamento nel gluteo destro.\n"
            "5. Cambia lato."
        ),
        "note_sicurezza": (
            "Efficace per sciatica e piriforme. Non forzare. "
            "Testa a terra. Adatto a tutti i livelli."
        ),
    },
    195: {
        "esecuzione": (
            "1. Parti in ginocchio, poi porta il piede destro avanti in affondo basso.\n"
            "2. Ginocchio posteriore a terra su tappetino.\n"
            "3. Spingi i fianchi in avanti sentendo l'allungamento del flessore dell'anca.\n"
            "4. Busto eretto, core attivo.\n"
            "5. Mantieni 30-45 secondi per lato."
        ),
        "note_sicurezza": (
            "Fondamentale per chi sta seduto molte ore. "
            "Non iperestendere la zona lombare. Cuscino sotto il ginocchio se necessario."
        ),
    },
}

safety_only = {
    130: "Esercizio sicuro e fondamentale. Schiena neutra. Evitare compensi con rotazione del bacino. Ideale per riabilitazione e prevenzione mal di schiena.",
    131: "Zona lombare aderente al pavimento. Se la schiena si inarca, ridurre l'ampiezza. Evitare con diastasi addominale non stabilizzata.",
    126: "Non eseguire se dolore lombare. Zona lombare a contatto col pavimento nella fase di discesa. Iniziare con crunch parziali se troppo difficile.",
    129: "Rotazione controllata, non veloce. Zona lombare stabile. Evitare con problemi discali acuti.",
    264: "Richiede buona stabilita' di base. Non lasciar ruotare o abbassare i fianchi. Iniziare con plank se troppo difficile.",
    919: "Attivazione glutea eccellente. Bacino livellato. Non iperestendere la lombare. Adatto a tutti come pre-attivazione.",
    918: "Core stabile durante tutto il movimento. Non compensare con la lombare. Movimento controllato. Adatto a tutti.",
    224: "Richiede buona mobilita' di anca e caviglia. Peso sul tallone. Non forzare la profondita'. Evitare con problemi al ginocchio mediale.",
    227: "Esercizio dolce per l'interno coscia. Schiena a terra. Movimento lento e controllato. Adatto a tutti.",
    165: "Alto impatto. Modificare eliminando il salto per low-impact. Evitare con problemi articolari o pavimento pelvico debole.",
    248: "Scendere lentamente (3-5 sec). Non lasciarsi cadere. Presa sicura. Usare band se necessario. Evitare con problemi alla spalla.",
    233: "Decompressione spinale eccellente. Presa sicura, spalle attive. Iniziare con 10 secondi. Evitare con problemi alla spalla.",
    222: "Elastico alla caviglia. Movimento controllato. Adatto a tutti. Ottimo per pre-attivazione glutei e interno coscia.",
    237: "Anti-rotazione eccellente. Braccia distese, core rigido. Non ruotare. Regolare la resistenza dell'elastico.",
    155: "Scapole retratte durante la trazione. Non compensare col busto. Regolare la resistenza. Adatto a tutti.",
    156: "Non iperestendere la lombare. Core attivo. Regolare la resistenza. Evitare con impingement della spalla.",
    325: "Allungamento dolce adduttori. Non forzare. Schiena dritta. Adatto a tutti. Ottimo dopo sedute prolungate.",
    330: "Apertura profonda delle anche. Non forzare. Cuscini sotto le ginocchia se necessario. Evitare con pubalgia.",
}


def fill_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    db_name = os.path.basename(db_path)

    count_exec = 0
    for eid, fields in exercise_fills.items():
        parts = []
        vals = []
        for k, v in fields.items():
            parts.append(f"{k} = ?")
            vals.append(v)
        vals.append(eid)
        c.execute(f"UPDATE esercizi SET {', '.join(parts)} WHERE id = ?", vals)
        count_exec += 1

    count_safety = 0
    for eid, note in safety_only.items():
        c.execute(
            "UPDATE esercizi SET note_sicurezza = ? "
            "WHERE id = ? AND (note_sicurezza IS NULL OR note_sicurezza = '')",
            (note, eid),
        )
        if c.rowcount:
            count_safety += 1

    conn.commit()
    print(f"{db_name}: {count_exec} con esecuzione+sicurezza, {count_safety} solo sicurezza")

    # Verifica completezza
    c.execute(
        "SELECT COUNT(*) FROM esercizi "
        "WHERE in_subset = 1 AND (esecuzione IS NULL OR esecuzione = '')"
    )
    no_exec = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(*) FROM esercizi "
        "WHERE in_subset = 1 AND (note_sicurezza IS NULL OR note_sicurezza = '')"
    )
    no_safety = c.fetchone()[0]
    print(f"  Subset senza esecuzione: {no_exec} | senza note_sicurezza: {no_safety}")
    conn.close()


if __name__ == "__main__":
    fill_db(os.path.join(BASE_DIR, "crm_dev.db"))
    fill_db(os.path.join(BASE_DIR, "crm.db"))
    print("Done.")
