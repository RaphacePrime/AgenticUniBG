# Iterazione 3 – Autenticazione JWT, Refactoring Architetturale e Analisi della Memoria Conversazionale

---

## 1. Obiettivo dell'Iterazione

L'obiettivo dell'Iterazione 3 è consolidare e raffinare l'architettura del server introdotta nell'Iterazione 2, completando le funzionalità rimaste in sospeso e analizzando in profondità la gestione della memoria conversazionale:

- **Implementazione del JWT stateless** con cookie httpOnly (rimandato dall'Iterazione 2)
- **Refactoring del server** in package separati (`auth/`, `models/`) seguendo i principi di separazione delle responsabilità
- **Progettazione della memoria conversazionale** del sistema attuale
- **Progettazione di architetture alternative** per la persistenza della memoria conversazionale (Redis e MongoDB)

---

## 2. User Stories Incluse

| ID | Descrizione | Ruolo |
|----|-------------|-------|
| US-06 | Come studente, voglio che la mia sessione venga mantenuta tramite un token sicuro nel browser, senza dover reinserire le credenziali ad ogni riavvio | Studente |
| US-07 | Come studente, voglio che il sistema ricordi le domande e le risposte precedenti durante la sessione, così le risposte tengano conto del contesto | Studente |
| US-08 | Come amministratore, voglio che la logica di autenticazione sia separata dal routing HTTP, così il codice sia più manutenibile e testabile | Sviluppatore |

---

## 3. Modifiche Incrementali rispetto all'Iterazione 2

### 3.1 JWT – da "rimandato" a implementato

Nell'Iterazione 2 il sistema restituiva direttamente i dati del profilo al login e il frontend li manteneva in memoria. Non era presente alcun token di sessione.

Nell'Iterazione 3 viene implementato il **JWT stateless** con le seguenti caratteristiche:

| Parametro | Valore |
|---|---|
| Algoritmo | `HS256` |
| Scadenza | 7 giorni  |
| Trasporto | Cookie `httpOnly` (`access_token`) |
| Verifica | `GET /api/auth/verify` al caricamento dell'app |
| Revoca | `POST /api/auth/logout` (cancella il cookie) |

Il token è firmato con una chiave segreta configurabile via variabile d'ambiente (`JWT_SECRET_KEY`). Il cookie httpOnly impedisce al JavaScript del browser di leggere il token, riducendo la superficie di attacco XSS.

### 3.2 Refactoring del server

**Struttura (Iterazione 3):**
```
server/
├── main.py          ← solo route e wiring delle dipendenze (191 righe)
├── db.py
├── config.py
├── models/
│   ├── __init__.py
│   └── user.py      ← tutti i modelli Pydantic
├── auth/
│   ├── __init__.py
│   ├── jwt_manager.py        ← JWTManager
│   ├── profile_repository.py ← ProfileRepository
│   ├── service.py            ← AuthService
│   └── controller.py         ← AuthController
└── agents/
```

### 3.3 Nuovi endpoint di autenticazione

| Metodo | Path | Descrizione | Novità |
|--------|------|-------------|--------|
| `POST` | `/api/auth/login` | Login → imposta cookie JWT httpOnly | Cookie JWT (nuovo) |
| `POST` | `/api/auth/register` | Registrazione → imposta cookie JWT httpOnly | Cookie JWT (nuovo) |
| `GET` | `/api/auth/verify` | Verifica il cookie JWT, restituisce profilo | Nuovo endpoint |
| `POST` | `/api/auth/logout` | Cancella il cookie JWT | Nuovo endpoint |
| `POST` | `/api/agent/query` | Query con protezione JWT (cookie) | Era non protetto |
| `GET` | `/api/agents` | Lista agenti | Invariato |
| `GET` | `/api/conversation/history` | Cronologia | Invariato |
| `DELETE` | `/api/conversation/history` | Cancella cronologia | Invariato |
| `POST` | `/api/agent/analyze` | Analisi query (debug) | Invariato |

---

## 4. Analisi Statica – Nuove Classi

### 4.1 `JWTManager` (`auth/jwt_manager.py`)

Responsabile della generazione e validazione dei token JWT. Centralizza tutta la logica crittografica.

| Attributo / Metodo | Tipo | Descrizione |
|---|---|---|
| `secret_key: str` | attributo | Chiave di firma (da env `JWT_SECRET_KEY`) |
| `algorithm: str` | attributo | `"HS256"` |
| `expire_minutes: int` | attributo | `60 * 24 * 7` (7 giorni) |
| `generateToken(data)` | metodo | Genera JWT con campo `exp` |
| `validateToken(token)` | metodo | Decodifica e valida, solleva `HTTPException(401)` se non valido |
| `validateFromRequest(request)` | metodo | Estrae il token dal cookie `access_token` e lo valida |

### 4.2 `ProfileRepository` (`auth/profile_repository.py`)

Astrae le operazioni CRUD su MongoDB per la collezione `users`, eliminando le query MongoDB inline da `main.py`.

| Metodo | Descrizione |
|---|---|
| `findById(matricola)` | Cerca utente per matricola (chiave primaria) |
| `findByEmail(email)` | Cerca utente per email |
| `save(user_doc)` | Inserisce nuovo documento utente |
| `exists(matricola)` | Verifica esistenza senza restituire il documento |

### 4.3 `AuthService` (`auth/service.py`)

Contiene la logica di business dell'autenticazione. Coordina `ProfileRepository` e `JWTManager`.

| Metodo | Descrizione |
|---|---|
| `authenticate(matricola, password)` | Verifica credenziali con `bcrypt`, genera JWT. Restituisce `{ "student": ..., "token": ... }` |
| `createUser(name, surname, matricola, password, ...)` | Hasha la password con `bcrypt`, salva via `ProfileRepository`, genera JWT |

### 4.4 `AuthController` (`auth/controller.py`)

Strato HTTP: riceve i dati dalla request, delega ad `AuthService`, imposta/elimina il cookie.

| Metodo | Descrizione |
|---|---|
| `login(matricola, password, response)` | Chiama `AuthService.authenticate`, imposta cookie JWT |
| `register(..., response)` | Chiama `AuthService.createUser`, imposta cookie JWT |
| `_set_auth_cookie(response, token)` | Imposta il cookie `access_token` httpOnly |
| `_public_profile(student)` | Filtra il documento MongoDB rimuovendo `passwordHash` prima di rispondere |

### 4.5 Modelli Pydantic (`models/user.py`)

Estratti da `main.py` e centralizzati in un modulo dedicato.

| Classe | Campi principali | Utilizzo |
|---|---|---|
| `User` | `name, surname, matricola, department, course, tipology, year, passwordHash` | Documento MongoDB |
| `LoginRequest` | `matricola, password` | Body `POST /api/auth/login` |
| `RegisterRequest` | `name, surname, matricola, password, department, course, tipology, year` | Body `POST /api/auth/register` |
| `QueryRequest` | `query, user_info?, context?` | Body `POST /api/agent/query` |
| `QueryResponse` | `response, agent_used?, metadata?` | Risposta agente |

> **Nota**: il campo `context: Optional[dict]` in `QueryRequest` è presente per estensibilità futura ma non è attualmente inviato dal frontend né utilizzato dagli agenti.

---

## 5. Analisi Dinamica

### 5.1 Flusso di Login aggiornato

```
1. Utente inserisce matricola e password nel frontend React
2. Frontend → POST /api/auth/login { matricola, password }
3. AuthController.login() → AuthService.authenticate()
4. AuthService: ProfileRepository.findById(matricola) da MongoDB
5. AuthService: bcrypt.checkpw(password, hash)
6. AuthService: JWTManager.generateToken({ matricola, ... })
7. AuthController._set_auth_cookie(response, token)   ← NUOVO
8. Risposta: Set-Cookie: access_token=<JWT>; HttpOnly; Max-Age=604800
9. Frontend → GET /api/auth/verify (con cookie automatico)
10. Backend: JWTManager.validateFromRequest(request) → profilo utente
11. Frontend salva profilo in stato React, abilita la chat
```

### 5.2 Flusso di Verifica Token (ricarica pagina)

All'avvio di `App.jsx`, prima di mostrare qualsiasi pagina:

```
1. Frontend → GET /api/auth/verify (cookie inviato automaticamente dal browser)
2. verify_token(request) → JWTManager.validateFromRequest()  
3. Se valido: ProfileRepository.findById(matricola) → restituisce profilo
4. Frontend: setUserInfo(userData), setIsAuthenticated(true)
5. Frontend carica conversazione da localStorage (se presente)
6. Se invalido/assente: mostra LoginPage
```

### 5.3 Flusso di Query (invariato nella logica, protetto da JWT)

```
1. Frontend → POST /api/agent/query { query, user_info, conversation_history }
   (cookie JWT inviato automaticamente)
2. Dipendenza FastAPI verify_token() → JWTManager.validateFromRequest()
3. OrchestratorAgent.process_query(query, user_info, conversation_history)
4. classify → generate → revise (LangGraph, invariato)
5. Risposta al frontend
```

---

## 6. Gestione della Memoria Conversazionale (Analisi)

Nell'Iterazione 3 viene analizzato e documentato il meccanismo di gestione della memoria conversazionale del sistema attuale, basato interamente sul **client (frontend)**.

### 6.1 Approccio attuale – Client-side (localStorage)

| Aspetto | Comportamento |
|---|---|
| **Storage** | `localStorage` del browser, chiave `conversation_{matricola}` |
| **Caricamento** | Al login/verifica token, la conversazione viene ripristinata |
| **Cancellazione** | Al logout, `localStorage.removeItem(key)` |
| **Payload inviato** | Ultimi 10 messaggi (5 scambi) via `.slice(-10)` |
| **AgentState** | Effimero, creato nuovo ad ogni query |
| **Persistenza server** | Nessuna — il server è completamente stateless |

### 6.2 Utilizzo della `conversation_history` negli agenti

| Agente | Porzione usata | Modalità |
|---|---|---|
| `ClassifierAgent` | `conversation_history[-4:]` (2 scambi) | Testo anteposto al prompt |
| `GeneratorAgent` | Tutti i 10 messaggi | Messaggi LLM nativi (`HumanMessage` / `AIMessage`) |
| `RevisionAgent` | `conversation_history[-4:]` (2 scambi) | Testo inserito nel prompt di revisione |

Il `GeneratorAgent` è l'unico a passare la history come messaggi LLM nativi, garantendo vera continuità conversazionale all'LLM.

Vedere il diagramma [sequence_memory.puml](sequence_memory.puml) per il flusso dettagliato.

---

## 7. Architetture Alternative – Proposte Progettuali

Nell'Iterazione 3 vengono progettate due architetture alternative per la persistenza della memoria conversazionale, da implementare nelle iterazioni successive. Entrambe spostano la responsabilità della history dal client al server.

### 7.1 Opzione A – Redis (cache + flush su MongoDB)

La conversazione attiva è mantenuta in un elenco Redis con TTL. Al logout viene persistita su MongoDB.

**Componente centrale**: `ConversationRepository` (Redis)

| Caratteristica | Dettaglio |
|---|---|
| Struttura Redis | `LIST chat:{matricola}` |
| Dimensione massima | 20 elementi (`LTRIM`) |
| TTL | 86400s (reset ad ogni messaggio) |
| Payload dal client | Solo `{ query, user_info }` — niente history |
| Persistenza permanente | Flush su MongoDB al logout |
| Conversazioni multiple | No — una sessione attiva per utente |

**Vantaggi**: latenza bassissima (Redis in-memory), zero modifiche agli agenti, payload client ridotto.  
**Svantaggi**: dati persi se TTL scade prima del logout, architettura più complessa (2 databse).

Diagrammi: [sequence_redis.puml](sequence_redis.puml) · [component_redis.puml](component_redis.puml) · [class_redis.puml](class_redis.puml)

### 7.2 Opzione B – MongoDB (persistenza diretta, multi-conversazione)

Ogni messaggio viene scritto direttamente su MongoDB. Il frontend gestisce un `conv_id` per identificare la conversazione attiva. Supporta una sidebar con la lista delle conversazioni precedenti.

**Componente centrale**: `ConversationRepository` (MongoDB)  
**Nuovo modello**: `Conversation { id, matricola, title, messages[], createdAt, updatedAt }`

| Caratteristica | Dettaglio |
|---|---|
| Struttura MongoDB | Collection `conversations`, documenti con array `messages` |
| Scrittura | Ad ogni messaggio (`updateOne $push`) |
| Payload dal client | `{ query, user_info, conv_id }` |
| Persistenza permanente | Sì — nessuna scadenza |
| Conversazioni multiple | Sì — gestite tramite `conv_id` |
| Nuovi endpoint | `GET/POST /api/conversations`, `GET /api/conversations/{conv_id}` |

**Vantaggi**: storico permanente, multi-conversazione, nessun rischio perdita dati.  
**Svantaggi**: latenza maggiore rispetto a Redis, ogni query richiede una lettura MongoDB.

Diagrammi: [sequence_mongodb.puml](sequence_mongodb.puml) · [component_mongodb.puml](component_mongodb.puml) · [class_mongodb.puml](class_mongodb.puml)

---

## 8. Diagrammi UML dell'Iterazione 3

| File | Tipo | Contenuto |
|---|---|---|
| [sequence_memory.puml](sequence_memory.puml) | Sequence | Flusso completo della memoria conversazionale nel sistema attuale |
| [sequence_redis.puml](sequence_redis.puml) | Sequence | Flusso con Redis: login → LRANGE/RPUSH/LTRIM → logout+flush MongoDB |
| [sequence_mongodb.puml](sequence_mongodb.puml) | Sequence | Flusso con MongoDB: carica conversazioni precedenti → query → updateOne |
| [component_redis.puml](component_redis.puml) | Componenti | Architettura con Redis come cache e MongoDB come archivio permanente |
| [component_mongodb.puml](component_mongodb.puml) | Componenti | Architettura con sola MongoDB e sidebar multi-conversazione |
| [class_redis.puml](class_redis.puml) | Classi | `ConversationRepository` Redis, modifiche a `OrchestratorAgent` e `QueryRequest` |
| [class_mongodb.puml](class_mongodb.puml) | Classi | `ConversationRepository`, `Conversation`, `Message`, `ConversationAPI` MongoDB |

---

## 9. Deployment – Docker (invariato)

La configurazione Docker Compose dell'Iterazione 2 rimane invariata. I nuovi package `models/` e `auth/` sono contenuti nella cartella `server/` usata come working directory dal container, quindi non richiedono modifiche al `Dockerfile`.

| Servizio | Immagine base | Porta esposta |
|---|---|---|
| `frontend` | node + nginx | 80 |
| `backend` | python:3.11-slim | 8000 |

---

## 10. Limitazioni dell'Iterazione 3

- **Memoria conversazionale ancora client-side**: la storia della conversazione è mantenuta nel `localStorage` del browser; se l'utente cambia dispositivo o cancella il browser, la history viene persa.
- **Singola conversazione attiva**: il sistema non supporta la gestione di più conversazioni parallele per lo stesso utente.
- **Nessun accesso a dati reali UniBG**: le risposte rimangono generate dall'LLM senza recupero da fonti strutturate.
- **Il campo `context` in `QueryRequest` è dead code**: è presente nel modello ma non viene mai inviato dal frontend né utilizzato concretamente dagli agenti.

---

## 11. Obiettivi Raggiunti

| Obiettivo | Iterazione | Stato |
|---|---|---|
| Registrazione studente con hashing password | 2 | ✅ Completato |
| Login con verifica credenziali | 2 | ✅ Completato |
| Personalizzazione risposta agenti tramite profilo | 2 | ✅ Completato |
| Pipeline classify → generate → revise (LangGraph) | 2 | ✅ Completato |
| Persistenza su MongoDB Atlas | 2 | ✅ Completato |
| Frontend React con login e chat | 2 | ✅ Completato |
| Containerizzazione Docker + Docker Compose | 2 | ✅ Completato |
| JWT stateless con cookie httpOnly | **3** | ✅ Completato |
| Refactoring server in `auth/` e `models/` | **3** | ✅ Completato |
| Separazione `JWTManager`, `AuthService`, `AuthController`, `ProfileRepository` | **3** | ✅ Completato |
| Analisi e documentazione memoria conversazionale | **3** | ✅ Completato |
| Progettazione architetture alternative (Redis / MongoDB) | **3** | ✅ Completato (design) |
| Persistenza server-side della memoria conversazionale | 4 | ⏳ Rimandato |
| Accesso a dati reali UniBG | 4 | ⏳ Rimandato |
| Supporto multi-conversazione | 4 | ⏳ Rimandato |
