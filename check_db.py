import sqlite3
from datetime import date

conn = sqlite3.connect('data/crm.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Tables
print("=" * 60)
print("TABLES IN DATABASE")
print("=" * 60)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(tables)

# Check agenda table
print("\n" + "=" * 60)
print("AGENDA TABLE - COUNT")
print("=" * 60)
cursor.execute("SELECT COUNT(*) FROM agenda")
print(f"Total events: {cursor.fetchone()[0]}")

# Sample events
print("\n" + "=" * 60)
print("SAMPLE EVENTS (first 10)")
print("=" * 60)
cursor.execute("SELECT id, data_inizio, titolo, id_cliente, categoria, stato FROM agenda LIMIT 10")
for row in cursor.fetchall():
    print(f"ID {row['id']}: {row['data_inizio']} | {row['titolo']} | Cliente: {row['id_cliente']} | {row['categoria']} | {row['stato']}")

# Check contratti
print("\n" + "=" * 60)
print("CONTRATTI - ACTIVE")
print("=" * 60)
cursor.execute("SELECT id, id_cliente, crediti_totali, crediti_usati, chiuso FROM contratti WHERE chiuso = 0")
for row in cursor.fetchall():
    residui = row['crediti_totali'] - row['crediti_usati']
    print(f"Contract {row['id']} | Cliente {row['id_cliente']} | Totali: {row['crediti_totali']} | Usati: {row['crediti_usati']} | Residui: {residui}")

# Check events by client with active contract
print("\n" + "=" * 60)
print("EVENTS BY CLIENT WITH ACTIVE CONTRACT")
print("=" * 60)
cursor.execute("""
    SELECT c.id_cliente, COUNT(*) as num_events
    FROM contratti c
    LEFT JOIN agenda a ON a.id_cliente = c.id_cliente
    WHERE c.chiuso = 0
    GROUP BY c.id_cliente
""")
for row in cursor.fetchall():
    print(f"Cliente {row['id_cliente']}: {row['num_events']} events in agenda")

# Check events WHERE id_contratto IS NOT NULL
print("\n" + "=" * 60)
print("EVENTS WITH CONTRACT REFERENCE")
print("=" * 60)
cursor.execute("SELECT id, data_inizio, id_cliente, id_contratto FROM agenda WHERE id_contratto IS NOT NULL LIMIT 10")
for row in cursor.fetchall():
    print(f"Event {row['id']} | Cliente {row['id_cliente']} | Contratto {row['id_contratto']} | Data {row['data_inizio']}")

conn.close()
