# Iterazione 4 – Web Search, Query Agent, Gestione Date Esami e Pipeline Logging

---

## 1. Obiettivo dell'Iterazione

L'obiettivo dell'Iterazione 4 è arricchire il sistema con la capacità di recuperare informazioni reali e aggiornate dal sito dell'Università di Bergamo, oltre a introdurre un sistema di logging completo della pipeline. Le macro-funzionalità introdotte sono:

- **QueryAgent**: agente dedicato alla generazione di query di ricerca web ottimizzate a partire dalla domanda dell'utente, dalla cronologia della conversazione e dal profilo dello studente.
- **WebAgent**: agente che esegue ricerche web tramite **Tavily API** su domini specifici dell'ateneo (`unibg.it`, `unibg.coursecatalogue.cineca.it`), estrae i contenuti testuali dei top 5 risultati e gestisce anche documenti PDF tramite **PyMuPDF**.
- **Categoria `date_esami` e Routing Condizionale**: il `ClassifierAgent` riconosce la nuova categoria `date_esami`. Il workflow LangGraph implementa un **routing condizionale** dopo il nodo `query`: se la categoria è `date_esami`, il flusso viene dirottato verso un nodo dedicato `exam_extract` (che usa LLM per selezionare il calendario corretto e Tavily Extract per estrarne il contenuto), altrimenti prosegue con il nodo `web_search` standard.
- **EXAM_CALENDAR_LINKS**: dizionario strutturato con i link ai calendari esami ufficiali di ciascun polo/dipartimento e sessione, usato dal WebAgent per la selezione intelligente del calendario.
- **PipelineLogger**: componente che scrive un file di log dettagliato per ogni query elaborata, tracciando tutti i passi della pipeline (classificazione, search query, risultati web, generazione, revisione).
- **Cambio LLM Provider**: da **Groq / llama-3.3-70b-versatile** a **Google Gemini 2.5 Flash** per tutti gli agenti.

---

## 2. User Stories Incluse

| ID | Descrizione | Ruolo |
|----|-------------|-------|
| US-10 | Come studente, voglio che il sistema recuperi informazioni reali dal sito di UniBG per rispondermi con dati aggiornati | Studente |
| US-11 | Come sistema, voglio generare query di ricerca ottimizzate tenendo conto del profilo dello studente, così da trovare informazioni pertinenti al suo percorso | Sistema |
| US-12 | Come sistema, voglio tracciare ogni elaborazione in un log strutturato, così da poter analizzare e migliorare la pipeline | Sistema |
| US-13 | Come studente, voglio ricevere risposte che citino fonti reali dell'università, così da poterle verificare | Studente |
| US-14 | Come studente, voglio chiedere le date degli esami e ricevere informazioni estratte direttamente dal calendario ufficiale del mio polo | Studente |

---

## 3. Architettura Implementata

### 3.1 Novità Rispetto all'Iterazione 3

| Funzionalità | Iterazione 3 | Iterazione 4 |
|---|---|---|
| Recupero dati reali | Assente (solo LLM) | WebAgent su Tavily (unibg.it) |
| Ottimizzazione query | Assente | QueryAgent con Gemini |
| Gestione PDF | Assente | WebAgent + PyMuPDF |
| Logging pipeline | Assente | PipelineLogger su file system |
| LLM Provider | Groq / llama-3.3-70b | Google Gemini 2.5 Flash |
| Workflow LangGraph | classify → generate → revise | classify → query → [web_search \| exam_extract] → generate → revise |
| AgentState | Senza `search_query`, `web_results` | Con `search_query`, `web_results`, `web_context`, `calendar_context` |
| Classificazione | 6 categorie | 7 categorie (aggiunta `date_esami`) |
| Routing | Lineare | Condizionale dopo `query` (date_esami → exam_extract, altri → web_search) |

### 3.2 Workflow LangGraph Aggiornato

