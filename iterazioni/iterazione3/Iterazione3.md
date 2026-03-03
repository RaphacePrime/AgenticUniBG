# Iterazione 3 – JWT Authentication, Gestione Sessione e Memoria Conversazionale

---

## 1. Obiettivo dell'Iterazione

L'obiettivo dell'Iterazione 3 è consolidare e potenziare il sistema introdotto nell'Iterazione 2 con tre macro-funzionalità distinte:

- **JWT Authentication via httpOnly Cookie**: il token di sessione viene ora generato lato server e trasmesso esclusivamente tramite cookie httpOnly, eliminando la gestione manuale del token lato frontend e aumentando la sicurezza.
- **Gestione della Sessione Browser**: l'applicazione è in grado di ripristinare automaticamente la sessione utente al ricaricamento della pagina, verificando la validità del cookie JWT senza richiedere un nuovo login.
- **Memoria Conversazionale**: la cronologia delle conversazioni viene mantenuta nel `localStorage` del browser (persistenza tra sessioni) e trasmessa ad ogni query come `conversation_history`, consentendo agli agenti di generare risposte coerenti con il contesto dei messaggi precedenti.

---

## 2. User Stories Incluse

| ID | Descrizione | Ruolo |
|----|-------------|-------|
| US-06 | Come studente, voglio che il sistema ricordi la mia sessione dopo il ricaricamento della pagina, così non devo autenticarmi nuovamente | Studente |
| US-07 | Come utente, voglio che le risposte del sistema tengano conto delle domande precedenti della sessione corrente, così posso avere una conversazione fluida | Utente |
| US-08 | Come studente, voglio che le mie conversazioni precedenti siano ripristinate quando riapro l'applicazione | Studente |
| US-09 | Come utente, voglio poter fare logout in modo sicuro cancellando la sessione, così i miei dati restano protetti | Utente |

---

## 3. Architettura Implementata

### 3.1 Novità Rispetto all'Iterazione 2

| Funzionalità | Iterazione 2 | Iterazione 3 |
|---|---|---|
| JWT | Assente (token non implementato) | httpOnly Cookie con firma HMAC-SHA256 |
| Ripristino sessione | Assente | `GET /api/auth/verify` con cookie |
| Logout | Assente | `POST /api/auth/logout` + delete cookie |
| Memoria conversazionale | Assente | `localStorage` + `conversation_history` in ogni query |
| Auth Layer | Logica in `main.py` | Pacchetto `auth/` con 4 classi separate |
| CORS | `allow_origins=["*"]` | Origini ristrette a localhost |

### 3.2 Struttura a Tier Aggiornata

```
Client Tier         →   React App + localStorage (Conversation Store)
Backend Tier        →   FastAPI + Auth Layer (JWT Cookie) + Agent Layer
Data Tier           →   MongoDB Atlas (Motor async)
```

---

## 4. Pacchetto `auth/` – Refactoring del Layer di Autenticazione

Il codice di autenticazione, precedentemente concentrato in `main.py`, è stato estratto in un pacchetto dedicato con responsabilità ben separate.

### 4.1 `JWTManager`
Gestisce la generazione e la validazione dei token JWT:
- `generateToken(data: dict)` — codifica il payload (matricola + status) con scadenza configurabile (default 7 giorni), firma HMAC-SHA256
- `validateToken(token: str)` — decodifica e verifica la firma; solleva `HTTPException 401` se il token è invalido o scaduto
- `validateFromRequest(request: Request)` — estrae il JWT dall'httpOnly cookie `access_token` della request e lo valida; usato come dipendenza FastAPI (`Depends`)

### 4.2 `AuthService`
Contiene la logica applicativa:
- `authenticate(matricola, password)` — verifica le credenziali via `bcrypt.checkpw`, genera JWT e restituisce `{student, token}`
- `createUser(...)` — verifica unicità matricola, hasha la password, inserisce in MongoDB, genera JWT

