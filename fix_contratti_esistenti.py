"""
Script per correggere i contratti esistenti applicando il fix dell'acconto.
Esegue sincronizza_stato_contratti_da_movimenti() per ricalcolare totale_versato includendo l'acconto.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.crm_db import CrmDBManager

def main():
    db = CrmDBManager()
    
    print("=" * 70)
    print("CORREZIONE CONTRATTI ESISTENTI - Include ACCONTO nel calcolo")
    print("=" * 70)
    
    # Prima: mostra i contratti con problema
    print("\n📊 SITUAZIONE PRIMA DELLA CORREZIONE:")
    print("-" * 70)
    
    with db._connect() as conn:
        cur = conn.cursor()
        
        # Trova tutti i contratti con movimenti
        cur.execute("""
            SELECT DISTINCT c.id, c.prezzo_totale, c.totale_versato, c.stato_pagamento
            FROM contratti c
            WHERE EXISTS (
                SELECT 1 FROM movimenti_cassa m 
                WHERE m.id_contratto = c.id
            )
            AND c.chiuso = 0
            ORDER BY c.id
        """)
        contratti_pre = [dict(row) for row in cur.fetchall()]
        
        print(f"\nTrovati {len(contratti_pre)} contratti attivi con pagamenti:")
        
        for c in contratti_pre:
            # Calcola acconto e rate separatamente
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN categoria = 'ACCONTO_CONTRATTO' THEN importo ELSE 0 END) as acconto,
                    SUM(CASE WHEN categoria = 'RATA_CONTRATTO' THEN importo ELSE 0 END) as rate,
                    SUM(CASE WHEN categoria IN ('ACCONTO_CONTRATTO', 'RATA_CONTRATTO') THEN importo ELSE 0 END) as totale_corretto
                FROM movimenti_cassa
                WHERE id_contratto = ?
            """, (c['id'],))
            movimenti = dict(cur.fetchone())
            
            residuo_db = c['prezzo_totale'] - c['totale_versato']
            residuo_corretto = c['prezzo_totale'] - movimenti['totale_corretto']
            
            print(f"\n  Contratto ID={c['id']}:")
            print(f"    Prezzo: €{c['prezzo_totale']:.2f}")
            print(f"    Acconto: €{movimenti['acconto']:.2f}")
            print(f"    Rate: €{movimenti['rate']:.2f}")
            print(f"    Totale Versato (DB): €{c['totale_versato']:.2f} {'❌' if c['totale_versato'] != movimenti['totale_corretto'] else '✅'}")
            print(f"    Totale CORRETTO: €{movimenti['totale_corretto']:.2f}")
            print(f"    Residuo (DB): €{residuo_db:.2f}")
            print(f"    Residuo CORRETTO: €{residuo_corretto:.2f}")
            
            if c['totale_versato'] != movimenti['totale_corretto']:
                print(f"    ⚠️  DIFFERENZA: €{movimenti['totale_corretto'] - c['totale_versato']:.2f} (acconto non contato!)")
    
    # Chiedi conferma
    print("\n" + "=" * 70)
    risposta = input("\n🔧 Vuoi CORREGGERE i contratti eseguendo la sincronizzazione? (si/no): ").strip().lower()
    
    if risposta not in ['si', 's', 'yes', 'y']:
        print("\n❌ Operazione annullata dall'utente.")
        return
    
    # Esegui la sincronizzazione
    print("\n🔄 Esecuzione sincronizzazione...")
    try:
        db.sincronizza_stato_contratti_da_movimenti()
        print("✅ Sincronizzazione completata con successo!")
    except Exception as e:
        print(f"❌ ERRORE durante sincronizzazione: {e}")
        return
    
    # Dopo: mostra i contratti corretti
    print("\n" + "=" * 70)
    print("📊 SITUAZIONE DOPO LA CORREZIONE:")
    print("-" * 70)
    
    with db._connect() as conn:
        cur = conn.cursor()
        
        for c in contratti_pre:
            # Rileggi contratto aggiornato
            cur.execute("SELECT * FROM contratti WHERE id = ?", (c['id'],))
            c_nuovo = dict(cur.fetchone())
            
            # Calcola totale corretto dai movimenti
            cur.execute("""
                SELECT 
                    SUM(CASE WHEN categoria = 'ACCONTO_CONTRATTO' THEN importo ELSE 0 END) as acconto,
                    SUM(CASE WHEN categoria = 'RATA_CONTRATTO' THEN importo ELSE 0 END) as rate,
                    SUM(CASE WHEN categoria IN ('ACCONTO_CONTRATTO', 'RATA_CONTRATTO') THEN importo ELSE 0 END) as totale
                FROM movimenti_cassa
                WHERE id_contratto = ?
            """, (c['id'],))
            movimenti = dict(cur.fetchone())
            
            residuo_nuovo = c_nuovo['prezzo_totale'] - c_nuovo['totale_versato']
            
            print(f"\n  Contratto ID={c['id']}:")
            print(f"    Prezzo: €{c_nuovo['prezzo_totale']:.2f}")
            print(f"    Acconto: €{movimenti['acconto']:.2f}")
            print(f"    Rate: €{movimenti['rate']:.2f}")
            print(f"    Totale Versato (DB): €{c_nuovo['totale_versato']:.2f} ✅")
            print(f"    Residuo: €{residuo_nuovo:.2f} ✅")
            print(f"    Stato: {c_nuovo['stato_pagamento']}")
            
            # Verifica correttezza
            if c_nuovo['totale_versato'] == movimenti['totale']:
                print(f"    ✅ CORRETTO: totale_versato coincide con movimenti")
            else:
                print(f"    ❌ ATTENZIONE: c'è ancora discrepanza!")
    
    print("\n" + "=" * 70)
    print("✅ CORREZIONE COMPLETATA!")
    print("=" * 70)
    print("\nPuoi ora ricaricare la pagina Streamlit per vedere i dati corretti.")

if __name__ == "__main__":
    main()
