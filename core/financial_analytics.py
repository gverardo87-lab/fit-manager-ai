"""
Financial Analytics Module - Advanced Metrics
Metriche avanzate per competere con Trainerize, TrueCoach, MarketLabs

Funzionalità:
- LTV (Lifetime Value) per cliente
- CAC (Customer Acquisition Cost)
- Churn Rate & Prediction
- Cohort Analysis
- Revenue per Trainer
- MRR (Monthly Recurring Revenue)
- ARR (Annual Recurring Revenue)
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

from core.repositories.base_repository import BaseRepository


class FinancialAnalytics(BaseRepository):
    """
    Advanced Financial Analytics Engine

    Implementa metriche standard dell'industria fitness SaaS:
    - Customer Lifetime Value (LTV)
    - Customer Acquisition Cost (CAC)
    - Churn Rate & Retention
    - Monthly Recurring Revenue (MRR)
    - Cohort Analysis

    Eredita da BaseRepository per accesso diretto al DB
    senza dipendere dal legacy CrmDBManager.
    """

    def __init__(self):
        super().__init__()

    # ══════════════════════════════════════════════════════════
    # 1. LIFETIME VALUE (LTV) ANALYSIS
    # ══════════════════════════════════════════════════════════

    def calculate_customer_ltv(
        self,
        id_cliente: int,
        as_of_date: date = None
    ) -> Dict:
        """
        Calcola il Lifetime Value di un singolo cliente

        Formula Standard:
        LTV = (Fatturato Totale Cliente - Costi Variabili Cliente) / Tempo Attivo

        Args:
            id_cliente: ID del cliente
            as_of_date: Data di riferimento (default: oggi)

        Returns:
            {
                'ltv_total': float,           # Valore totale generato
                'ltv_monthly': float,         # Valore medio mensile
                'revenue_total': float,       # Fatturato totale
                'num_contracts': int,         # Numero contratti
                'active_months': int,         # Mesi di attività
                'avg_contract_value': float,  # Valore medio contratto
                'retention_rate': float,      # % retention (0-100)
                'first_purchase': str,        # Data primo acquisto
                'last_purchase': str,         # Data ultimo acquisto
                'status': str,                # Attivo/Inattivo
                'predicted_ltv_12m': float    # LTV previsto prossimi 12 mesi
            }
        """
        if as_of_date is None:
            as_of_date = date.today()

        with self._connect() as conn:
            # Recupera dati cliente
            cliente = conn.execute("""
                SELECT nome, cognome, stato, data_creazione
                FROM clienti
                WHERE id = ?
            """, (id_cliente,)).fetchone()

            if not cliente:
                return None

            # Recupera tutti i contratti del cliente
            contratti = conn.execute("""
                SELECT
                    id, data_vendita, data_inizio, data_scadenza,
                    prezzo_totale, totale_versato, crediti_totali,
                    crediti_usati, stato_pagamento
                FROM contratti
                WHERE id_cliente = ?
                ORDER BY data_vendita
            """, (id_cliente,)).fetchall()

            if not contratti:
                return {
                    'ltv_total': 0.0,
                    'ltv_monthly': 0.0,
                    'revenue_total': 0.0,
                    'num_contracts': 0,
                    'active_months': 0,
                    'avg_contract_value': 0.0,
                    'retention_rate': 0.0,
                    'first_purchase': None,
                    'last_purchase': None,
                    'status': cliente['stato'],
                    'predicted_ltv_12m': 0.0
                }

            # Calcoli base
            num_contracts = len(contratti)
            revenue_total = sum(c['totale_versato'] for c in contratti)
            avg_contract_value = revenue_total / num_contracts if num_contracts > 0 else 0

            # Date primo/ultimo acquisto
            first_purchase = min(c['data_vendita'] for c in contratti if c['data_vendita'])
            last_purchase = max(c['data_vendita'] for c in contratti if c['data_vendita'])

            # Calcola mesi di attività (dalla prima vendita a oggi)
            if first_purchase:
                first_date = datetime.strptime(first_purchase, '%Y-%m-%d').date()
                active_months = ((as_of_date.year - first_date.year) * 12 +
                               (as_of_date.month - first_date.month))
                active_months = max(1, active_months)  # Almeno 1 mese
            else:
                active_months = 1

            # LTV mensile
            ltv_monthly = revenue_total / active_months if active_months > 0 else 0

            # Retention rate (% di crediti utilizzati rispetto al totale acquistato)
            crediti_totali = sum(c['crediti_totali'] or 0 for c in contratti)
            crediti_usati = sum(c['crediti_usati'] or 0 for c in contratti)
            retention_rate = (crediti_usati / crediti_totali * 100) if crediti_totali > 0 else 0

            # Predizione LTV prossimi 12 mesi (media ultimi mesi * 12)
            # Semplificato: se cliente attivo, usa media mensile * 12
            if cliente['stato'] == 'Attivo':
                predicted_ltv_12m = ltv_monthly * 12
            else:
                predicted_ltv_12m = 0.0

            return {
                'ltv_total': round(revenue_total, 2),
                'ltv_monthly': round(ltv_monthly, 2),
                'revenue_total': round(revenue_total, 2),
                'num_contracts': num_contracts,
                'active_months': active_months,
                'avg_contract_value': round(avg_contract_value, 2),
                'retention_rate': round(retention_rate, 2),
                'first_purchase': first_purchase,
                'last_purchase': last_purchase,
                'status': cliente['stato'],
                'predicted_ltv_12m': round(predicted_ltv_12m, 2),
                'cliente_nome': f"{cliente['nome']} {cliente['cognome']}"
            }

    def calculate_portfolio_ltv(self, as_of_date: date = None) -> Dict:
        """
        Calcola LTV medio dell'intero portfolio clienti

        Returns:
            {
                'avg_ltv_per_customer': float,
                'median_ltv': float,
                'total_ltv_portfolio': float,
                'num_customers': int,
                'ltv_distribution': List[Dict]  # Per grafici
            }
        """
        if as_of_date is None:
            as_of_date = date.today()

        with self._connect() as conn:
            # Tutti i clienti attivi
            clienti = conn.execute("""
                SELECT id FROM clienti WHERE stato = 'Attivo'
            """).fetchall()

            if not clienti:
                return {
                    'avg_ltv_per_customer': 0.0,
                    'median_ltv': 0.0,
                    'total_ltv_portfolio': 0.0,
                    'num_customers': 0,
                    'ltv_distribution': []
                }

            # Calcola LTV per ogni cliente
            ltv_values = []
            for c in clienti:
                ltv_data = self.calculate_customer_ltv(c['id'], as_of_date)
                if ltv_data:
                    ltv_values.append({
                        'id_cliente': c['id'],
                        'ltv': ltv_data['ltv_total'],
                        'ltv_monthly': ltv_data['ltv_monthly'],
                        'cliente_nome': ltv_data['cliente_nome']
                    })

            if not ltv_values:
                return {
                    'avg_ltv_per_customer': 0.0,
                    'median_ltv': 0.0,
                    'total_ltv_portfolio': 0.0,
                    'num_customers': 0,
                    'ltv_distribution': []
                }

            ltv_amounts = [v['ltv'] for v in ltv_values]

            return {
                'avg_ltv_per_customer': round(np.mean(ltv_amounts), 2),
                'median_ltv': round(np.median(ltv_amounts), 2),
                'total_ltv_portfolio': round(sum(ltv_amounts), 2),
                'num_customers': len(ltv_values),
                'ltv_distribution': sorted(ltv_values, key=lambda x: x['ltv'], reverse=True)
            }

    # ══════════════════════════════════════════════════════════
    # 2. CUSTOMER ACQUISITION COST (CAC)
    # ══════════════════════════════════════════════════════════

    def calculate_cac(
        self,
        data_inizio: date,
        data_fine: date,
        costi_marketing: float = 0.0,
        costi_sales: float = 0.0
    ) -> Dict:
        """
        Calcola il Customer Acquisition Cost per un periodo

        Formula Standard:
        CAC = (Costi Marketing + Costi Vendita) / Numero Nuovi Clienti

        Args:
            data_inizio: Inizio periodo
            data_fine: Fine periodo
            costi_marketing: Costi marketing/pubblicità del periodo
            costi_sales: Costi commerciali (se hai venditori)

        Returns:
            {
                'cac': float,                    # CAC medio per cliente
                'num_new_customers': int,        # Nuovi clienti acquisiti
                'total_acquisition_cost': float, # Costo totale acquisizione
                'avg_first_purchase': float,     # Valore medio primo acquisto
                'ltv_cac_ratio': float,          # Rapporto LTV/CAC (target: 3+)
                'payback_months': float          # Mesi per recuperare CAC
            }
        """
        with self._connect() as conn:
            # Nuovi clienti nel periodo
            nuovi_clienti = conn.execute("""
                SELECT id, nome, cognome, data_creazione
                FROM clienti
                WHERE DATE(data_creazione) BETWEEN ? AND ?
            """, (data_inizio, data_fine)).fetchall()

            num_new_customers = len(nuovi_clienti)

            if num_new_customers == 0:
                return {
                    'cac': 0.0,
                    'num_new_customers': 0,
                    'total_acquisition_cost': costi_marketing + costi_sales,
                    'avg_first_purchase': 0.0,
                    'ltv_cac_ratio': 0.0,
                    'payback_months': 0.0
                }

            # Costi totali di acquisizione
            # Nota: Se hai tracciato spese marketing in movimenti_cassa, somma anche quelle
            spese_marketing_db = conn.execute("""
                SELECT COALESCE(SUM(importo), 0) as totale
                FROM movimenti_cassa
                WHERE tipo = 'USCITA'
                  AND categoria IN ('Marketing', 'Pubblicità', 'Ads')
                  AND data_effettiva BETWEEN ? AND ?
            """, (data_inizio, data_fine)).fetchone()

            total_acquisition_cost = (
                costi_marketing +
                costi_sales +
                (spese_marketing_db['totale'] if spese_marketing_db else 0)
            )

            # CAC medio
            cac = total_acquisition_cost / num_new_customers

            # Valore medio primo acquisto (per calcolare payback)
            first_purchases = []
            for cliente in nuovi_clienti:
                primo_contratto = conn.execute("""
                    SELECT prezzo_totale, totale_versato
                    FROM contratti
                    WHERE id_cliente = ?
                    ORDER BY data_vendita
                    LIMIT 1
                """, (cliente['id'],)).fetchone()

                if primo_contratto:
                    first_purchases.append(primo_contratto['totale_versato'] or 0)

            avg_first_purchase = (
                sum(first_purchases) / len(first_purchases)
                if first_purchases else 0
            )

            # LTV medio dei nuovi clienti (per calcolare LTV/CAC ratio)
            ltv_sum = 0
            for cliente in nuovi_clienti:
                ltv_data = self.calculate_customer_ltv(cliente['id'])
                if ltv_data:
                    ltv_sum += ltv_data['ltv_total']

            avg_ltv = ltv_sum / num_new_customers if num_new_customers > 0 else 0

            # LTV/CAC Ratio (Industry benchmark: 3+ è buono)
            ltv_cac_ratio = avg_ltv / cac if cac > 0 else 0

            # Payback period (mesi per recuperare il CAC)
            # Assumendo revenue mensile costante
            ltv_monthly_avg = avg_ltv / 12 if avg_ltv > 0 else 0
            payback_months = cac / ltv_monthly_avg if ltv_monthly_avg > 0 else 0

            return {
                'cac': round(cac, 2),
                'num_new_customers': num_new_customers,
                'total_acquisition_cost': round(total_acquisition_cost, 2),
                'avg_first_purchase': round(avg_first_purchase, 2),
                'ltv_cac_ratio': round(ltv_cac_ratio, 2),
                'payback_months': round(payback_months, 1),
                'avg_ltv_new_customers': round(avg_ltv, 2)
            }

    # ══════════════════════════════════════════════════════════
    # 3. CHURN RATE & RETENTION
    # ══════════════════════════════════════════════════════════

    def calculate_churn_rate(
        self,
        data_inizio: date,
        data_fine: date
    ) -> Dict:
        """
        Calcola Churn Rate (% di clienti persi) nel periodo

        Formula Standard:
        Churn Rate = (Clienti Persi / Clienti Inizio Periodo) * 100

        Industry Benchmark:
        - Eccellente: < 5% mensile
        - Buono: 5-7% mensile
        - Medio: 7-10% mensile
        - Alto: > 10% mensile

        Returns:
            {
                'churn_rate': float,           # % churn (0-100)
                'retention_rate': float,       # % retention (0-100)
                'customers_start': int,        # Clienti inizio periodo
                'customers_end': int,          # Clienti fine periodo
                'customers_lost': int,         # Clienti persi
                'customers_gained': int,       # Nuovi clienti
                'net_growth': int,             # Crescita netta
                'revenue_churn': float         # Revenue persa da churn
            }
        """
        with self._connect() as conn:
            # Clienti attivi all'inizio del periodo
            customers_start = conn.execute("""
                SELECT COUNT(*) as count
                FROM clienti
                WHERE stato = 'Attivo'
                  AND DATE(data_creazione) < ?
            """, (data_inizio,)).fetchone()['count']

            # Clienti attivi alla fine del periodo
            customers_end = conn.execute("""
                SELECT COUNT(*) as count
                FROM clienti
                WHERE stato = 'Attivo'
                  AND DATE(data_creazione) <= ?
            """, (data_fine,)).fetchone()['count']

            # Nuovi clienti nel periodo
            customers_gained = conn.execute("""
                SELECT COUNT(*) as count
                FROM clienti
                WHERE DATE(data_creazione) BETWEEN ? AND ?
            """, (data_inizio, data_fine)).fetchone()['count']

            # Clienti persi = (Inizio + Nuovi) - Fine
            customers_lost = (customers_start + customers_gained) - customers_end

            # Churn rate
            churn_rate = (
                (customers_lost / customers_start * 100)
                if customers_start > 0 else 0
            )

            # Retention rate (inverso del churn)
            retention_rate = 100 - churn_rate

            # Revenue churn (quanto fatturato abbiamo perso)
            # Clienti che erano attivi a inizio periodo ma non più a fine
            clienti_persi = conn.execute("""
                SELECT id, nome, cognome
                FROM clienti
                WHERE stato != 'Attivo'
                  AND DATE(data_creazione) < ?
            """, (data_inizio,)).fetchall()

            revenue_churn = 0.0
            for cliente in clienti_persi:
                ltv_data = self.calculate_customer_ltv(cliente['id'])
                if ltv_data:
                    revenue_churn += ltv_data['ltv_monthly']  # Revenue mensile persa

            return {
                'churn_rate': round(churn_rate, 2),
                'retention_rate': round(retention_rate, 2),
                'customers_start': customers_start,
                'customers_end': customers_end,
                'customers_lost': customers_lost,
                'customers_gained': customers_gained,
                'net_growth': customers_gained - customers_lost,
                'revenue_churn': round(revenue_churn, 2)
            }

    def predict_churn_risk(self, id_cliente: int) -> Dict:
        """
        Predice il rischio di churn per un cliente usando AI semplificata

        Fattori di rischio:
        1. Nessun acquisto recente (> 90 giorni)
        2. Bassa % utilizzo crediti
        3. Nessuna sessione recente
        4. Trend negativo nei pagamenti

        Returns:
            {
                'risk_score': float,      # 0-100 (100 = alto rischio)
                'risk_level': str,        # 'Basso', 'Medio', 'Alto', 'Critico'
                'factors': List[str],     # Fattori di rischio identificati
                'recommendations': List[str]  # Azioni suggerite
            }
        """
        ltv_data = self.calculate_customer_ltv(id_cliente)

        if not ltv_data or ltv_data['num_contracts'] == 0:
            return {
                'risk_score': 100.0,
                'risk_level': 'Critico',
                'factors': ['Nessun contratto attivo'],
                'recommendations': ['Contattare immediatamente il cliente']
            }

        risk_score = 0.0
        factors = []
        recommendations = []

        # Fattore 1: Ultimo acquisto
        if ltv_data['last_purchase']:
            last_purchase_date = datetime.strptime(
                ltv_data['last_purchase'], '%Y-%m-%d'
            ).date()
            days_since_purchase = (date.today() - last_purchase_date).days

            if days_since_purchase > 180:
                risk_score += 40
                factors.append(f'Nessun acquisto da {days_since_purchase} giorni')
                recommendations.append('Offrire promozione/rinnovo')
            elif days_since_purchase > 90:
                risk_score += 20
                factors.append(f'Ultimo acquisto {days_since_purchase} giorni fa')
                recommendations.append('Contattare per feedback')

        # Fattore 2: Utilizzo crediti
        if ltv_data['retention_rate'] < 30:
            risk_score += 30
            factors.append(f"Basso utilizzo crediti ({ltv_data['retention_rate']:.0f}%)")
            recommendations.append('Verificare soddisfazione servizio')
        elif ltv_data['retention_rate'] < 50:
            risk_score += 15
            factors.append(f"Utilizzo crediti medio-basso ({ltv_data['retention_rate']:.0f}%)")

        # Fattore 3: Status inattivo
        if ltv_data['status'] != 'Attivo':
            risk_score += 30
            factors.append('Cliente inattivo')
            recommendations.append('Piano di riattivazione urgente')

        # Determina livello rischio
        if risk_score >= 70:
            risk_level = 'Critico'
        elif risk_score >= 50:
            risk_level = 'Alto'
        elif risk_score >= 30:
            risk_level = 'Medio'
        else:
            risk_level = 'Basso'

        # Raccomandazioni generiche se non ce ne sono
        if not recommendations:
            recommendations.append('Continua il buon lavoro')

        return {
            'risk_score': round(min(risk_score, 100), 2),
            'risk_level': risk_level,
            'factors': factors if factors else ['Nessun fattore di rischio'],
            'recommendations': recommendations
        }

    # ══════════════════════════════════════════════════════════
    # 4. MONTHLY/ANNUAL RECURRING REVENUE (MRR/ARR)
    # ══════════════════════════════════════════════════════════

    def calculate_mrr_arr(self, as_of_date: date = None) -> Dict:
        """
        Calcola MRR (Monthly Recurring Revenue) e ARR

        Importante per SaaS/Subscription business

        Returns:
            {
                'mrr': float,              # Ricavi mensili ricorrenti
                'arr': float,              # Ricavi annuali ricorrenti (MRR * 12)
                'active_subscriptions': int,
                'avg_revenue_per_customer': float,
                'mrr_growth_rate': float   # % crescita MRR vs mese precedente
            }
        """
        if as_of_date is None:
            as_of_date = date.today()

        # Per ora calcoliamo MRR come media dei contratti attivi
        with self._connect() as conn:
            # Contratti attivi con scadenza futura
            contratti_attivi = conn.execute("""
                SELECT
                    id, id_cliente, prezzo_totale, totale_versato,
                    data_inizio, data_scadenza,
                    crediti_totali, crediti_usati
                FROM contratti
                WHERE stato_pagamento != 'PENDENTE'
                  AND DATE(data_scadenza) >= ?
                  AND chiuso = 0
            """, (as_of_date,)).fetchall()

            if not contratti_attivi:
                return {
                    'mrr': 0.0,
                    'arr': 0.0,
                    'active_subscriptions': 0,
                    'avg_revenue_per_customer': 0.0,
                    'mrr_growth_rate': 0.0
                }

            # Calcola MRR come: totale_versato / mesi di durata contratto
            mrr_total = 0.0
            for contratto in contratti_attivi:
                data_inizio = datetime.strptime(
                    contratto['data_inizio'], '%Y-%m-%d'
                ).date()
                data_scadenza = datetime.strptime(
                    contratto['data_scadenza'], '%Y-%m-%d'
                ).date()

                # Durata in mesi
                durata_mesi = (
                    (data_scadenza.year - data_inizio.year) * 12 +
                    (data_scadenza.month - data_inizio.month)
                )
                durata_mesi = max(1, durata_mesi)

                # MRR = versato / durata
                mrr_contratto = (
                    contratto['totale_versato'] / durata_mesi
                    if durata_mesi > 0 else 0
                )
                mrr_total += mrr_contratto

            active_subscriptions = len(contratti_attivi)
            avg_revenue_per_customer = (
                mrr_total / active_subscriptions
                if active_subscriptions > 0 else 0
            )

            # ARR = MRR * 12
            arr = mrr_total * 12

            # MRR Growth Rate (vs mese precedente)
            # TODO: Implementare calcolo storico
            mrr_growth_rate = 0.0  # Placeholder

            return {
                'mrr': round(mrr_total, 2),
                'arr': round(arr, 2),
                'active_subscriptions': active_subscriptions,
                'avg_revenue_per_customer': round(avg_revenue_per_customer, 2),
                'mrr_growth_rate': round(mrr_growth_rate, 2)
            }

    # ══════════════════════════════════════════════════════════
    # 5. COHORT ANALYSIS
    # ══════════════════════════════════════════════════════════

    def analyze_cohorts(
        self,
        cohort_by: str = 'month',  # 'month', 'quarter', 'year'
        start_date: date = None,
        end_date: date = None
    ) -> pd.DataFrame:
        """
        Analisi per coorti (gruppi di clienti acquisiti nello stesso periodo)

        Args:
            cohort_by: Raggruppamento ('month', 'quarter', 'year')
            start_date: Data inizio analisi
            end_date: Data fine analisi

        Returns:
            DataFrame con analisi per coorte:
            - cohort: Nome coorte (es. "2026-01")
            - num_customers: Clienti nella coorte
            - avg_ltv: LTV medio
            - retention_rate: % retention
            - total_revenue: Fatturato totale coorte
        """
        if start_date is None:
            start_date = date.today() - relativedelta(months=12)
        if end_date is None:
            end_date = date.today()

        with self._connect() as conn:
            clienti = conn.execute("""
                SELECT id, nome, cognome, data_creazione
                FROM clienti
                WHERE DATE(data_creazione) BETWEEN ? AND ?
                ORDER BY data_creazione
            """, (start_date, end_date)).fetchall()

            if not clienti:
                return pd.DataFrame()

            # Raggruppa per coorte
            cohorts = {}
            for cliente in clienti:
                created = datetime.strptime(
                    cliente['data_creazione'], '%Y-%m-%d %H:%M:%S'
                ).date()

                if cohort_by == 'month':
                    cohort_key = created.strftime('%Y-%m')
                elif cohort_by == 'quarter':
                    quarter = (created.month - 1) // 3 + 1
                    cohort_key = f"{created.year}-Q{quarter}"
                else:  # year
                    cohort_key = str(created.year)

                if cohort_key not in cohorts:
                    cohorts[cohort_key] = []
                cohorts[cohort_key].append(cliente['id'])

            # Calcola metriche per coorte
            cohort_data = []
            for cohort_name, cliente_ids in cohorts.items():
                ltv_sum = 0
                retention_sum = 0
                revenue_sum = 0

                for id_cliente in cliente_ids:
                    ltv_data = self.calculate_customer_ltv(id_cliente)
                    if ltv_data:
                        ltv_sum += ltv_data['ltv_total']
                        retention_sum += ltv_data['retention_rate']
                        revenue_sum += ltv_data['revenue_total']

                num_customers = len(cliente_ids)
                cohort_data.append({
                    'cohort': cohort_name,
                    'num_customers': num_customers,
                    'avg_ltv': round(ltv_sum / num_customers, 2) if num_customers > 0 else 0,
                    'avg_retention': round(retention_sum / num_customers, 2) if num_customers > 0 else 0,
                    'total_revenue': round(revenue_sum, 2)
                })

            return pd.DataFrame(cohort_data)