### 4.3 `AuthController`
Fa da ponte tra i route handler FastAPI e `AuthService`:
- `login(...)` / `register(...)` — delega ad `AuthService` e poi chiama `_set_auth_cookie` per depositare il JWT nel cookie httpOnly
- `_set_auth_cookie(response, token)` — imposta il cookie con attributi `httponly=True`, `samesite="lax"`, `max_age` dal config; `secure=True` in produzione
- `_public_profile(student)` — filtra il documento restituendo solo i campi pubblici (omette `passwordHash`)

### 4.4 `ProfileRepository`
Incapsula le operazioni MongoDB sulla collection `users`:
- `findById(matricola)` — ricerca per chiave applicativa primaria
- `findByEmail(email)` — ricerca alternativa per email
- `save(user_doc)` — inserisce e restituisce il documento senza `_id`
- `exists(matricola)` — verifica unicità prima della registrazione

---

## 5. Gestione della Sessione Browser

### 5.1 Ripristino Automatico della Sessione

Al caricamento dell'applicazione React, viene effettuata una chiamata `GET /api/auth/verify` con `credentials: "include"`. Il backend:
1. Estrae il JWT dall'httpOnly cookie tramite `JWTManager.validateFromRequest`
2. Decodifica il payload e recupera la matricola
3. Interroga `ProfileRepository.findById` su MongoDB
4. Restituisce il profilo completo al frontend

Se il cookie è assente, scaduto o invalido, il frontend mostra la pagina di login senza esporre dettagli dell'errore.

### 5.2 Logout Sicuro

`POST /api/auth/logout` chiama `response.delete_cookie("access_token")`, rendendo il JWT non più trasmesso nelle request successive. Lato frontend, il logout:
- Cancella il profilo dallo stato React
- Cancella la conversazione dal `localStorage`
- Reimposta `isAuthenticated = false`

---

## 6. Memoria Conversazionale

### 6.1 Persistenza in `localStorage`

La cronologia viene salvata nel `localStorage` del browser con chiave `conversation_{matricola}`:
- **Salvataggio**: ad ogni aggiornamento del conversation state (React `useEffect`)
- **Ripristino**: dopo il verify token con successo, il frontend carica la conversazione salvata
- **Cancellazione**: al logout o su richiesta esplicita dell'utente

### 6.2 Trasmissione agli Agenti

Ad ogni query, il frontend costruisce un array `conversation_history` con gli ultimi **10 messaggi** (5 turni domanda/risposta):

```javascript
const conversationHistory = conversation
  .filter(msg => msg.type === "user" || msg.type === "agent")
  .slice(-10)
  .map(msg => ({
    role: msg.type === "user" ? "user" : "assistant",
    content: msg.content,
  }));
```

L'array viene inviato nel body di `POST /api/agent/query` insieme a `query` e `user_info`.

### 6.3 Utilizzo da Parte degli Agenti

`AgentState` ora include il campo `conversation_history: Optional[List[Dict]]`. L'`OrchestratorAgent` lo popola dallo stato iniziale e lo passa a:
- **GeneratorAgent**: inietta la history nel prompt per generare risposte coerenti con la conversazione in corso
- **RevisionAgent**: considera la history nella revisione per evitare contraddizioni con risposte precedenti

---

## 7. Analisi Dinamica

### 7.1 Flusso di Ripristino Sessione
1. Il browser carica l'app React e invia automaticamente `GET /api/auth/verify` con il cookie.
2. FastAPI usa `Depends(verify_token)` per validare il JWT.
3. `ProfileRepository.findById` recupera il profilo da MongoDB.
4. Il frontend imposta `userInfo` e `isAuthenticated`, poi carica la conversazione da `localStorage`.

### 7.2 Flusso di Query con Contesto Conversazionale
1. L'utente digita una domanda; il frontend estrae gli ultimi 10 messaggi come history.
2. `POST /api/agent/query` invia query + user_info + conversation_history (cookie allegato automaticamente).
3. L'orchestratore inizializza `AgentState` con tutti i campi inclusa la history.
4. **Classify** → **Generate** (con history) → **Revise** (con history).
5. La risposta viene restituita, aggiunta alla UI e salvata in `localStorage`.

