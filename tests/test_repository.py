"""
Test rapido per verificare i repository dopo migrazione
"""
from core.repositories import ClientRepository, ContractRepository, FinancialRepository, AgendaRepository
from datetime import date, datetime

def test_client_repository():
    print("=" * 60)
    print("TEST CLIENT REPOSITORY")
    print("=" * 60)
    
    client_repo = ClientRepository()
    
    # Test get_all_active
    print("\n1. Test get_all_active()")
    try:
        clienti = client_repo.get_all_active()
        print(f"   ✅ Funziona! Trovati {len(clienti)} clienti attivi")
        if clienti:
            print(f"   Primo cliente: {clienti[0].nome} {clienti[0].cognome} (ID: {clienti[0].id})")
        else:
            print("   ⚠️ NESSUN CLIENTE ATTIVO TROVATO!")
            print("   Verifico se ci sono clienti nel database...")
            
            # Query diretta per debug
            with client_repo.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as total FROM clienti")
                total = cursor.fetchone()[0]
                print(f"   Totale clienti in DB: {total}")
                
                cursor.execute("SELECT COUNT(*) as total FROM clienti WHERE stato='Attivo'")
                attivi = cursor.fetchone()[0]
                print(f"   Clienti con stato='Attivo': {attivi}")
                
                cursor.execute("SELECT id, nome, cognome, stato FROM clienti LIMIT 5")
                rows = cursor.fetchall()
                print("\n   Primi 5 clienti in DB:")
                for row in rows:
                    print(f"      - ID {row[0]}: {row[1]} {row[2]} (stato: {row[3]})")
    except Exception as e:
        print(f"   ❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()

def test_financial_repository():
    print("\n" + "=" * 60)
    print("TEST FINANCIAL REPOSITORY")
    print("=" * 60)
    
    financial_repo = FinancialRepository()
    
    # Test get_cash_balance
    print("\n1. Test get_cash_balance()")
    try:
        oggi = date.today()
        balance = financial_repo.get_cash_balance()
        print(f"   ✅ Saldo cassa totale: €{balance.get('saldo_cassa', 0):.2f}")
        print(f"   Incassato: €{balance.get('incassato', 0):.2f}")
        print(f"   Speso: €{balance.get('speso', 0):.2f}")
    except Exception as e:
        print(f"   ❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()

def test_contract_repository():
    print("\n" + "=" * 60)
    print("TEST CONTRACT REPOSITORY")
    print("=" * 60)
    
    contract_repo = ContractRepository()
    
    # Test get_pending_rates
    print("\n1. Test get_pending_rates()")
    try:
        rate = contract_repo.get_pending_rates(only_future=False)
        print(f"   ✅ Trovate {len(rate)} rate pendenti")
        if rate:
            print(f"   Prima rata: {rate[0].get('descrizione', 'N/A')} - €{rate[0].get('importo_previsto', 0):.2f}")
    except Exception as e:
        print(f"   ❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()

def test_agenda_repository():
    print("\n" + "=" * 60)
    print("TEST AGENDA REPOSITORY")
    print("=" * 60)
    
    agenda_repo = AgendaRepository()
    
    # Test get_events_by_range
    print("\n1. Test get_events_by_range()")
    try:
        oggi = datetime.now()
        eventi = agenda_repo.get_events_by_range(oggi, oggi)
        print(f"   ✅ Trovati {len(eventi)} eventi oggi")
    except Exception as e:
        print(f"   ❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n🔍 VERIFICA REPOSITORY DOPO MIGRAZIONE\n")
    
    test_client_repository()
    test_financial_repository()
    test_contract_repository()
    test_agenda_repository()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETATI")
    print("=" * 60)