```
classify → query → [routing condizionale] → generate → revise → END
                       ├── web_search      (per tutte le categorie tranne date_esami)
                       └── exam_extract    (solo per la categoria date_esami)
```

Ogni nodo corrisponde a un agente specializzato. Il grafo include un **branch condizionale** dopo il nodo `query`: il metodo `_route_after_query(state)` verifica se `state["category"] == "date_esami"` e instrada il flusso verso `exam_extract` oppure verso `web_search`. Entrambi i rami convergono poi su `generate`.

---

## 4. Query Agent

### 4.1 Responsabilità
Trasforma la domanda dell'utente in una **query di ricerca web breve e ottimizzata** (max 6-8 parole chiave), adatta per la ricerca su `unibg.it`.

### 4.2 Logica di Personalizzazione
L'agente decide **autonomamente** se includere le informazioni del profilo studente (corso, anno, tipologia) nella query.

**Regola critica — priorità del contesto conversazionale**: il contesto della conversazione ha SEMPRE la priorità sul profilo dello studente. Se la conversazione indica che l'utente sta chiedendo informazioni su un corso/dipartimento diverso dal proprio, la query deve riferirsi al corso menzionato nella conversazione, non a quello del profilo.

**Includi il profilo quando** la domanda riguarda:
- Materie, piano di studi, crediti del proprio corso
- Orari delle lezioni specifiche del corso
- Qualsiasi domanda la cui risposta dipende dal percorso specifico dello studente
- L'utente usa pronomi possessivi ("mio", "miei", "il mio corso")

**Non includere il profilo quando** la domanda riguarda:
- Procedure generiche (iscrizioni, tasse, borse di studio)
- Informazioni su docenti o servizi universitari
- Informazioni generali sull'ateneo, Erasmus, laurea
- La conversazione indica un argomento/corso diverso dal profilo (follow-up)

### 4.3 Input / Output
- **Input**: `query` + `conversation_history` (ultimi 3 turni) + `user_context`
- **Output**: `{ search_query, original_query, status, system_prompt, user_prompt, raw_response }`
- **Fallback**: se il Gemini fallisce, usa la query originale senza modifiche

---

## 5. Web Agent

### 5.1 Responsabilità
Esegue ricerche su Tavily API limitando i risultati ai domini universitari e prepara il contenuto per il Generator.

### 5.2 Configurazione Tavily
```python
client.search(
    query=search_query,
    search_depth="advanced",
    include_domains=["unibg.it", "unibg.coursecatalogue.cineca.it"],
    max_results=30,
    chunks_per_source=5,
    include_raw_content=True
)
```

- Recupera fino a 30 risultati con contenuto grezzo
- Ordina per `score` decrescente e seleziona i **top 5**

### 5.3 Gestione PDF
Se un risultato punta a un URL `.pdf`, l'agente:
1. Scarica il PDF in memoria tramite `requests`
2. Apre il documento con **PyMuPDF** (`fitz`)
3. Estrae tutti i link ipertestuali (URI + numero pagina) da ogni pagina
4. I link vengono inclusi nel contesto formattato passato al Generator

### 5.4 Output
```python
{
  "web_results": [ { rank, title, url, content, score, is_pdf, pdf_links } ],
  "formatted_context": "INFORMAZIONI DAL SITO DELL'UNIVERSITÀ DI BERGAMO: ...",
  "total_results": int,
  "top_results_count": int,
  "status": "success" | "error"
}
```

Il `formatted_context` viene iniettato in `context["additional_info"]` e passato al `GeneratorAgent` come fonte primaria per la risposta.

---

## 5bis. Gestione Date Esami (`exam_extract`)

### 5bis.1 Responsabilità
Quando il `ClassifierAgent` riconosce la categoria `date_esami`, il workflow bypassa il nodo `web_search` standard e attiva il nodo `exam_extract`, che implementa un flusso in tre fasi:

1. **Selezione intelligente del calendario** tramite LLM
2. **Estrazione del contenuto** tramite Tavily Extract
3. **Ricerca web aggiuntiva** per fonti complementari (top 3)

