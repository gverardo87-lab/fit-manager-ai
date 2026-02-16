import sqlite3
import json

conn = sqlite3.connect('data/crm.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Lista tabelle
print("=== TABELLE DATABASE ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
for t in tables:
    print(f"  - {t}")

# Trova Laura Baccelliere
print("\n=== CERCA CLIENTE LAURA ===")
cur.execute("SELECT * FROM clienti WHERE cognome LIKE '%Baccell%' OR nome LIKE '%Laura%'")
clienti = [dict(row) for row in cur.fetchall()]
print(json.dumps(clienti, indent=2, default=str))

if clienti:
    id_cliente = clienti[0]['id']
    print(f"\n=== CONTRATTI CLIENTE ID={id_cliente} ===")
    
    # Contratti
    cur.execute("SELECT * FROM contratti WHERE id_cliente = ?", (id_cliente,))
    contratti = [dict(row) for row in cur.fetchall()]
    print(json.dumps(contratti, indent=2, default=str))
    
    if contratti:
        id_contratto = contratti[0]['id']
        print(f"\n=== MOVIMENTI CASSA CONTRATTO ID={id_contratto} ===")
        
        # Movimenti cassa
        cur.execute("""
            SELECT id, tipo, categoria, importo, data_effettiva, id_rata
            FROM movimenti_cassa 
            WHERE id_contratto = ?
            ORDER BY data_effettiva
        """, (id_contratto,))
        movimenti = [dict(row) for row in cur.fetchall()]
        print(json.dumps(movimenti, indent=2, default=str))
        
        # Somme per categoria
        print(f"\n=== ANALISI PAGAMENTI ===")
        cur.execute("""
            SELECT 
                categoria,
                COUNT(*) as num_movimenti,
                SUM(importo) as totale
            FROM movimenti_cassa
            WHERE id_contratto = ?
            GROUP BY categoria
        """, (id_contratto,))
        riepilogo = [dict(row) for row in cur.fetchall()]
        print(json.dumps(riepilogo, indent=2, default=str))
        
        # Somma totale
        cur.execute("""
            SELECT 
                SUM(CASE WHEN categoria = 'ACCONTO_CONTRATTO' THEN importo ELSE 0 END) as tot_acconto,
                SUM(CASE WHEN categoria = 'RATA_CONTRATTO' THEN importo ELSE 0 END) as tot_rate,
                SUM(CASE WHEN categoria IN ('ACCONTO_CONTRATTO', 'RATA_CONTRATTO') THEN importo ELSE 0 END) as totale_con_acconto
            FROM movimenti_cassa
            WHERE id_contratto = ?
        """, (id_contratto,))
        somme = dict(cur.fetchone())
        print("\n=== SOMME CALCOLATE ===")
        print(f"Acconto: €{somme['tot_acconto']}")
        print(f"Rate: €{somme['tot_rate']}")
        print(f"Totale (acconto+rate): €{somme['totale_con_acconto']}")
        
        # Contratto info
        contratto = contratti[0]
        print("\n=== CONTRATTO ===")
        print(f"Prezzo Totale: €{contratto['prezzo_totale']}")
        print(f"Totale Versato (DB): €{contratto['totale_versato']}")
        print(f"Residuo (DB): €{contratto['prezzo_totale'] - contratto['totale_versato']}")
        print(f"Residuo CORRETTO: €{contratto['prezzo_totale'] - somme['totale_con_acconto']}")
        
        # Rate programmate
        print(f"\n=== RATE PROGRAMMATE ===")
        cur.execute("SELECT * FROM rate_programmate WHERE id_contratto = ? ORDER BY numero_rata", (id_contratto,))
        rate = [dict(row) for row in cur.fetchall()]
        for r in rate:
            print(f"Rata {r['numero_rata']}: €{r['importo_previsto']} - saldato €{r['importo_saldato']} - stato: {r['stato']}")

conn.close()
