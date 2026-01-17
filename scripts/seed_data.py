#!/usr/bin/env python3
"""
Seed Data Script per FitManager AI
Popola il database con dati di esempio per testing e demo.

Usage:
    python scripts/seed_data.py              # Aggiungi dati
    python scripts/seed_data.py --reset      # Reset DB e aggiungi dati
    python scripts/seed_data.py --clear      # Solo reset DB
"""

import sys
from pathlib import Path

# Aggiungi root al path per import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.crm_db import CrmDBManager
from datetime import date, datetime, timedelta
import argparse
import json


def clear_database(db: CrmDBManager):
    """Elimina tutti i dati dal database (mantiene schema)"""
    print("🗑️  Clearing database...")
    
    with db._connect() as conn:
        cursor = conn.cursor()
        
        # Ordine importante per foreign keys (se abilitati)
        tables = [
            'progress_records',
            'workout_plans',
            'client_assessment_followup',
            'client_assessment_initial',
            'misurazioni',
            'agenda',
            'rate_programmate',
            'movimenti_cassa',
            'spese_ricorrenti',
            'contratti',
            'clienti'
        ]
        
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            print(f"   ✓ Cleared {table}")
        
        conn.commit()
    
    print("✅ Database cleared successfully\n")


def seed_clienti(db: CrmDBManager):
    """Crea clienti di esempio"""
    print("👥 Seeding clienti...")
    
    clienti_data = [
        {
            "nome": "Mario",
            "cognome": "Rossi",
            "telefono": "+39 333 1234567",
            "email": "mario.rossi@example.com",
            "data_nascita": "1985-03-15",
            "sesso": "Uomo",
            "anamnesi_json": json.dumps({
                "patologie": ["Nessuna"],
                "farmaci": [],
                "note": "Sedentario da 5 anni, vuole tornare in forma"
            })
        },
        {
            "nome": "Laura",
            "cognome": "Bianchi",
            "telefono": "+39 340 9876543",
            "email": "laura.bianchi@example.com",
            "data_nascita": "1990-07-22",
            "sesso": "Donna",
            "anamnesi_json": json.dumps({
                "patologie": ["Mal di schiena cronico"],
                "farmaci": [],
                "note": "Ex atleta, ora manager. Stress elevato."
            })
        },
        {
            "nome": "Giuseppe",
            "cognome": "Verdi",
            "telefono": "+39 328 5555555",
            "email": "giuseppe.verdi@example.com",
            "data_nascita": "1978-11-10",
            "sesso": "Uomo",
            "anamnesi_json": json.dumps({
                "patologie": ["Ipertensione controllata"],
                "farmaci": ["Ramipril 5mg"],
                "note": "Medico consiglia attività moderata"
            })
        },
        {
            "nome": "Sofia",
            "cognome": "Romano",
            "telefono": "+39 345 7777777",
            "email": "sofia.romano@example.com",
            "data_nascita": "1995-05-05",
            "sesso": "Donna",
            "anamnesi_json": json.dumps({
                "patologie": ["Nessuna"],
                "farmaci": [],
                "note": "Competitiva, obiettivo gara bodybuilding"
            })
        },
        {
            "nome": "Luca",
            "cognome": "Ferrari",
            "telefono": "+39 347 4444444",
            "email": "luca.ferrari@example.com",
            "data_nascita": "2000-12-20",
            "sesso": "Uomo",
            "anamnesi_json": json.dumps({
                "patologie": ["Nessuna"],
                "farmaci": [],
                "note": "Studente universitario, principiante assoluto"
            })
        }
    ]
    
    client_ids = {}
    
    with db._connect() as conn:
        cursor = conn.cursor()
        for cliente in clienti_data:
            cursor.execute("""
                INSERT INTO clienti (nome, cognome, telefono, email, data_nascita, sesso, anamnesi_json, stato)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Attivo')
            """, (
                cliente['nome'], cliente['cognome'], cliente['telefono'],
                cliente['email'], cliente['data_nascita'], cliente['sesso'],
                cliente['anamnesi_json']
            ))
            client_ids[f"{cliente['nome']} {cliente['cognome']}"] = cursor.lastrowid
            print(f"   ✓ Created client: {cliente['nome']} {cliente['cognome']} (ID: {cursor.lastrowid})")
        
        conn.commit()
    
    print(f"✅ Created {len(clienti_data)} clients\n")
    return client_ids


def main():
    parser = argparse.ArgumentParser(description='Seed FitManager AI database with sample data')
    parser.add_argument('--reset', action='store_true', help='Clear database before seeding')
    parser.add_argument('--clear', action='store_true', help='Only clear database (no seeding)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🌱 FitManager AI - Database Seed Script")
    print("=" * 60)
    print()
    
    # Initialize database manager
    db = CrmDBManager()
    
    if args.clear or args.reset:
        clear_database(db)
    
    if args.clear:
        print("✅ Database cleared. Exiting.\n")
        return
    
    print("📦 Starting data seeding...\n")
    
    # Seed data in dependency order
    client_ids = seed_clienti(db)
    
    print("=" * 60)
    print("✅ SEEDING COMPLETE!")
    print("=" * 60)
    print()
    print("📊 Summary:")
    print(f"   • {len(client_ids)} clients")
    print()
    print("🚀 Ready to test! Run: streamlit run server/app.py")
    print()


if __name__ == "__main__":
    main()
