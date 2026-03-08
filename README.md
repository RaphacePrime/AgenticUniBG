<p align="center">
  <img src="agentic_unibg/app/src/img/unibg_logo.png" alt="UniBG Logo" width="120"/>
</p>

<h1 align="center">Agentic UniBG</h1>

<p align="center">
  <strong>Sistema multi-agente intelligente per l'Università degli Studi di Bergamo</strong>
</p>

---

## Indice

- [Panoramica](#panoramica)
- [Architettura del Sistema](#architettura-del-sistema)
- [Struttura del Progetto](#struttura-del-progetto)
- [Prerequisiti](#prerequisiti)
- [Ottenere le API Key](#ottenere-le-api-key)
- [Installazione e Avvio](#installazione-e-avvio)
  - [Avvio con Docker (consigliato)](#avvio-con-docker-consigliato)
  - [Avvio in locale (sviluppo)](#avvio-in-locale-sviluppo)
- [Configurazione Variabili d'Ambiente](#configurazione-variabili-dambiente)
- [Utilizzo dell'Applicazione](#utilizzo-dellapplicazione)
- [API Endpoints](#api-endpoints)
- [Pipeline degli Agenti](#pipeline-degli-agenti)
- [Tecnologie Utilizzate](#tecnologie-utilizzate)
- [Logging e Debug](#logging-e-debug)

---

## Panoramica

**Agentic UniBG** è un sistema multi-agente che sfrutta foundation models (Google Gemini) per rispondere in modo intelligente e autonomo alle richieste degli studenti e degli ospiti dell'Università degli Studi di Bergamo.

A differenza di un semplice chatbot, il sistema è composto da **5 agenti specializzati** coordinati da un **orchestratore** tramite un grafo di esecuzione (LangGraph). Ogni query dell'utente attraversa una pipeline completa:

1. **Classificazione** della richiesta in categorie semantiche
2. **Ottimizzazione** della query per la ricerca web
3. **Ricerca web** su domini ufficiali dell'ateneo (con supporto per estrazione dati da PDF)
4. **Generazione** di una risposta contestualizzata e personalizzata
5. **Revisione** automatica per garantire qualità, accuratezza e formato

Il sistema supporta sia utenti autenticati (con personalizzazione basata su corso, dipartimento e anno) sia ospiti.

---

## Architettura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│                    http://localhost:3000                         │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐             │
│  │ LoginPage│  │   Chat App   │  │ SettingsPage  │             │
│  └──────────┘  └──────┬───────┘  └───────────────┘             │
│                       │ /api/*                                  │
└───────────────────────┼─────────────────────────────────────────┘
                        │ (Vite proxy / Nginx reverse proxy)
┌───────────────────────┼─────────────────────────────────────────┐
│                 BACKEND (FastAPI)                                │
│               http://localhost:8000                              │
│                       │                                         │
│  ┌────────────────────▼────────────────────┐                    │
│  │         OrchestratorAgent               │                    │
│  │           (LangGraph Workflow)          │                    │
│  │                                         │                    │
│  │  ┌───────────┐    ┌──────────────┐      │                    │
│  │  │ Classifier├───►│ QueryAgent   │      │                    │
│  │  └───────────┘    └──────┬───────┘      │                    │
│  │                          │              │                    │
│  │              ┌───────────┴──────────┐   │                    │
│  │              ▼                      ▼   │                    │
│  │     ┌──────────────┐    ┌───────────┐   │                    │
│  │     │  WebAgent    │    │ExamExtract│   │                    │
│  │     │  (Tavily)    │    │(PDF+Tavily)│  │                    │
│  │     └──────┬───────┘    └─────┬─────┘   │                    │
│  │            └────────┬─────────┘         │                    │
│  │                     ▼                   │                    │
│  │            ┌─────────────────┐          │                    │
│  │            │ GeneratorAgent  │          │                    │
│  │            └────────┬────────┘          │                    │
│  │                     ▼                   │                    │
│  │            ┌─────────────────┐          │                    │
│  │            │ RevisionAgent   │          │                    │
│  │            └─────────────────┘          │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                 │
│  ┌──────────────┐  ┌────────────┐  ┌────────────────┐           │
│  │ Auth (JWT)   │  │  MongoDB   │  │ PipelineLogger │           │
│  │ httpOnly     │  │  (Atlas)   │  │  (file logs)   │           │
│  └──────────────┘  └────────────┘  └────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Struttura del Progetto

```
AgenticUniBG/
├── docker-compose.yml              # Orchestrazione container
├── .env                            # Variabili d'ambiente (da creare)
├── README.md
│
├── agentic_unibg/
│   ├── app/                        # Frontend React + Vite
│   │   ├── Dockerfile              # Container Node.js (dev)
│   │   ├── nginx.conf              # Config Nginx (production)
│   │   ├── package.json
│   │   ├── vite.config.js          # Proxy API verso il backend
│   │   ├── index.html
│   │   └── src/
│   │       ├── main.jsx            # Entry point React
│   │       ├── App.jsx             # Chat principale + logica conversazione
│   │       ├── App.css
│   │       ├── LoginPage.jsx       # Login, registrazione, accesso ospite
│   │       ├── LoginPage.css
│   │       ├── SettingsPage.jsx    # Modifica profilo e password
│   │       ├── SettingsPage.css
│   │       └── img/                # Asset grafici (logo UniBG)
│   │
│   └── server/                     # Backend FastAPI + LangChain
│       ├── Dockerfile              # Container Python 3.11
│       ├── main.py                 # Entry point FastAPI, routing, CORS
│       ├── config.py               # Configurazione (Pydantic Settings)
│       ├── db.py                   # Connessione MongoDB (motor async)
│       ├── requirements.txt        # Dipendenze Python
│       │
│       ├── agents/                 # Sistema multi-agente
│       │   ├── agent_state.py      # Stato condiviso (TypedDict)
│       │   ├── orchestrator_agent.py  # Grafo LangGraph + orchestrazione
│       │   ├── classifier_agent.py    # Classificazione query (7 categorie)
│       │   ├── query_agent.py         # Ottimizzazione query di ricerca
│       │   ├── web_agent.py           # Ricerca web Tavily + estrazione PDF
│       │   ├── generator_agent.py     # Generazione risposta contestualizzata
│       │   └── revision_agent.py      # Revisione qualità e formato
│       │
│       ├── auth/                   # Autenticazione
│       │   ├── jwt_manager.py      # Generazione/validazione JWT
│       │   ├── service.py          # Logica di business auth
│       │   ├── controller.py       # Controller HTTP auth
│       │   └── profile_repository.py  # Repository MongoDB utenti
│       │
│       ├── models/                 # Schemi Pydantic
│       │   └── user.py             # User, LoginRequest, QueryRequest, ecc.
│       │
│       ├── logger/                 # Sistema di logging
│       │   └── pipeline_logger.py  # Log dettagliato per ogni query
│       │
│       └── logs/                   # File di log generati (auto-creata)
│
├── documentazione/                 # Documentazione di progetto
│   ├── relazione_finale.tex        # Relazione LaTeX
│   ├── analisi_statica.md
│   ├── analisi_dinamica.md
│   └── design_iterazione*.md       # Design per ogni iterazione
│
├── iterazioni/                     # Documentazione iterativa (Agile)
│   ├── iterazione0/ ... iterazione5/
│
└── test/                           # Test e valutazione
    └── expert_judgment_evaluation/ # Valutazione con expert judgment
```

---

## Prerequisiti

Prima di avviare il progetto, assicurati di avere installato:

| Requisito          | Versione minima | Note                                                                      |
| ------------------ | --------------- | ------------------------------------------------------------------------- |
| **Docker**         | 20.10+          | [Scarica Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Docker Compose** | v2.0+           | Incluso in Docker Desktop                                                 |
| **Git**            | 2.30+           | Per clonare il repository                                                 |

> **Solo per sviluppo locale (senza Docker):**
>
> | Requisito   | Versione | Note                                          |
> | ----------- | -------- | --------------------------------------------- |
> | **Python**  | 3.11+    | [Download](https://www.python.org/downloads/) |
> | **Node.js** | 20+      | [Download](https://nodejs.org/)               |
> | **npm**     | 9+       | Incluso con Node.js                           |

### API Key necessarie

Il sistema richiede **2 API key** gratuite:

| Servizio               | Utilizzo                              | Costo                         |
| ---------------------- | ------------------------------------- | ----------------------------- |
| **Google AI (Gemini)** | Foundation model per tutti gli agenti | Gratuito (piano free)         |
| **Tavily**             | Ricerca web avanzata su domini UniBG  | Gratuito (1000 ricerche/mese) |

---

## Ottenere le API Key

### 1. Google AI API Key (Gemini)

1. Vai su [Google AI Studio](https://aistudio.google.com/apikey)
2. Accedi con il tuo account Google
3. Clicca su **"Create API Key"**
4. Copia la chiave generata (formato: `AIza...`)

### 2. Tavily API Key

1. Vai su [Tavily](https://tavily.com/)
2. Crea un account gratuito
3. Dalla dashboard, copia la tua API key (formato: `tvly-...`)

---

## Installazione e Avvio

### Avvio con Docker (consigliato)

Questo è il metodo più semplice e garantisce un ambiente identico per tutti.

**1. Clona il repository:**

```bash
git clone https://github.com/tuo-username/AgenticUniBG.git
cd AgenticUniBG
```

**2. Crea il file `.env` nella root del progetto:**

```bash
# Su Linux/macOS
touch .env

# Su Windows (PowerShell)
New-Item .env -ItemType File
```

**3. Inserisci le API key nel file `.env`:**

```env
GOOGLE_API_KEY=AIzaSy...la-tua-chiave-google
TAVILY_API_KEY=tvly-...la-tua-chiave-tavily
```

**4. Avvia i container:**

```bash
docker-compose up --build
```

> Al primo avvio, Docker scaricherà le immagini base e installerà le dipendenze. Le esecuzioni successive saranno più rapide grazie alla cache.

**5. Accedi all'applicazione:**

| Servizio                         | URL                        |
| -------------------------------- | -------------------------- |
| **Frontend** (interfaccia chat)  | http://localhost:3000      |
| **Backend API**                  | http://localhost:8000      |
| **Documentazione API** (Swagger) | http://localhost:8000/docs |

**6. Per fermare l'applicazione:**

```bash
docker-compose down
```

---

### Avvio in locale (sviluppo)

Per lo sviluppo attivo con hot-reload su entrambi frontend e backend.

#### Backend (FastAPI)

```bash
# 1. Entra nella cartella del server
cd agentic_unibg/server

# 2. Crea un ambiente virtuale Python
python -m venv venv

# 3. Attiva l'ambiente virtuale
# Su Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Su Windows (CMD):
venv\Scripts\activate.bat
# Su Linux/macOS:
source venv/bin/activate

# 4. Installa le dipendenze
pip install -r requirements.txt

# 5. Crea il file .env nella cartella server (oppure imposta le variabili di sistema)
# Contenuto .env:
# GOOGLE_API_KEY=AIzaSy...
# TAVILY_API_KEY=tvly-...

# 6. Avvia il server con hot-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend (React + Vite)

```bash
# In un nuovo terminale:

# 1. Entra nella cartella dell'app
cd agentic_unibg/app

# 2. Installa le dipendenze
npm install

# 3. Avvia il dev server con hot-reload
npm run dev
```

> **Nota:** Il frontend in sviluppo è configurato con un proxy Vite che inoltra tutte le chiamate `/api/*` al backend su `http://server:8000`. Se esegui il backend in locale (non in Docker), modifica `vite.config.js` cambiando il target del proxy in `http://localhost:8000`.

---

## Utilizzo dell'Applicazione

### Primo accesso

1. Apri il browser all'indirizzo **http://localhost:3000**
2. Dalla pagina di login puoi:
   - **Registrarti** come studente (con matricola, dipartimento, corso di laurea, anno)
   - **Accedere come ospite** senza registrazione

### Chat con il sistema

Una volta autenticato, accedi alla chat dove puoi porre domande su:

| Categoria              | Esempi                                                                |
| ---------------------- | --------------------------------------------------------------------- |
| **Informazioni corso** | "Chi è il docente di Analisi I?", "Quali materie ho al secondo anno?" |
| **Orari**              | DA IMPLEMENTARE                                                       |
| **Date esami**         | "Quando è l'esame di Analisi?", "Esami della sessione estiva 2026"    |
| **Procedure**          | "Come mi iscrivo all'esame?", "Come pago le tasse universitarie?"     |
| **Servizi**            | "Dove si trova la mensa?", "Orari biblioteca di Dalmine"              |
| **Generale**           | "Informazioni sull'Erasmus", "Come raggiungo l'università?"           |

### Funzionalità principali

- **Risposte personalizzate**: se autenticato, il sistema adatta le risposte al tuo corso, dipartimento e anno
- **Memoria conversazionale**: il sistema mantiene il contesto delle conversazioni recenti per gestire follow-up
- **Estrazione date esami**: per domande sulle date degli esami, il sistema estrae automaticamente i dati dai calendari PDF ufficiali
- **Fonti verificabili**: ogni risposta include link alle pagine ufficiali consultate
- **Modifica profilo**: dalla pagina Impostazioni puoi aggiornare i tuoi dati o cambiare password

---

## Pipeline degli Agenti

Ogni query dell'utente attraversa questa pipeline sequenziale gestita da **LangGraph**:

### 1. ClassifierAgent

Classifica la query in una delle 7 categorie:
`informazioni_corso` | `orari` | `date_esami` | `procedure` | `servizi` | `generale` | `altro`

### 2. QueryAgent

Trasforma la domanda in una query di ricerca ottimizzata per il web (max 8 keyword). Tiene conto del contesto conversazionale e, quando pertinente, del profilo studente.

### 3. WebAgent (branching condizionale)

- **Percorso standard** (`web_search`): ricerca web con Tavily su domini `unibg.it` e `unibg.coursecatalogue.cineca.it`, recupera i top 5 risultati per rilevanza e ne estrae il contenuto (inclusi link da PDF)
- **Percorso date esami** (`exam_extract`): seleziona tramite LLM il calendario PDF corretto per dipartimento/sessione, estrae il contenuto via Tavily Extract, e integra con risultati di ricerca aggiuntivi

### 4. GeneratorAgent

Genera una risposta contestualizzata basandosi su:

- Il prompt specializzato per la categoria
- Le informazioni estratte dal web
- Il contesto conversazionale completo
- Il profilo dello studente (se autenticato)

### 5. RevisionAgent

Revisiona la risposta per garantire:

- Accuratezza (nessun dato inventato)
- Struttura chiara (elenchi puntati, formattazione pulita)
- Concisione (rimozione di ripetizioni e formule di cortesia superflue)
- Preservazione di URL, date e dati fattuali

---

## Tecnologie Utilizzate

### Frontend

| Tecnologia | Versione | Ruolo                      |
| ---------- | -------- | -------------------------- |
| React      | 18.2     | Libreria UI                |
| Vite       | 5.x      | Build tool e dev server    |
| Axios      | 1.6      | HTTP client                |
| Nginx      | latest   | Reverse proxy (production) |

### Backend

| Tecnologia    | Versione  | Ruolo                       |
| ------------- | --------- | --------------------------- |
| FastAPI       | 0.109+    | Web framework asincrono     |
| LangChain     | 0.1+      | Framework per LLM           |
| LangGraph     | 0.0.20+   | Grafo di esecuzione agenti  |
| Google Gemini | 2.5 Flash | Foundation model (LLM)      |
| Tavily        | 0.5+      | Ricerca web avanzata (API)  |
| PyMuPDF       | 1.24+     | Estrazione link da PDF      |
| Motor         | 3.3+      | Driver asincrono MongoDB    |
| python-jose   | 3.3+      | Gestione token JWT          |
| bcrypt        | 4.1+      | Hashing password            |
| Pydantic      | 2.5+      | Validazione dati e settings |

### Infrastruttura

| Tecnologia              | Ruolo                               |
| ----------------------- | ----------------------------------- |
| Docker + Docker Compose | Containerizzazione e orchestrazione |
| MongoDB Atlas           | Database cloud (gestione utenti)    |
| Tavily API              | Motore di ricerca web per LLM       |

---

## Logging e Debug

Ogni query elaborata dal sistema produce un file di log dettagliato nella cartella `agentic_unibg/server/logs/`.

Il nome del file segue il formato: `log_{matricola}_{timestamp}.txt`

Ogni log contiene:

- Informazioni utente (matricola, corso, dipartimento)
- Query originale e storico conversazione
- Dettaglio di ogni step della pipeline (prompt, risposta LLM, tempo di esecuzione)
- Risultati della ricerca web
- Risposta generata e risposta revisionata
- Eventuali errori

I log sono utili per:

- Debugging delle risposte generate
- Analisi delle performance di ogni agente
- Monitoraggio dell'utilizzo del sistema

> Per la documentazione interattiva dell'API, accedi a http://localhost:8000/docs dopo aver avviato il backend.

---
