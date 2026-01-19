# 🎯 Guida: Financial Intelligence Dashboard

**Data**: 19 Gennaio 2026
**Versione**: 1.0
**Livello**: Advanced Analytics per PT Professionisti

---

## 📊 Cosa Abbiamo Implementato

Hai ora accesso alle **stesse metriche professionali** che usano i leader mondiali come **Trainerize, TrueCoach e MarketLabs** per gestire business fitness di successo.

### Nuove Metriche Disponibili

| Metrica | Cosa Significa | Perché È Importante |
|---------|----------------|---------------------|
| **LTV** (Lifetime Value) | Quanto vale un cliente nel tempo | Sapere quanto investire in acquisizione |
| **CAC** (Customer Acquisition Cost) | Costo per acquisire un nuovo cliente | Capire se il marketing è sostenibile |
| **LTV/CAC Ratio** | Rapporto tra valore cliente e costo acquisizione | Target: 3.0+ per business sano |
| **Churn Rate** | % di clienti che abbandonano | Target: <5% mensile per retention ottimale |
| **MRR/ARR** | Ricavi mensili/annuali ricorrenti | Fondamentale per previsioni e crescita |
| **Churn Prediction** | AI che prevede quali clienti abbandoneranno | Intervento proattivo prima della perdita |
| **Cohort Analysis** | Analisi per gruppi di clienti | Capire quali periodi funzionano meglio |

---

## 🚀 Come Usare la Dashboard

### 1. Accedi alla Nuova Pagina

Nella sidebar di FitManager, clicca su:
```
📄 09_Financial_Intelligence
```

### 2. Configura il Periodo di Analisi

**Nella sidebar sinistra:**

- **Periodo**: Scegli "Ultimi 30 giorni", "Ultimi 90 giorni", "Anno corrente", ecc.
- **Costi Marketing**: Inserisci quanto hai speso in pubblicità (Facebook Ads, Google, flyer, ecc.)
- **Costi Sales**: Se hai venditori o commissioni, inseriscili qui

**Esempio:**
```
Periodo: Ultimi 90 giorni
Costi Marketing: €500 (speso in Facebook Ads)
Costi Sales: €0
```

### 3. Leggi le Metriche Principali (Dashboard)

In alto vedrai 4 KPI chiave:

#### 💎 LTV Medio/Cliente
- **Cosa mostra**: Quanto vale in media ogni tuo cliente
- **Come interpretare**:
  - €1000-2000: Buono per PT freelance
  - €2000-5000: Ottimo, cliente fidelizzato
  - €5000+: Eccellente, clienti premium

#### 🎯 CAC (Costo Acquisizione)
- **Cosa mostra**: Quanto spendi per acquisire un nuovo cliente
- **Come interpretare**:
  - €50-150: Ottimo (marketing efficiente)
  - €150-300: Medio (ottimizzabile)
  - €300+: Alto (rivedi strategia marketing)

#### 📈 LTV/CAC Ratio
- **Cosa mostra**: Quante volte il valore del cliente supera il costo di acquisizione
- **Come interpretare**:
  - **3.0+**: ✅ Eccellente - Business sostenibile
  - **2.0-3.0**: ⚠️ Buono ma migliorabile
  - **<2.0**: 🔴 Attenzione - Non sostenibile

**Esempio:**
- LTV = €2000
- CAC = €200
- Ratio = 10x → Ogni €1 speso genera €10 di valore! 🎉

#### ⚠️ Churn Rate
- **Cosa mostra**: % di clienti che abbandonano
- **Come interpretare**:
  - **<5%**: ✅ Eccellente retention
  - **5-7%**: 🟡 Buono, monitorare
  - **7-10%**: ⚠️ Medio, azioni necessarie
  - **>10%**: 🔴 Critico, intervento urgente

---

## 📑 I 5 Tab Principali

### Tab 1: 💎 LTV Analysis

**Cosa trovi:**
- LTV totale del tuo portfolio
- Top 20 clienti per valore
- Tabella dettagliata di tutti i clienti con:
  - LTV totale e mensile
  - Numero contratti
  - Mesi di attività
  - % Retention (utilizzo crediti)
  - Predizione LTV prossimi 12 mesi

**Come usarlo:**
1. Identifica i tuoi "best customers" (top LTV)
2. Studia cosa hanno in comune
3. Replica la strategia con nuovi clienti
4. Fai upselling ai clienti a basso LTV

**Azione Immediata:**
- Scarica il CSV "Report LTV"
- Contatta i top 10 clienti per un "thank you" o referral program

---

### Tab 2: 🎯 CAC & Acquisition

**Cosa trovi:**
- CAC medio per nuovo cliente
- Numero nuovi clienti acquisiti
- Breakdown costi (Marketing, Sales, Altro)
- Payback Period (mesi per recuperare il CAC)

