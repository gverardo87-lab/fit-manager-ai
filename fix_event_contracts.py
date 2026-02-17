"""
Script per verificare e correggere eventi senza collegamento al contratto
"""
import sqlite3

conn = sqlite3.connect('data/crm.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("EVENTI SENZA COLLEGAMENTO CONTRATTO")
print("=" * 60)

# Get events without contract but with cliente
cursor.execute("""
    SELECT a.id, a.data_inizio, a.id_cliente, a.categoria, a.stato, a.id_contratto
    FROM agenda a
    WHERE a.id_cliente IS NOT NULL 
    AND a.id_contratto IS NULL
    ORDER BY a.data_inizio DESC
""")

events_to_fix = cursor.fetchall()

if not events_to_fix:
    print("✅ Tutti gli eventi con cliente hanno riferimento contratto!")
else:
    print(f"\n⚠️ Trovati {len(events_to_fix)} eventi senza contratto:\n")
    
    for event in events_to_fix:
        print(f"Event {event['id']} | Cliente {event['id_cliente']} | {event['data_inizio']} | {event['categoria']} | {event['stato']}")
        
        # Find active contract for this client
        cursor.execute("""
            SELECT id FROM contratti
            WHERE id_cliente = ? AND chiuso = 0
            ORDER BY data_inizio DESC
            LIMIT 1
        """, (event['id_cliente'],))
        
        contract = cursor.fetchone()
        
        if contract:
            print(f"  → Contratto attivo trovato: {contract['id']}")
            
            # Link event to contract
            cursor.execute("""
                UPDATE agenda
                SET id_contratto = ?
                WHERE id = ?
            """, (contract['id'], event['id']))
            
            print(f"  ✅ Collegato a contratto {contract['id']}")
        else:
            print(f"  ⚠️ NESSUN contratto attivo trovato per cliente {event['id_cliente']}")

conn.commit()

# Verify
print("\n" + "=" * 60)
print("VERIFICA POST-FIX")
print("=" * 60)

cursor.execute("""
    SELECT COUNT(*) as count
    FROM agenda a
    WHERE a.id_cliente IS NOT NULL 
    AND a.id_contratto IS NULL
""")

orphan_count = cursor.fetchone()['count']
print(f"Eventi rimasti senza contratto: {orphan_count}")

conn.close()
print("\n✅ Fix completato!")
