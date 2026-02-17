"""
Script per ricalcolare i crediti usati basandosi sugli eventi 'Fatto' in agenda
"""
import sqlite3

conn = sqlite3.connect('data/crm.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=" * 60)
print("RICALCOLO CREDITI USATI DA EVENTI COMPLETATI")
print("=" * 60)

# Get all active contracts
cursor.execute("SELECT id, id_cliente, crediti_usati FROM contratti WHERE chiuso = 0")
contracts = cursor.fetchall()

for contract in contracts:
    contract_id = contract['id']
    client_id = contract['id_cliente']
    current_usati = contract['crediti_usati']
    
    # Count completed events for this contract
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM agenda
        WHERE id_contratto = ? AND stato = 'Fatto'
    """, (contract_id,))
    
    actual_usati = cursor.fetchone()['count']
    
    print(f"\nContratto {contract_id} (Cliente {client_id}):")
    print(f"  DB crediti_usati: {current_usati}")
    print(f"  Eventi 'Fatto': {actual_usati}")
    
    if current_usati != actual_usati:
        print(f"  ⚠️ MISMATCH! Aggiornamento necessario: {current_usati} → {actual_usati}")
        cursor.execute("""
            UPDATE contratti
            SET crediti_usati = ?
            WHERE id = ?
        """, (actual_usati, contract_id))
        print(f"  ✅ Aggiornato!")
    else:
        print(f"  ✅ OK - già sincronizzato")

conn.commit()

# Verify
print("\n" + "=" * 60)
print("VERIFICA POST-AGGIORNAMENTO")
print("=" * 60)
cursor.execute("""
    SELECT id, id_cliente, crediti_totali, crediti_usati 
    FROM contratti WHERE chiuso = 0
""")
for row in cursor.fetchall():
    residui = row['crediti_totali'] - row['crediti_usati']
    print(f"Contract {row['id']} | Cliente {row['id_cliente']} | Totali: {row['crediti_totali']} | Usati: {row['crediti_usati']} | Residui: {residui}")

conn.close()
print("\n✅ Ricalcolo completato!")
