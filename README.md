# AgenticUniBG

Agentic UniBG è un sistema ad agenti che sfruttano foundation models per la capacità di ragionare e prendere decisioni autonomamente.
In particolare questo sistema si occcupa di accogliere le richieste da parte di studenti dell'università oppure da ospiti.
L'obiettivo è quello di rispondere alle richieste fornendo informazioni, guide passo passo, documenti, orari ecc. in modo facile e veloce.

Agentic Unibg non è un semplice chatbot ma un sistema di agenti intelligenti che coordinati da un orchestratore possono lavorare in modo autonomo per completare le task richieste e successivamente generare una risposta coerente per l'utente.

## Struttura del Progetto

```
AgenticUniBG/
├── agentic_unibg/
│   ├── app/                    # Frontend React
│   │   ├── src/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   ├── package.json
│   │   └── vite.config.js
│   └── server/                 # Backend FastAPI + LangChain
│       ├── agents/
│       │   ├── __init__.py
│       │   └── agent_manager.py
│       ├── main.py
│       ├── config.py
│       ├── requirements.txt
│       └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Prerequisiti

- Docker e Docker Compose
- Groq API Key (gratuita su https://groq.com)

## Setup

1. **Clona il repository e configura le variabili d'ambiente:**

```bash
cp .env.example .env
```

Modifica il file `.env` e inserisci la tua Groq API key:
```
GROQ_API_KEY=gsk_...
```

2. **Avvia i container Docker:**

```bash
docker-compose up --build
```

3. **Accedi all'applicazione:**

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Documentazione API: http://localhost:8000/docs

## Sviluppo Locale

### Frontend (React)

```bash
cd agentic_unibg/app
npm install
npm run dev
```

### Backend (FastAPI)

```bash
cd agentic_unibg/server
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## API Endpoints

- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `POST /api/agent/query` - Invia una query al sistema ad agenti
- `GET /api/agents` - Lista degli agenti disponibili

## Tecnologie Utilizzate

### Frontend
- React 18
- Vite
- Axios
- Nginx (production)

### Backend
- FastAPI
- LangChain
- Groq (Llama 3.3 70B)
- Python 3.11

### Infrastructure
- Docker
- Docker Compose

## Note per lo Sviluppo

- Il frontend usa Vite per il development server con hot reload
- Il backend usa uvicorn con --reload per il development
- In produzione, il frontend viene servito da Nginx
- CORS è configurato per permettere richieste dal frontend

## Prossimi Passi

1. Implementare agenti specifici per diversi task
2. Aggiungere persistenza dei dati (database)
3. Implementare autenticazione e autorizzazione
4. Aggiungere testing (unit e integration tests)
5. Configurare CI/CD
