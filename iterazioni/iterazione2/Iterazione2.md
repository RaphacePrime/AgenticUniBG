# Iterazione 2 – Autenticazione, Profilazione Utente e Sistema Multi-Agent Completo

---

## 1. Obiettivo dell'Iterazione

L'obiettivo dell'Iterazione 2 è evolvere il sistema dal prototipo funzionale dell'Iterazione 1 verso un'applicazione completa e deployabile, introducendo:

- **Autenticazione utente** (registrazione e login con matricola/password)
- **Profilazione personalizzata** dello studente (corso, dipartimento, anno, tipologia)
- **Personalizzazione delle risposte** degli agenti in base al profilo utente
- **Frontend React** con interfaccia di login e chat
- **Persistenza su MongoDB** tramite Motor (driver asincrono)
- **Containerizzazione completa** con Docker e Docker Compose

---

## 2. User Stories Incluse

| ID | Descrizione | Ruolo |
|----|-------------|-------|
| US-01 | Come studente, voglio registrarmi con matricola e password, così da accedere al sistema con il mio profilo | Studente |
| US-02 | Come studente, voglio autenticarmi e ricevere in risposta i dati del mio profilo, così il sistema può personalizzare le risposte | Studente |
| US-03 | Come ospite, voglio inviare domande senza autenticazione, così da ottenere risposte generiche | Ospite |
| US-04 | Come studente autenticato, voglio ricevere risposte personalizzate in base al mio corso e anno, così ottengo informazioni rilevanti per me | Studente |
| US-05 | Come utente, voglio inviare una richiesta testuale e ricevere una risposta elaborata dal sistema ad agenti | Utente |

---

## 3. Architettura Implementata

### 3.1 Struttura a Tier

L'architettura è articolata in tre tier distinti:

```
Client Tier         →   React App (Vite + Nginx)
Backend Tier        →   FastAPI + Agenti (LangChain / LangGraph)
Data Tier           →   MongoDB Atlas (Motor async)
```

### 3.2 Componenti Sviluppati

| Componente | Tecnologia | Responsabilità |
|---|---|---|
| `Web / Mobile App` | React + Vite | Interfaccia login e chat |
| `API Gateway` (FastAPI) | Python / uvicorn | Routing HTTP, CORS, endpoint REST |
| `Auth Controller` | FastAPI routes | Gestione `/api/auth/login` e `/api/auth/register` |
| `Auth Service` | bcrypt | Hashing e verifica password |
| `OrchestratorAgent` | LangGraph | Coordinamento pipeline classify → generate → revise |
| `ClassifierAgent` | LangChain + Groq | Classificazione intento della query |
| `GeneratorAgent` | LangChain + Groq | Generazione risposta contestualizzata |
| `RevisionAgent` | LangChain + Groq | Revisione e raffinamento risposta |
| `ProfileRepository` | Motor / MongoDB | Persistenza e recupero profilo studente |
| `MongoDB` | MongoDB Atlas | Storage documenti utente |

---

## 4. Analisi Statica – Classi Principali

### 4.1 `AgentState` (TypedDict)
Stato condiviso tra tutti i nodi del workflow LangGraph. Contiene:

- **Input**: `query`, `context`
- **Profilo utente**: `user_status`, `user_name`, `user_surname`, `user_course`, `user_department`, `user_tipology`, `user_year`, `user_matricola`
- **Output classificazione**: `category`, `category_description`, `confidence`
- **Output generazione**: `generated_response`, `generation_status`
- **Output revisione**: `final_response`, `has_revisions`
- **Tracking**: `workflow_steps`, `current_step`, `status`, `error`

### 4.2 `OrchestratorAgent`
- Costruisce il grafo LangGraph con tre nodi: `classify → generate → revise`
- Il LLM utilizzato è **llama-3.3-70b-versatile** via **Groq API**
- Espone `process_query(query, context, user_info)` richiamato dall'endpoint `/api/agent/query`
- Mantiene la `conversation_history` in memoria

### 4.3 `build_user_context(state)`
Funzione helper che, dati i campi del profilo nello `AgentState`, costruisce una stringa di contesto da iniettare nei prompt degli agenti. Se l'utente è autenticato, include nome, corso, anno, dipartimento. Se è ospite, inserisce un disclaimer di risposta generica.

### 4.4 Modelli Pydantic (Request/Response)
- `LoginRequest`: `matricola`, `password`
- `RegisterRequest`: `name`, `surname`, `matricola`, `password`, `department`, `course`, `tipology`, `year`
- `QueryRequest`: `query`, `context?`, `user_info?`
- `QueryResponse`: `response`, `agent_used?`, `metadata?`

---

## 5. Analisi Dinamica

### 5.1 Flusso di Login
1. L'utente inserisce matricola e password nel frontend React.
2. Il frontend invia `POST /api/auth/login`.
3. FastAPI cerca lo studente in MongoDB per matricola.
4. `bcrypt.checkpw` verifica la password contro l'hash memorizzato.
5. In caso di successo, vengono restituiti tutti i dati del profilo studente.
6. Il frontend salva il profilo in memoria e abilita la chat.

### 5.2 Flusso di Registrazione
1. L'utente compila il form di registrazione.
2. Il frontend invia `POST /api/auth/register`.
3. FastAPI verifica che la matricola non sia già presente.
4. La password viene hashata con `bcrypt.hashpw` e il documento viene inserito in MongoDB.
5. Viene restituito il profilo appena creato.

