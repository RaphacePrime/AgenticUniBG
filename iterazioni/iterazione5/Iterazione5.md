# Iterazione 5 – Timestamp Temporale, Routing `date_exam` con Extract, Pagina Impostazioni Profilo, Prompt Engineering e Tempi nel Logger

---

## 1. Obiettivo dell'Iterazione

L'obiettivo dell'Iterazione 5 è raffinare e consolidare la pipeline multi-agente introdotta nelle iterazioni precedenti, con interventi trasversali su qualità delle risposte, consapevolezza temporale, gestione del profilo utente e miglioramento del logging. Le macro-funzionalità introdotte sono:

- **Timestamp Temporale per gli Agenti**: tutti gli agenti ricevono la data corrente in formato italiano (es. "06 marzo 2026") iniettata automaticamente nei prompt di sistema, consentendo risposte temporalmente consapevoli (anno accademico, prossima sessione, scadenze).
- **Routing `date_exam` con Extract**: il `ClassifierAgent` classifica la nuova categoria `date_exam` (già `date_esami` nell'Iterazione 4, ora consolidata). Il flusso LangGraph attiva un edge dedicato verso il nodo `exam_extract`, dove il `WebAgent` utilizza la sua funzione `.extract()` per recuperare il contenuto integrale dei calendari esami. I link dei calendari per i vari poli/dipartimenti sono fissi e codificati in `EXAM_CALENDAR_LINKS`; l'agente seleziona autonomamente tramite LLM quale calendario estrarre in base alla domanda e al profilo utente.
- **Pagina Impostazioni Profilo Utente**: nuovo componente React `SettingsPage` che permette agli utenti autenticati di modificare i propri dati personali (nome, cognome, dipartimento, corso, anno) e di cambiare la password. I dati sono organizzati tramite il dizionario `DIPARTIMENTI_CORSI` che mappa ogni dipartimento ai rispettivi corsi di laurea con tipologia derivata automaticamente. Due nuovi endpoint REST (`PUT /api/auth/profile` e `PUT /api/auth/password`) gestiscono le operazioni di aggiornamento.
- **Prompt Engineering Estensivo**: revisione sistematica di tutti i prompt di sistema di ogni agente (ClassifierAgent, QueryAgent, GeneratorAgent, RevisionAgent) con test manuali iterativi e correzioni mirate. Include regole critiche per la gestione del contesto conversazionale, istruzioni dettagliate per l'uso delle fonti web, format di risposta in testo semplice (no Markdown) e regole di concisione intelligente.
- **Tempi di Esecuzione nel Logger**: il `PipelineLogger` registra ora il tempo di esecuzione di ogni singolo agente e il tempo totale della pipeline, con una sezione dedicata "TEMPI DI ESECUZIONE" nel file di log.

---

## 2. User Stories Incluse

| ID | Descrizione | Ruolo |
|----|-------------|-------|
| US-15 | Come studente, voglio che il sistema conosca la data odierna così da ricevere risposte temporalmente accurate (es. "prossima sessione", "scadenza iscrizione") | Studente |
| US-16 | Come studente, voglio poter modificare i miei dati personali (nome, cognome, dipartimento, corso, anno) dalla pagina impostazioni senza dovermi re-iscrivere | Studente |
| US-17 | Come studente, voglio poter cambiare la mia password dall'interfaccia web in modo sicuro | Studente |
| US-18 | Come studente, voglio risposte più precise e meglio strutturate grazie a prompt ottimizzati che gestiscano correttamente il contesto della conversazione | Studente |
| US-19 | Come sviluppatore, voglio monitorare i tempi di esecuzione di ogni agente nei log per identificare colli di bottiglia nella pipeline | Sistema |

---

## 3. Architettura Implementata

### 3.1 Novità Rispetto all'Iterazione 4

| Funzionalità | Iterazione 4 | Iterazione 5 |
|---|---|---|
| Consapevolezza temporale | Assente nei prompt | `get_italian_timestamp()` in QueryAgent, GeneratorAgent; data iniettata in system prompt |
| Gestione profilo utente | Assente (solo registrazione) | SettingsPage con modifica profilo e cambio password |
| Endpoint profilo | Assenti | `PUT /api/auth/profile`, `PUT /api/auth/password` |
| Prompt ClassifierAgent | Esempi base | Prompt esteso con contesto conversazionale (ultimi 2 turni) |
| Prompt QueryAgent | Prompt generico | Prompt con regola critica contesto > profilo, esempi follow-up, gestione date/sessioni |
| Prompt GeneratorAgent | Prompt per categoria | Aggiunta `SOURCE_INSTRUCTIONS` per uso fonti web, prompt specializzato `date_esami`, history come messaggi LLM nativi |
| Prompt RevisionAgent | Prompt generico di revisione | Prompt con regole di formato (no Markdown, no emoji), lunghezza target, preservazione date/URL |
| Logger | Senza tempi di esecuzione | Sezione "TEMPI DI ESECUZIONE" con `elapsed_time` per agente + `total_time` pipeline |
| Routing `date_esami` | Presente (Iterazione 4) | Consolidato con gestione caso ospite (NUMERO: 0) e fallback robusto |
| Dizionario corsi | Assente | `DIPARTIMENTI_CORSI` nel frontend con mapping dipartimento → corsi → tipologia |
| `AuthService` | Solo authenticate/createUser | Aggiunta `updateProfile()` e `changePassword()` |
| `AuthController` | Solo login/register | Aggiunta `update_profile()` e `change_password()` |
| `ProfileRepository` | Solo findById/save/exists | Aggiunta `updateProfile()` |

### 3.2 Workflow LangGraph (Invariato)

```
classify → query → [routing condizionale] → generate → revise → END
                       ├── web_search      (per tutte le categorie tranne date_esami)
                       └── exam_extract    (solo per la categoria date_esami)
```

Il workflow LangGraph rimane strutturalmente identico all'Iterazione 4. Le modifiche riguardano i prompt interni degli agenti, non la topologia del grafo.

---

## 4. Timestamp Temporale per gli Agenti

### 4.1 Funzione `get_italian_timestamp()`
Definita in `web_agent.py` e importata da `QueryAgent` e `GeneratorAgent`:

```python
def get_italian_timestamp() -> str:
    now = datetime.datetime.now()
    return f"{now.day:02d} {MESI_ITALIANI[now.month - 1]} {now.year}"
```

Restituisce la data corrente in formato italiano (es. "06 marzo 2026").

### 4.2 Iniezione nei Prompt
- **QueryAgent**: il system prompt include `DATA ODIERNA: {today} (Anno accademico 2025/2026)` e istruisce l'agente a includere il periodo temporale nelle query quando la domanda riguarda date o sessioni.
- **GeneratorAgent**: il system prompt include `DATA ODIERNA: {today} (Anno accademico 2025/2026)` per consentire al modello di determinare "prossima sessione", "scadenza imminente" ecc.
- **WebAgent** (`_format_exam_results`): include `DATA ODIERNA: {today}` nel contesto formattato per il calendario esami.

### 4.3 Motivazione
Senza il timestamp, il modello LLM non ha consapevolezza della data corrente e non può rispondere correttamente a domande come "quando è la prossima sessione?", "la scadenza per l'iscrizione è già passata?" o "in quale sessione siamo?". L'iniezione del timestamp risolve questa limitazione.

---

## 5. Pagina Impostazioni Profilo Utente

### 5.1 Frontend — Componente `SettingsPage`

#### 5.1.1 Struttura
Il componente `SettingsPage` è un pannello overlay accessibile tramite il pulsante ⚙ nell'header, visibile solo per utenti autenticati (`userInfo.status === "loggato"`). Il pannello contiene tre sezioni:

1. **Stato del Server**: indicatore visuale di connessione (connesso/disconnesso).
2. **Dati Profilo**: form per la modifica di nome, cognome, dipartimento, corso di laurea, tipologia e anno.
3. **Cambia Password**: form per il cambio password (password corrente, nuova password, conferma).

#### 5.1.2 Dizionario `DIPARTIMENTI_CORSI`
Struttura dati nel frontend che mappa ogni dipartimento dell'Università di Bergamo ai rispettivi corsi di laurea, con indicazione della tipologia:

```javascript
const DIPARTIMENTI_CORSI = {
    "Scuola di Ingegneria": [
        { nome: "Ingegneria informatica", tipo: "Laurea" },
        { nome: "Ingegneria informatica", tipo: "Laurea Magistrale" },
        // ... altri corsi
    ],
    "Dipartimento di Giurisprudenza": [ ... ],
    "Dipartimento di Scienze Economiche": [ ... ],
    // ... tutti i dipartimenti
};
```

La tipologia viene derivata automaticamente tramite `tipoToTipology()`:
- `"Laurea"` → `"Triennale"`
- `"Laurea Magistrale"` → `"Magistrale"`
- `"Laurea Magistrale a ciclo unico (5 anni)"` → `"Ciclo Unico"`

L'anno massimo selezionabile dipende dalla tipologia (3, 2 o 5).

#### 5.1.3 Logica di Selezione Corso
Quando l'utente cambia dipartimento, il campo corso viene resettato e il dropdown mostra solo i corsi di quel dipartimento. Quando l'utente seleziona un corso, la tipologia viene impostata automaticamente e il campo anno viene resettato a 1.

#### 5.1.4 Propagazione al Parent
Il componente riceve la callback `onProfileUpdate` che aggiorna lo stato `userInfo` in `App.jsx`, propagando immediatamente le modifiche a tutti i componenti che utilizzano il profilo utente (header, prompt degli agenti).

### 5.2 Backend — Endpoint `PUT /api/auth/profile`

- **Path**: `/api/auth/profile`
- **Autenticazione**: richiede JWT valido (`Depends(verify_token)`)
- **Body**: `{ name?, surname?, department?, course?, tipology?, year? }` — tutti i campi opzionali
- **Flusso**:
  1. `verify_token` estrae la matricola dal cookie JWT.
  2. `AuthController.update_profile()` delega ad `AuthService.updateProfile()`.
  3. `AuthService` verifica l'esistenza dell'utente e chiama `ProfileRepository.updateProfile()`.
  4. `ProfileRepository` esegue `update_one` su MongoDB con `$set` dei campi forniti.
  5. Restituisce il profilo aggiornato (senza `passwordHash`).
- **Errori**: `401` se token invalido, `404` se utente non trovato.

### 5.3 Backend — Endpoint `PUT /api/auth/password`

- **Path**: `/api/auth/password`
- **Autenticazione**: richiede JWT valido (`Depends(verify_token)`)
- **Body**: `{ current_password, new_password }`
- **Flusso**:
  1. `verify_token` estrae la matricola dal cookie JWT.
  2. `AuthController.change_password()` delega ad `AuthService.changePassword()`.
  3. `AuthService` verifica la password corrente con `bcrypt.checkpw()`.
  4. Se corretta, hasha la nuova password con `bcrypt.hashpw()` e aggiorna MongoDB.
  5. Restituisce `{ status: "success", message: "Password aggiornata con successo" }`.
- **Errori**: `401` se password corrente errata, `404` se utente non trovato.

### 5.4 Aggiornamenti all'Auth Layer

| Classe | Metodo Aggiunto | Descrizione |
|---|---|---|
| `ProfileRepository` | `updateProfile(matricola, fields)` | Esegue `update_one` con `$set` su MongoDB |
| `AuthService` | `updateProfile(matricola, fields)` | Valida esistenza utente e delega al repository |
| `AuthService` | `changePassword(matricola, current, new)` | Verifica password corrente, hasha nuova, aggiorna MongoDB |
| `AuthController` | `update_profile(matricola, fields)` | Delega a service, restituisce profilo pubblico |
| `AuthController` | `change_password(matricola, current, new)` | Delega a service, restituisce messaggio successo |

---

## 6. Prompt Engineering

### 6.1 Approccio
Il prompt engineering in questa iterazione è stato un processo iterativo e manuale:
1. Esecuzione di test con domande reali diverse (chiusure, materie, sedi, esami, servizi).
2. Analisi delle risposte tramite i log della pipeline (system prompt + raw response).
3. Identificazione di pattern di errore (allucinazioni, contesto ignorato, formattazione errata).
4. Modifica mirata del prompt e nuovo ciclo di test.

### 6.2 ClassifierAgent — Modifiche al Prompt
- Aggiunto contesto conversazionale: la `query_text` viene arricchita con gli ultimi 2 turni di conversazione per una classificazione più accurata nei follow-up.
- Aggiunti esempi dettagliati per la categoria `date_esami`: 4 esempi specifici per guidare la classificazione di domande su date e sessioni d'esame.

### 6.3 QueryAgent — Modifiche al Prompt
- **Regola critica "contesto > profilo"**: il contesto della conversazione ha SEMPRE la priorità sulle informazioni del profilo studente. Se la conversazione indica un corso diverso dal profilo, la query deve riferirsi al corso menzionato nella conversazione.
- **Gestione date e periodi temporali**: quando la domanda riguarda date o sessioni, l'agente include l'anno accademico (2025/2026) nella query generata.
- **Esempi dettagliati**: aggiunti esempi con e senza profilo, esempi di follow-up con contesto divergente dal profilo.
- **Massimo 8 parole**: limite esplicito per mantenere le query compatte.

### 6.4 GeneratorAgent — Modifiche al Prompt
- **`SOURCE_INSTRUCTIONS`**: blocco testuale aggiunto al system prompt quando il contesto web è presente. Contiene 8 regole fondamentali per l'uso delle fonti, inclusa la gestione di link PDF estratti e il formato "Pagina di riferimento: [URL]".
- **History come messaggi LLM nativi**: la `conversation_history` non è più una stringa testuale nel prompt, ma viene iniettata come sequenza di `HumanMessage` / `AIMessage`, sfruttando la memoria nativa del modello per risposte più coerenti nei follow-up.
- **Prompt specializzato `date_esami`**: istruzioni specifiche per cercare date all'interno del calendario fornito, gestire il caso ospite, non esporre metadati interni.
- **Timestamp nel prompt**: `DATA ODIERNA: {today} (Anno accademico 2025/2026)` per consapevolezza temporale.

### 6.5 RevisionAgent — Modifiche al Prompt
- **Regole di formato esplicite**: testo semplice compatibile con tag `<p>` HTML; niente Markdown (`**`, `*`, `#`), niente emoji, uso di MAIUSCOLE per enfasi.
- **Lunghezza target**: risposte semplici in 1-3 frasi; risposte articolate in max 10-15 punti. Date e scadenze NON vengono compresse.
- **Priorità ACCURATEZZA**: le date, scadenze, URL e dati specifici non vengono MAI rimossi durante la revisione.
- **Preservazione "Pagina di riferimento"**: se la risposta del GeneratorAgent contiene URL di fonti, il RevisionAgent li mantiene in fondo.
- **Contesto conversazionale**: la revisione considera gli ultimi 2 turni per evitare contraddizioni con risposte precedenti.

---

## 7. Tempi di Esecuzione nel Logger

### 7.1 Raccolta dei Tempi
Ogni nodo del workflow LangGraph misura il proprio tempo di esecuzione tramite `time.time()`:

```python
start = time.time()
# ... esecuzione agente ...
elapsed = time.time() - start
state["workflow_steps"].append({
    "step": "classification",
    "agent": "ClassifierAgent",
    "result": classification,
    "elapsed_time": elapsed
})
```

Il tempo totale della pipeline viene calcolato nell'`OrchestratorAgent.process_query()`:

```python
pipeline_start = time.time()
final_state = await self.workflow.ainvoke(initial_state)
total_time = time.time() - pipeline_start
```

### 7.2 Sezione nel Log
Il `PipelineLogger` include ora una sezione "TEMPI DI ESECUZIONE" alla fine del file di log:

```
------------------------------------------------------------
TEMPI DI ESECUZIONE
------------------------------------------------------------
  Classifier Agent       : 0.842s
  Query Agent            : 1.231s
  Web Agent              : 3.456s
  Generator Agent        : 2.108s
  Revision Agent         : 1.567s

  TEMPO TOTALE           : 9.204s
```

### 7.3 Metodo `_format_timing_section()`
Il metodo utilizza una mappa `step_labels` per tradurre i nomi tecnici degli step in etichette leggibili, e formatta ogni tempo con 3 decimali.

---

## 8. Analisi Dinamica

### 8.1 Flusso di Modifica Profilo
1. L'utente clicca ⚙ nell'header della chat.
2. Si apre il pannello `SettingsPage` come overlay.
3. L'utente modifica i campi desiderati e clicca "Salva Modifiche".
4. Il frontend invia `PUT /api/auth/profile` con i nuovi dati e il cookie JWT.
5. Il backend valida il token, aggiorna il profilo su MongoDB e restituisce il profilo aggiornato.
6. Il frontend aggiorna `userInfo` nello stato React tramite `onProfileUpdate`.
7. Tutte le successive query invieranno il profilo aggiornato agli agenti.

### 8.2 Flusso di Cambio Password
1. L'utente compila il form "Cambia Password" nella `SettingsPage`.
2. Il frontend valida che la nuova password abbia almeno 6 caratteri e che la conferma corrisponda.
3. `PUT /api/auth/password` invia password corrente e nuova con il cookie JWT.
4. Il backend verifica la password corrente con bcrypt, hasha la nuova e aggiorna MongoDB.
5. Il frontend mostra il messaggio di successo e resetta i campi.

### 8.3 Flusso Pipeline con Timestamp (invariato nella struttura)
1. Query dell'utente entra nel workflow LangGraph.
2. Il `ClassifierAgent` classifica la query usando il contesto conversazionale.
3. Il `QueryAgent` genera la search query con data odierna se pertinente.
4. Il `WebAgent` esegue la ricerca (o `exam_extract` per `date_esami`).
5. Il `GeneratorAgent` produce la risposta con timestamp e fonti web nel prompt.
6. Il `RevisionAgent` revisiona applicando le regole di formato.
7. Il `PipelineLogger` scrive il log con i tempi di esecuzione.

---

## 9. Analisi Statica — Aggiornamenti

### 9.1 `AgentState` (invariato)
Nessun campo aggiunto allo stato. I campi `calendar_context`, `web_context` e `workflow_steps` (con `elapsed_time`) erano già presenti nell'Iterazione 4.

### 9.2 Nuovi Modelli Pydantic

```python
class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    department: Optional[str] = None
    course: Optional[str] = None
    tipology: Optional[str] = None
    year: Optional[int] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
```

### 9.3 `ProfileRepository` — Metodo Aggiunto
```python
async def updateProfile(self, matricola: str, fields: dict) -> dict:
    await self._collection.update_one(
        {"matricola": matricola}, {"$set": fields}
    )
    return await self.findById(matricola)
```

### 9.4 `AuthService` — Metodi Aggiunti
- `updateProfile(matricola, fields)`: valida esistenza, delega a `ProfileRepository.updateProfile()`.
- `changePassword(matricola, current, new)`: verifica password corrente con bcrypt, hasha nuova password, aggiorna MongoDB.

### 9.5 `AuthController` — Metodi Aggiunti
- `update_profile(matricola, fields)`: delega a service, filtra profilo pubblico.
- `change_password(matricola, current, new)`: delega a service, restituisce messaggio.

### 9.6 Frontend — Nuovo Componente `SettingsPage`
- File: `src/SettingsPage.jsx` + `src/SettingsPage.css`
- Props: `userInfo`, `connectionStatus`, `onClose`, `onProfileUpdate`
- Stato locale: `profileData`, `passwordData`, messaggi feedback, loading
- Utilizza `DIPARTIMENTI_CORSI` per la selezione gerarchica dipartimento → corso → tipologia

### 9.7 Frontend — Aggiornamenti a `App.jsx`
- Aggiunto stato `showSettings` e toggle tramite pulsante ⚙ nell'header.
- Aggiunta callback `handleProfileUpdate` che aggiorna `userInfo` nello stato React.
- Il pulsante impostazioni è visibile solo per utenti con `status === "loggato"`.

---

## 10. Endpoint API — Aggiornamenti

| Metodo | Path | Novità | Descrizione |
|--------|------|--------|-------------|
| `POST` | `/api/auth/login` | — | Login (invariato) |
| `POST` | `/api/auth/register` | — | Registrazione (invariato) |
| `GET` | `/api/auth/verify` | — | Verifica sessione (invariato) |
| `POST` | `/api/auth/logout` | — | Logout (invariato) |
| `PUT` | `/api/auth/profile` | **Nuovo** | Aggiorna dati profilo utente |
| `PUT` | `/api/auth/password` | **Nuovo** | Cambia password utente |
| `POST` | `/api/agent/query` | Aggiornato | Prompt interni migliorati (trasparente per l'API) |
| `GET` | `/api/agents` | — | Lista agenti (invariato) |

---

## 11. Limitazioni dell'Iterazione 5

- **Ricerca solo su unibg.it**: il WebAgent resta limitato ai domini universitari.
- **Top 5 risultati fissi**: nessun re-ranking semantico.
- **Calendari esami statici**: `EXAM_CALENDAR_LINKS` hardcoded, da aggiornare manualmente.
- **Log solo su file system**: non consultabili via API né persistiti su MongoDB.
- **Nessun refresh token JWT**: invariato dall'Iterazione 3.
- **Conversazione solo in localStorage**: la history non è persistita sul backend.
- **`secure=False` sul cookie**: da abilitare in produzione con HTTPS.
- **Validazione profilo lato server limitata**: il backend accetta qualsiasi valore per dipartimento/corso senza validare contro l'elenco ufficiale.

---

## 12. Diagrammi UML

Tutti i diagrammi sono in formato PlantUML (`.puml`).

| Diagramma | File | Descrizione |
|---|---|---|
| Use Case | `usecase_diagram5.puml` | Casi d'uso UC-01 — UC-16 (include UC-14 Modifica Profilo, UC-15 Cambio Password, UC-16 Timestamp) |
| Activity | `activity_diagram5.puml` | Flusso attività pipeline completa con timestamp e logging tempi |
| Sequence | `sequence_diagram5.puml` | Pipeline end-to-end con timestamp e tempi logging |
| Sequence (Settings) | `sequence_settings5.puml` | Flusso modifica profilo e cambio password |
| Class (Auth) | `class_auth_diagram5.puml` | Package `auth` aggiornato con updateProfile e changePassword |
| Class (Agents + Logger) | `class_agents_diagram5.puml` | Package `agents` + `logger` con timestamp e timing |
| Class (Frontend) | `class_frontend_diagram5.puml` | Package `frontend` con SettingsPage e DIPARTIMENTI_CORSI |
| Component (Overview) | `component5.puml` | Architettura a 4 tier (invariata nella struttura) |
| Component (Auth) | `component_auth_diagram5.puml` | Dettaglio Auth Layer con nuovi endpoint profile/password |
| Component (Agents) | `component_agents_diagram5.puml` | Dettaglio Agent Layer con timestamp e prompt engineering |

---

## 13. Obiettivi Raggiunti

| Obiettivo | Stato |
|---|---|
| Timestamp temporale per tutti gli agenti | ✅ Completato |
| Routing `date_esami` con Extract consolidato | ✅ Completato |
| Pagina impostazioni profilo utente (SettingsPage) | ✅ Completato |
| Endpoint PUT /api/auth/profile | ✅ Completato |
| Endpoint PUT /api/auth/password | ✅ Completato |
| Dizionario DIPARTIMENTI_CORSI nel frontend | ✅ Completato |
| Prompt engineering ClassifierAgent | ✅ Completato |
| Prompt engineering QueryAgent (contesto > profilo) | ✅ Completato |
| Prompt engineering GeneratorAgent (SOURCE_INSTRUCTIONS, history nativa) | ✅ Completato |
| Prompt engineering RevisionAgent (formato, lunghezza, accuratezza) | ✅ Completato |
| Tempi di esecuzione nel PipelineLogger | ✅ Completato |
| Test manuali iterativi | ✅ Completato |
| Re-ranking semantico risultati web | ⏳ Rimandato |
| Log consultabili via API / MongoDB | ⏳ Rimandato |
| Refresh token JWT | ⏳ Rimandato |
| Persistenza conversazione su backend | ⏳ Rimandato |
| Validazione server-side dei dati profilo | ⏳ Rimandato |