**Come interpretare il Payback Period:**
- **< 6 mesi**: Eccellente! Puoi scalare il marketing
- **6-12 mesi**: Nella norma, monitorare
- **> 12 mesi**: Troppo lungo, rivedi strategia

**Azione Immediata:**
Se il tuo CAC è > €300:
1. Identifica i canali marketing più costosi
2. Concentrati su quelli con ROI migliore
3. Considera referral program (CAC quasi zero!)

---

### Tab 3: ⚠️ Churn & Retention

**Cosa trovi:**
- Churn Rate e Retention Rate
- Benchmark vs industry standard
- **Churn Risk Prediction AI** - LA FEATURE KILLER! 🔥

**Churn Risk Prediction - Come Funziona:**

L'AI analizza ogni cliente e assegna un **Risk Score** (0-100):

- **Critico (70-100)**: Cliente sta per abbandonare
- **Alto (50-70)**: Rischio elevato
- **Medio (30-50)**: Da monitorare
- **Basso (0-30)**: Cliente felice

**Fattori analizzati dall'AI:**
1. Nessun acquisto recente (>90 giorni)
2. Bassa % utilizzo crediti (<30%)
3. Nessuna sessione recente
4. Trend negativo nei pagamenti

**Azione Immediata:**
1. Filtra per "Critico" e "Alto"
2. Leggi i "Fattori di rischio"
3. Segui le "Azioni consigliate"
4. Contatta OGGI i clienti a rischio critico

**Esempio:**
```
Cliente: Mario Rossi
Risk Score: 85/100 (Critico)
Fattori:
  - Nessun acquisto da 120 giorni
  - Utilizzo crediti: 15%
Azioni:
  - Offrire promozione/rinnovo
  - Verificare soddisfazione servizio
```

---

### Tab 4: 💰 MRR/ARR Tracking

**Cosa trovi:**
- MRR (Monthly Recurring Revenue): Ricavi mensili ricorrenti
- ARR (Annual Recurring Revenue): MRR × 12
- ARPU (Average Revenue Per User): Revenue medio per cliente
- Proiezioni a 6 e 12 mesi

**Perché è importante:**
- MRR/ARR sono le metriche che usano le startup SaaS per valutazioni
- Se vuoi crescere/vendere il business, questi numeri contano

**Come migliorare MRR:**
1. **Upselling**: Vendi pacchetti più grandi
2. **Cross-selling**: Aggiungi nutrizione, fisioterapia, ecc.
3. **Aumenta prezzi**: Se fornisci valore, puoi aumentare
4. **Riduci churn**: Mantieni i clienti esistenti

---

### Tab 5: 👥 Cohort Analysis

**Cosa trovi:**
- Analisi clienti raggruppati per periodo di acquisizione
- LTV medio per coorte
- Retention rate per coorte
- Identifica quale periodo ha generato i migliori clienti

**Come usarlo:**

**Esempio:**
```
Coorte 2025-10 (Ottobre 2025):
- LTV Medio: €2500
- Retention: 85%
- Clienti: 12

Coorte 2025-12 (Dicembre 2025):
- LTV Medio: €800
- Retention: 45%
- Clienti: 8
```

**Domande da farti:**
- Cosa ho fatto a Ottobre che ha funzionato?
- Cosa è andato storto a Dicembre?
- C'era una promo? Un nuovo servizio?

**Azione Immediata:**
- Replica le strategie della coorte migliore
- Evita gli errori della coorte peggiore

---

## 🎯 Scenari d'Uso Pratici

### Scenario 1: "Devo investire più in Marketing?"

**Step:**
1. Vai a **Tab 2: CAC & Acquisition**
2. Controlla LTV/CAC Ratio
3. Se **Ratio >= 3.0**: ✅ SÌ, puoi investire di più
4. Se **Ratio < 2.0**: ❌ NO, prima ottimizza retention/churn

---

### Scenario 2: "Perché perdo clienti?"

**Step:**
1. Vai a **Tab 3: Churn & Retention**
2. Filtra "Critico" e "Alto" rischio
3. Leggi i **Fattori di rischio** più comuni
4. Implementa azioni correttive:
   - Se "Basso utilizzo crediti": Chiama e chiedi feedback
   - Se "Nessun acquisto recente": Offri promozione rinnovo
   - Se "Cliente inattivo": Piano riattivazione urgente

---

### Scenario 3: "Quanto posso guadagnare quest'anno?"

**Step:**
1. Vai a **Tab 4: MRR/ARR**
2. Leggi **ARR** (Annual Recurring Revenue)
3. Questa è la tua proiezione se mantieni tutti i clienti attuali
4. Calcola crescita:
   - ARR attuale: €50.000
   - Se acquisisci 10 nuovi clienti/mese (LTV €2000): +€240.000
   - Potenziale totale: €290.000/anno

---

### Scenario 4: "Quali clienti devo coccolare?"