### 5bis.2 `EXAM_CALENDAR_LINKS`
Il dizionario `EXAM_CALENDAR_LINKS` contiene i link ai calendari esami ufficiali organizzati per polo/dipartimento e sessione:

- **Scuola di Ingegneria** — sessioni: intermedia/aprile, estiva, autunnale (PDF su `unibg.it`)
- **Polo Economico-Giuridico** — sessioni: intermedia (HTML), estiva e autunnale (PDF su `logistica.unibg.it`)
- **Polo Linguistico** — sessioni: estiva, autunnale (PDF su `logistica.unibg.it`)
- **Polo Umanistico** — sessioni: primaverile, Scienze della Formazione, estiva, autunnale (PDF su `logistica.unibg.it`)

Ogni entry indica anche se la sessione è già conclusa o non ancora disponibile.

### 5bis.3 Selezione del Calendario (`_select_calendar_link`)
L'LLM riceve la domanda dell'utente, il contesto utente (profilo) e la lista completa dei calendari disponibili. Il prompt contiene una **regola critica**:

- Se l'utente è un **ospite** e **non specifica** un corso o dipartimento nella domanda → l'LLM risponde `NUMERO: 0` (nessun calendario selezionabile)
- Se l'utente è **autenticato** o ha specificato esplicitamente il corso → l'LLM sceglie il calendario del polo corrispondente alla domanda (non necessariamente al profilo dello studente)
- Se la domanda chiede della "prossima sessione", viene scelta la sessione più prossima alla data odierna

### 5bis.4 Tavily Extract
Una volta selezionato il link, `WebAgent.extract(url)` usa l'API Tavily Extract per estrarre il contenuto completo della pagina (HTML o PDF) in formato testuale.

### 5bis.5 Output Formattato
Il `_format_exam_results()` costruisce un testo che include:
- La data odierna (per contesto temporale)
- Il polo e la sessione selezionati
- Il contenuto completo del calendario estratto
- Il link al portale generale esami di UniBG
- Le top 3 fonti web aggiuntive da Tavily Search

Questo contesto viene passato al `GeneratorAgent` con un prompt specializzato per `date_esami` che istruisce il modello a cercare le date specifiche richieste all'interno del calendario fornito.

---

## 6. Pipeline Logger

### 6.1 Responsabilità
Scrive un file `.txt` nella cartella `logs/` per ogni query elaborata, con tracciamento completo di tutti i passi della pipeline.

### 6.2 Naming Convention
```
log_{matricola}_{YYYYMMDD_HHMMSS_ffffff}.txt
log_ospite_{YYYYMMDD_HHMMSS_ffffff}.txt
```

### 6.3 Struttura del Log
Ogni file contiene le seguenti sezioni:
1. **Header** — timestamp, status pipeline
2. **User Information** — tipo utente, nome, corso, anno, dipartimento
3. **Original User Query**
4. **Conversation History** — ultimi 3 turni
5. **Step 1 – Classifier Agent** — categoria, descrizione, confidence
6. **Step 2 – Query Agent** — search query generata, query originale
7. **Step 3 – Web Agent** oppure **Web Agent (Exam Calendar Extract)** — risultati Tavily, oppure selezione calendario e contenuto estratto
8. **Step 4 – Generator Agent** — risposta generata
9. **Step 5 – Revision Agent** — risposta finale, modifiche apportate
10. **Tempi di esecuzione** — tempo di ogni agente e tempo totale pipeline

### 6.4 Integrazione nell'Orchestratore
Il logger viene invocato **dopo** il completamento del workflow, mai prima, e gli errori di logging non interrompono la pipeline:
```python
try:
    self.logger.write_log(final_state, final_state.get("workflow_steps", []))
except Exception:
    pass  # Logging non blocca mai la risposta all'utente
```

---

## 7. Cambio LLM Provider

### Motivazione
Il provider LLM è stato cambiato da **Groq (llama-3.3-70b-versatile)** a **Google Gemini 2.5 Flash**:

| Aspetto | Groq / llama-3.3-70b | Google Gemini 2.5 Flash |
|---|---|---|
| Latenza | Molto bassa | Bassa |
| Context window | 128K tokens | 1M tokens |
| Qualità ragionamento | Alta | Molto alta |
| Gestione contesti lunghi | Limitata | Ottima (utile con web context) |

Il context window più ampio è fondamentale per questa iterazione, dato che il `web_context` può contenere fino a 5 risultati completi di testo grezzo.

Tutti gli agenti (`ClassifierAgent`, `QueryAgent`, `GeneratorAgent`, `RevisionAgent`) usano la stessa istanza `ChatGoogleGenerativeAI` inizializzata nell'`OrchestratorAgent`.

---

## 8. Analisi Dinamica – Flusso Pipeline Completa

1. Il frontend invia `POST /api/agent/query` con query, user_info e conversation_history (cookie allegato).
2. L'`OrchestratorAgent` inizializza `AgentState` con tutti i campi.
3. **Classify**: il `ClassifierAgent` determina la categoria e la confidence della query. La nuova categoria `date_esami` intercetta domande su date e sessioni degli esami.
4. **Query**: il `QueryAgent` genera una search query ottimizzata considerando profilo e history.
5. **Routing condizionale**:
   - Se `category == "date_esami"` → **Exam Extract**: l'LLM seleziona il calendario corretto tra `EXAM_CALENDAR_LINKS`, Tavily Extract ne estrae il contenuto, e una Tavily Search recupera le top 3 fonti aggiuntive.
   - Altrimenti → **Web Search**: il `WebAgent` interroga Tavily, recupera i top 5 risultati, gestisce PDF.
6. **Generate**: il `GeneratorAgent` riceve query + categoria + web_context (o calendar_context) + profilo + history; produce la risposta bozza.
7. **Revise**: il `RevisionAgent` revisiona la bozza tenendo conto del contesto della conversazione.
8. **Log**: il `PipelineLogger` scrive il file di log completo su file system, inclusi i tempi di esecuzione di ogni step.
9. La risposta finale viene restituita al frontend.

---

## 9. Aggiornamenti ad `AgentState`

Aggiunti i campi:

| Campo | Tipo | Descrizione |
|---|---|---|
| `search_query` | `Optional[String]` | Query ottimizzata generata dal QueryAgent |
| `web_results` | `Optional[List[Dict]]` | Top 5 risultati Tavily con score, URL, contenuto |
| `web_context` | `Optional[String]` | Testo formattato dei risultati da iniettare nel Generator |
| `calendar_context` | `Optional[String]` | Testo formattato del calendario esami estratto (per `date_esami`) |

---

## 10. Classificazione — Categoria `date_esami`

Il `ClassifierAgent` è stato esteso con la nuova categoria `date_esami`, che intercetta domande relative a date, sessioni e orari degli esami. Esempi nel prompt del classificatore:

- "Quando è l'esame di analisi?" → `date_esami`
- "Che esami ho alla prossima sessione?" → `date_esami`
- "In che date sono gli esami della sessione estiva?" → `date_esami`

Le categorie totali del classificatore sono ora 7: `informazioni_corso`, `orari`, `date_esami`, `procedure`, `servizi`, `generale`, `altro`.

---

## 11. Endpoint API – Nessuna Variazione

Gli endpoint esposti dal backend rimangono invariati rispetto all'Iterazione 3. Le modifiche riguardano esclusivamente la pipeline interna degli agenti.

| Metodo | Path | Descrizione |
|--------|------|-------------|
| `POST` | `/api/auth/login` | Login con cookie JWT |
| `POST` | `/api/auth/register` | Registrazione |
| `GET` | `/api/auth/verify` | Verifica sessione |
| `POST` | `/api/auth/logout` | Logout |
| `POST` | `/api/agent/query` | Elaborazione query (pipeline estesa con routing condizionale) |
| `GET` | `/api/agents` | Lista agenti (aggiornata con query_agent e web_agent) |

