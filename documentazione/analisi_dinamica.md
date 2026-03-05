# Analisi Dinamica — Test API con Postman

## 1. Introduzione

L'analisi dinamica del sistema AgenticUniBG è stata condotta attraverso test API eseguiti con **Postman**. I test verificano il corretto funzionamento di tutti gli endpoint REST esposti dal backend FastAPI, organizzati per iterazione di sviluppo.

La collezione Postman completa è disponibile nel file `postman_collection.json` nella stessa cartella di questo documento.

---

## 2. Setup

### Prerequisiti
- Backend in esecuzione (`docker-compose up` o `uvicorn main:app`)
- MongoDB raggiungibile
- Variabili d'ambiente configurate (`.env`)

### Variabili Postman
| Variabile | Valore Default | Descrizione |
|---|---|---|
| `base_url` | `http://localhost:8000` | URL del backend |
| `test_matricola` | `9999999` | Matricola usata per i test |
| `test_password` | `TestPassword123!` | Password usata per i test |

---

## 3. Casi di Test per Iterazione

### 3.1 Iterazione 1 — Inviare Domanda e Ricevere Risposta

| ID | Endpoint | Metodo | Descrizione | Risultato Atteso |
|---|---|---|---|---|
| IT1-01 | `/api/health` | GET | Health check del backend | 200, `status: "healthy"` |
| IT1-02 | `/` | GET | Root endpoint informativo | 200, `message: "Agentic UniBG API"` |
| IT1-03 | `/api/agent/query` | POST | Query generica come ospite | 200, risposta non vuota, `agent_used: "orchestrator"` |
| IT1-04 | `/api/agent/query` | POST | Query su docente di un corso | 200, categoria `informazioni_corso` o `generale` |
| IT1-05 | `/api/agent/query` | POST | Query vuota | 200/422/500 (gestione errore) |
| IT1-06 | `/api/agents` | GET | Lista agenti disponibili | 200, array con `classifier`, `generator`, `reviser` |

**Asserzioni chiave:**
- La risposta della pipeline contiene sempre `response` (stringa non vuota), `agent_used` e `metadata.workflow_steps`
- I workflow_steps registrano ogni passo della pipeline con il nome dell'agente

---

### 3.2 Iterazione 2 — Registrazione, Login, Personalizzazione

| ID | Endpoint | Metodo | Descrizione | Risultato Atteso |
|---|---|---|---|---|
| IT2-01 | `/api/auth/register` | POST | Registrazione nuovo studente | 200, profilo con `status: "loggato"`, cookie `access_token` |
| IT2-02 | `/api/auth/register` | POST | Matricola duplicata | 409, `"già registrata"` |
| IT2-03 | `/api/auth/login` | POST | Login credenziali corrette | 200, `status: "loggato"`, cookie JWT |
| IT2-04 | `/api/auth/login` | POST | Matricola inesistente | 401, `"non trovata"` |
| IT2-05 | `/api/auth/login` | POST | Password errata | 401, `"Password errata"` |
| IT2-06 | `/api/auth/verify` | GET | Verifica token valido | 200, profilo utente completo |
| IT2-07 | `/api/auth/verify` | GET | Senza cookie | 401 |
| IT2-08 | `/api/auth/profile` | PUT | Aggiornamento profilo | 200, dati aggiornati |
| IT2-09 | `/api/auth/password` | PUT | Cambio password valido | 200, `status: "success"` |
| IT2-10 | `/api/auth/password` | PUT | Password corrente errata | 401, `"corrente errata"` |
| IT2-11 | `/api/agent/query` | POST | Query personalizzata | 200, risposta con contesto utente |
| IT2-12 | `/api/auth/logout` | POST | Logout | 200, cookie eliminato |

**Asserzioni chiave:**
- Il cookie `access_token` è impostato con flag `httponly`
- Il login e la registrazione restituiscono lo stesso formato di profilo pubblico (senza `passwordHash`)
- Le risposte personalizzate utilizzano le informazioni del profilo utente

---

### 3.3 Iterazione 3 — Memoria Conversazionale

| ID | Endpoint | Metodo | Descrizione | Risultato Atteso |
|---|---|---|---|---|
| IT3-01 | `/api/agent/query` | POST | Prima domanda senza storico | 200, risposta sul tema |
| IT3-02 | `/api/agent/query` | POST | Follow-up con contesto | 200, risposta che usa il contesto |
| IT3-03 | `/api/agent/query` | POST | Cambio argomento | 200, risposta sul nuovo tema |
| IT3-04 | `/api/conversation/history` | GET | Recupero cronologia | 200, array |
| IT3-05 | `/api/conversation/history` | DELETE | Cancellazione cronologia | 200, `status: "success"` |

**Asserzioni chiave:**
- Il sistema disambigua correttamente domande di follow-up ("E quelli di informatica?") utilizzando il `conversation_history`
- Un cambio di argomento viene gestito correttamente senza confusione col contesto precedente

---

### 3.4 Iterazione 4 — Query Agent, Web Agent, Logger

| ID | Endpoint | Metodo | Descrizione | Risultato Atteso |
|---|---|---|---|---|
| IT4-01 | `/api/agent/query` | POST | Query con web search | 200, pipeline completa (5 step) con timing |
| IT4-02 | `/api/agent/query` | POST | Query date esami | 200, categoria `date_esami`, step `exam_extract` |
| IT4-03 | `/api/agent/query` | POST | Verifica ottimizzazione query | 200, `search_query` più corta dell'originale |
| IT4-04 | `/api/agent/analyze` | POST | Analisi debug | 200, `predicted_category` + piano workflow |
| IT4-05 | `/api/agent/query` | POST | Follow-up date esami | 200, risposta contestuale |

**Asserzioni chiave:**
- La pipeline completa contiene 5 step: `classification`, `query_generation`, `web_search` (o `exam_extract`), `generation`, `revision`
- Ogni step ha `elapsed_time` (numero) per il monitoraggio delle performance
- Il QueryAgent produce query ottimizzate (< 100 char) a partire da domande verbose
- Il branching condizionale `date_esami → exam_extract` vs `altro → web_search` funziona correttamente

---

## 4. Riepilogo dei Test

| Iterazione | N. Test | Endpoint Testati | Copertura |
|---|---|---|---|
| IT1 | 6 | 4 | Pipeline base, health check, lista agenti |
| IT2 | 12 | 7 | Auth completa (register, login, verify, profile, password, logout) |
| IT3 | 5 | 2 | Memoria conversazionale, follow-up, cronologia |
| IT4 | 5 | 2 | Pipeline completa, exam extract, debug |
| **Totale** | **28** | **10** | **Tutti gli endpoint REST** |

---

## 5. Come Eseguire i Test

### Importazione in Postman
1. Aprire Postman
2. File → Import → Selezionare `postman_collection.json`
3. La collezione "AgenticUniBG - Test API" apparirà nella sidebar

### Esecuzione sequenziale
1. Avviare il backend
2. Eseguire la cartella "Iterazione 1" con il Collection Runner
3. Proseguire con le iterazioni successive in ordine
4. **Nota**: IT2-01 (Registrazione) va eseguito prima di IT2-03 (Login)

### Esecuzione con Newman (CLI)
```bash
npm install -g newman
newman run postman_collection.json --env-var "base_url=http://localhost:8000"
```