**Step:**
1. Vai a **Tab 1: LTV Analysis**
2. Scarica il CSV
3. Ordina per "LTV Totale" (decrescente)
4. Top 20% = i tuoi VIP
5. Azioni:
   - Regalo di ringraziamento
   - Referral bonus (portami un amico = sconto)
   - Early access a nuovi servizi

---

## 📈 KPI Target Raccomandati

| Metrica | Target PT Freelance | Target Studio (5-50 PT) |
|---------|---------------------|-------------------------|
| **LTV/CAC Ratio** | 3.0+ | 4.0+ |
| **Churn Rate** | <7% mensile | <5% mensile |
| **CAC** | <€200 | <€150 |
| **LTV Medio** | €1500+ | €2500+ |
| **Payback Period** | <8 mesi | <6 mesi |
| **MRR Growth** | +5% mese su mese | +10% mese su mese |

---

## 🚨 Alert: Quando Preoccuparsi

### 🔴 CRITICO - Azione Immediata

1. **LTV/CAC < 1.5**: Stai perdendo soldi su ogni cliente
2. **Churn > 15%**: Stai perdendo clienti troppo velocemente
3. **CAC > €500**: Costi acquisizione troppo alti
4. **Payback > 18 mesi**: Non recupererai mai l'investimento

**Cosa fare:**
- STOP a nuova acquisizione marketing
- Focus 100% su retention
- Rivedi pricing e valore offerto
- Considera consulenza business coach

### 🟡 ATTENZIONE - Monitora

1. **LTV/CAC tra 2.0-2.5**: Margini stretti
2. **Churn 7-10%**: Sopra media industria
3. **MRR Growth < 3%**: Crescita lenta

**Cosa fare:**
- Implementa churn prediction
- Upselling ai clienti esistenti
- Referral program per abbassare CAC

---

## 💡 Best Practices

### 1. Monitora Settimanalmente
- Ogni lunedì mattina: Check churn prediction
- Ogni fine mese: Analisi completa LTV/CAC/MRR

### 2. Agisci sui Dati
- Non basta guardare i numeri
- Implementa azioni concrete:
  - Clienti a rischio → Chiama entro 24h
  - CAC alto → Testa nuovo canale marketing
  - LTV basso → Aggiungi upselling

### 3. Documenta i Cambiamenti
- Quando cambi strategia, annotalo
- Dopo 30 giorni, confronta metriche pre/post
- Mantieni cosa funziona, elimina cosa non funziona

### 4. Usa i CSV
- Scarica i report regolarmente
- Confronta mese su mese
- Crea grafici Excel per presentazioni

---

## 🎓 Termini Chiave - Glossario

| Termine | Significato |
|---------|-------------|
| **LTV** | Lifetime Value - Valore totale cliente nel tempo |
| **CAC** | Customer Acquisition Cost - Costo acquisizione |
| **Churn** | Tasso abbandono clienti (%) |
| **Retention** | Tasso mantenimento clienti (%) = 100 - Churn |
| **MRR** | Monthly Recurring Revenue - Ricavi mensili ricorrenti |
| **ARR** | Annual Recurring Revenue - Ricavi annuali ricorrenti |
| **ARPU** | Average Revenue Per User - Revenue medio per utente |
| **Cohort** | Gruppo di clienti acquisiti nello stesso periodo |
| **Payback Period** | Tempo per recuperare il CAC |

---

## 🆘 FAQ

### Q: I miei numeri LTV/CAC sono bassi, è normale all'inizio?
**A:** Sì! Nei primi 6 mesi il CAC è alto (pochi clienti da dividere per costi fissi marketing) e LTV ancora basso (clienti appena acquisiti). Dopo 12 mesi vedrai numeri realistici.

### Q: Come abbasso il CAC?
**A:**
1. Referral program (clienti portano amici)
2. Content marketing (Instagram, TikTok organico)
3. Partnership con palestre/nutrizionisti
4. Eliminare canali a basso ROI

### Q: Come aumento il LTV?
**A:**
1. Upselling (pacchetti più grandi)
2. Cross-selling (aggiungi nutrizione, fisioterapia)
3. Aumenta retention (riduci churn)
4. Aumenta prezzi (se fornisci valore)

### Q: Quanti clienti servono per dati affidabili?
**A:** Minimo 20 clienti attivi. Con meno di 10, le metriche saranno volatili.

---

## 🎉 Conclusione

Ora hai gli stessi strumenti analytics dei big player mondiali!

**Prossimi Passi:**
1. Esplora tutti i 5 tab
2. Scarica i CSV report
3. Identifica 3 azioni immediate (es: contatta clienti a rischio)
4. Monitora settimanalmente
5. Confronta dopo 30 giorni

**Ricorda:**
> "You can't improve what you don't measure" - Peter Drucker

Hai domande? Consulta questa guida o esplora la dashboard! 🚀

---

**Aggiornato**: 19 Gennaio 2026
**Versione FitManager**: 3.0 - Financial Intelligence Edition