---

## 12. Limitazioni dell'Iterazione 4

- **Ricerca solo su unibg.it**: il WebAgent è limitato ai domini universitari; non accede a fonti esterne come banche dati bibliografiche o altri atenei.
- **Top 5 risultati fissi**: la selezione è basata solo sullo score Tavily; non c'è re-ranking semantico.
- **Calendari esami statici**: i link in `EXAM_CALENDAR_LINKS` sono hardcoded e devono essere aggiornati manualmente ogni anno accademico.
- **Log solo su file system**: i log non sono consultabili via API né persistiti su MongoDB.
- **Nessun refresh token JWT**: invariato dall'Iterazione 3.
- **Conversazione solo in localStorage**: la history non è persistita sul backend.
- **`secure=False` sul cookie**: da abilitare in produzione con HTTPS.
- **Gestione profilo utente non ancora disponibile**: l'utente non può modificare i propri dati personali dal frontend.

---

## 13. Diagrammi UML

Tutti i diagrammi sono in formato PlantUML (`.puml`).

| Diagramma | File | Descrizione |
|---|---|---|
| Use Case | `usecase4.puml` | Casi d'uso UC-01 — UC-12 (include UC-11 Risposta con Dati Reali, UC-12 Logging Pipeline) |
| Activity | `activity4.puml` | Flusso attività pipeline completa con QueryAgent, WebAgent e Logger |
| Sequence | `sequence4.puml` | Pipeline end-to-end: Classify → Query → Web → Generate → Revise → Log |
| Class (Auth) | `class4_auth.puml` | Package `auth`: AuthController, AuthService, JWTManager, ProfileRepository, User |
| Class (Agents + Logger) | `class4_agents.puml` | Package `agents` + `logger`: tutti gli agenti incl. QueryAgent, WebAgent, PipelineLogger |
| Class (Frontend) | `class4_frontend.puml` | Package `frontend`: ConversationStore, Message |
| Class (completo) | `class4.puml` | Diagramma classi monolitico (tutti i package in un file) |
| Component (Overview) | `component4.puml` | Architettura a 4 tier (Client, Backend, Data, External Services) con porte |
| Component (Auth) | `component4_auth.puml` | Dettaglio Authentication Layer (invariato da Iterazione 3) |
| Component (Agents) | `component4_agents.puml` | Dettaglio Agent Layer con QueryAgent, WebAgent e porta verso servizi esterni |
| Component (Logging) | `component4_logging.puml` | Dettaglio Logging Layer: PipelineLogger → File System |

---

## 14. Obiettivi Raggiunti

| Obiettivo | Stato |
|---|---|
| QueryAgent per ottimizzazione query di ricerca | ✅ Completato |
| WebAgent con Tavily su domini unibg.it | ✅ Completato |
| Gestione documenti PDF (PyMuPDF) | ✅ Completato |
| Categoria `date_esami` con routing condizionale | ✅ Completato |
| Selezione intelligente calendario esami tramite LLM | ✅ Completato |
| Tavily Extract per contenuto calendari | ✅ Completato |
| PipelineLogger con log strutturati per query | ✅ Completato |
| Cambio LLM provider a Gemini 2.5 Flash | ✅ Completato |
| Pipeline estesa con branch condizionale | ✅ Completato |
| Web context iniettato nel GeneratorAgent | ✅ Completato |
| Prompt specializzato per `date_esami` nel GeneratorAgent | ✅ Completato |
| Gestione profilo utente da frontend | ⏳ Rimandato (Iterazione 5) |
| Miglioramento ClassifierAgent | ⏳ Rimandato (Iterazione 5) |
| Re-ranking semantico risultati web | ⏳ Rimandato |
| Log consultabili via API / MongoDB | ⏳ Rimandato |
| Refresh token JWT | ⏳ Rimandato |
| Persistenza conversazione su backend | ⏳ Rimandato |