### 5.3 Flusso di Query Personalizzata
1. Il frontend invia `POST /api/agent/query` con `query` e `user_info` (profilo dal login).
2. L'`OrchestratorAgent` inizializza l'`AgentState` con query e profilo.
3. `build_user_context` genera una stringa di contesto dal profilo.
4. **Classify**: il `ClassifierAgent` riceve query + contesto utente e restituisce `category` e `confidence`.
5. **Generate**: il `GeneratorAgent` riceve query, categoria e contesto profilo; genera una risposta personalizzata.
6. **Revise**: il `RevisionAgent` riceve la bozza e la raffina.
7. La `final_response` viene restituita al frontend.

---

## 6. Persistenza – MongoDB

Il modulo `db.py` utilizza **Motor** (driver asincrono) per connettersi a **MongoDB Atlas**:

```python
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client["agentic_unibg"]
students_collection = db["users"]
```

Il documento utente salvato ha la seguente struttura:

```json
{
  "name": "Mario",
  "surname": "Rossi",
  "matricola": "123456",
  "passwordHash": "<bcrypt hash>",
  "department": "Ingegneria",
  "course": "Informatica",
  "tipology": "Triennale",
  "year": 2
}
```

---

## 7. Personalizzazione della Risposta

Il meccanismo di personalizzazione si basa sull'iniezione del profilo nel prompt degli agenti attraverso `build_user_context`. Esempio di contesto iniettato per utente autenticato:

```
INFORMAZIONI STUDENTE (autenticato):
- Nome: Mario
- Cognome: Rossi
- Matricola: 123456
- Dipartimento: Ingegneria
- Corso di laurea: Informatica
- Tipologia: Triennale
- Anno di frequentazione: 2
```

Per gli ospiti, il contesto indica esplicitamente l'assenza di profilo, guidando il modello a fornire risposte generiche.

---

## 8. Frontend

Il frontend è una Single Page Application React (Vite) servita tramite Nginx. Comprende:

- **`LoginPage.jsx`**: form di login/registrazione con chiamate REST verso il backend
- **`App.jsx`**: interfaccia chat principale, attiva solo dopo autenticazione, invia query con `user_info` allegato

---

## 9. Deployment – Docker

Il sistema è containerizzato con Docker Compose:

| Servizio | Immagine base | Porta esposta |
|---|---|---|
| `frontend` | node + nginx | 80 |
| `backend` | python:3.11-slim | 8000 |

Il backend utilizza `uvicorn` con `motor` per la connessione asincrona a MongoDB Atlas (esterno ai container).

---

## 10. Endpoint API

| Metodo | Path | Descrizione |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/auth/login` | Login con matricola e password |
| `POST` | `/api/auth/register` | Registrazione nuovo studente |
| `POST` | `/api/agent/query` | Elaborazione query con pipeline agenti |
| `GET` | `/api/agents` | Lista agenti disponibili |
| `GET` | `/api/conversation/history` | Cronologia conversazioni |
| `DELETE` | `/api/conversation/history` | Cancella cronologia |
| `POST` | `/api/agent/analyze` | Analisi query senza esecuzione (debug) |

---

## 11. Limitazioni dell'Iterazione 2

- **Nessun accesso a dati reali UniBG**: le risposte sono generate dall'LLM senza recupero da fonti strutturate (orari, corsi, documenti ufficiali).
- **Conversation history in memoria**: la cronologia delle conversazioni non è persistita su MongoDB ma mantenuta nell'istanza dell'`OrchestratorAgent`.

---

## 12. Diagrammi UML

Tutti i diagrammi sono in formato PlantUML (`.puml`).

| Diagramma | File | Descrizione |
|---|---|---|
| Use Case | `usecase_diagram2.puml` | Casi d'uso: registrazione, login, query, risposta personalizzata |
| Activity | `activity_diagram2.puml` | Flusso attività della pipeline classify → generate → revise |
| Sequence | `sequence_diagram2.puml` | Processo di login: Frontend → Gateway → Auth → MongoDB |
| Class | `class_diagram2.puml` | Diagramma classi completo (Auth Layer + Agent Layer + modelli) |
| Component (Overview) | `component_diagram2.puml` | Architettura a 3 tier con porte e interfacce cross-tier |
| Component (Auth Layer) | `component2_auth.puml` | Dettaglio Authentication Layer: AuthCtrl → AuthSvc |
| Component (Agent Layer) | `component2_agents.puml` | Dettaglio Agent Layer: Orchestrator → Classifier, Generator, Revision |

---

## 13. Obiettivi Raggiunti

| Obiettivo | Stato |
|---|---|
| Registrazione studente con hashing password | ✅ Completato |
| Login con verifica credenziali e restituzione profilo | ✅ Completato |
| Personalizzazione risposta agenti tramite profilo | ✅ Completato |
| Pipeline classify → generate → revise con LangGraph | ✅ Completato |
| Persistenza su MongoDB Atlas | ✅ Completato |
| Frontend React con login e chat | ✅ Completato |
| Containerizzazione Docker + Docker Compose | ✅ Completato |
| Accesso a dati reali UniBG | ⏳ Rimandato |
| Persistenza cronologia conversazioni | ⏳ Rimandato |