### 7.3 Flusso di Logout
1. L'utente clicca logout; il frontend invia `POST /api/auth/logout`.
2. Il backend cancella il cookie `access_token`.
3. Il frontend pulisce `localStorage`, resetta lo stato e reindirizza al login.

---

## 8. Analisi Statica – Aggiornamenti alle Classi

### 8.1 `AgentState` (aggiornato)
Aggiunto il campo:
- `conversation_history: Optional[List[Dict]]` — lista di `{role: "user"|"assistant", content: String}` trasmessa dal frontend

### 8.2 `OrchestratorAgent.process_query()` (aggiornato)
La firma passa da:
```python
process_query(query, context, user_info)
```
a:
```python
process_query(query, context, user_info, conversation_history)
```
e popola `initial_state["conversation_history"]`.

### 8.3 Dipendenze FastAPI
`verify_token` è registrata come dipendenza (`Depends`) utilizzata sull'endpoint `/api/auth/verify`. Usa `JWTManager.validateFromRequest` per estrarre e validare il cookie.

---

## 9. Endpoint API – Aggiornamenti

| Metodo | Path | Novità | Descrizione |
|--------|------|--------|-------------|
| `POST` | `/api/auth/login` | Imposta httpOnly cookie | Login — ora restituisce JWT in cookie |
| `POST` | `/api/auth/register` | Imposta httpOnly cookie | Registrazione — ora restituisce JWT in cookie |
| `GET` | `/api/auth/verify` | **Nuovo** | Verifica cookie e ripristina profilo |
| `POST` | `/api/auth/logout` | **Nuovo** | Cancella il cookie JWT |
| `POST` | `/api/agent/query` | Aggiornato | Accetta `conversation_history` nel body |

---

## 10. Sicurezza

| Aspetto | Iterazione 2 | Iterazione 3 |
|---|---|---|
| Token JWT | Non implementato | httpOnly cookie (inaccessibile da JS) |
| CORS | `allow_origins=["*"]` | Origini esplicite (localhost dev) |
| Password | bcrypt | bcrypt (invariato) |
| Scadenza token | — | 7 giorni (configurabile) |
| SameSite | — | `lax` (protezione CSRF base) |

---

## 11. Limitazioni dell'Iterazione 3

- **`secure=False`**: il cookie non è marcato `Secure` perché il deploy locale non usa HTTPS; da abilitare in produzione.
- **Conversazione solo lato client**: la history è memorizzata in `localStorage` e non è persistita su MongoDB; cambiando browser o dispositivo la cronologia è persa.
- **Nessun refresh token**: il JWT ha scadenza fissa a 7 giorni senza meccanismo di rinnovo; alla scadenza l'utente deve riautenticarsi.
- **Nessun accesso a dati reali UniBG**: le risposte restano generate dall'LLM senza recupero da fonti strutturate (web, documenti).

---

## 12. Obiettivi Raggiunti

| Obiettivo | Stato |
|---|---|
| JWT generato e inviato via httpOnly cookie | ✅ Completato |
| Ripristino automatico sessione (`/api/auth/verify`) | ✅ Completato |
| Logout con cancellazione cookie | ✅ Completato |
| Memoria conversazionale in localStorage | ✅ Completato |
| Conversazione persistente tra ricaricamenti | ✅ Completato |
| Trasmissione `conversation_history` agli agenti | ✅ Completato |
| Refactoring Auth Layer in pacchetto dedicato | ✅ Completato |
| Restrizione CORS per origini autorizzate | ✅ Completato |
| Refresh token | ⏳ Rimandato |
| Persistenza conversazione su MongoDB | ⏳ Rimandato |
| Accesso a dati reali UniBG | ⏳ Rimandato (Iterazione 4) |
