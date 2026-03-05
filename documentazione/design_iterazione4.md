# Design Document — Iterazione 4: Query Agent, Web Agent e Logger

## 1. Obiettivo dell'iterazione

Estendere il pipeline degli agenti con: (1) **QueryAgent** per ottimizzare le query di ricerca web, (2) **WebAgent** per eseguire ricerche su siti UniBG tramite Tavily API (con sotto-flusso specializzato per date esami), (3) **PipelineLogger** per registrare l'intera esecuzione di ogni query su file di log strutturato.

Il workflow diventa: `Classifier → QueryAgent → WebAgent → Generator → Reviser` con branching condizionale dopo QueryAgent: se la categoria è `date_esami` si attiva il sotto-flusso `exam_extract`, altrimenti il `web_search` standard.

---

## 2. Algoritmo 1: Ricerca Web con Ranking e Branching Condizionale (WebAgent + Workflow)

### 2.1 Descrizione

Il WebAgent esegue ricerche web avanzate tramite l'API Tavily, filtrate su domini UniBG. Recupera fino a 30 risultati, li ordina per score di rilevanza e seleziona i top-5. Per la categoria `date_esami`, esiste un sotto-flusso specializzato che:
1. Usa l'LLM per scegliere il calendario esami corretto tra più dipartimenti
2. Estrae il contenuto del PDF/pagina del calendario con Tavily Extract
3. Integra con 3 risultati web aggiuntivi

### 2.2 Pseudocodice — Web Search Standard

```
ALGORITHM WebSearch(search_query)

INPUT:  search_query (stringa ottimizzata dal QueryAgent)
OUTPUT: {web_results, formatted_context}

1.  // Esecuzione ricerca Tavily con filtro domini
    response ← TavilyClient.search(
        query=search_query,
        search_depth="advanced",
        include_domains=["unibg.it", "unibg.coursecatalogue.cineca.it"],
        max_results=30,
        chunks_per_source=5,
        include_raw_content=TRUE
    )

2.  results ← response.results    // Lista di N risultati (N ≤ 30)

3.  // Ordinamento per score di rilevanza (decrescente)
    sorted_results ← SORT(results, key=score, descending=TRUE)

4.  // Selezione top-5
    top_results ← sorted_results[0:5]

5.  // Arricchimento: estrazione link da PDF
    FOR EACH result IN top_results:
        IF result.url ENDS WITH ".pdf":
            pdf_bytes ← HTTP_GET(result.url)
            doc ← PyMuPDF.open(pdf_bytes)
            pdf_links ← []
            seen ← SET()
            FOR EACH page IN doc:
                FOR EACH link IN page.get_links():
                    IF link.uri NOT IN seen:
                        seen.add(link.uri)
                        pdf_links.append({uri: link.uri, page: page_num})
            result.pdf_links ← pdf_links

6.  // Formattazione testo per il GeneratorAgent
    formatted ← FORMAT_RESULTS(top_results)

7.  RETURN {
        web_results: top_results,
        formatted_context: formatted,
        total_results: N,
        top_results_count: 5
    }
```

### 2.3 Pseudocodice — Sotto-flusso Exam Extract

```
ALGORITHM SearchAndExtractExams(query, user_context)

INPUT:  query (stringa), user_context (contesto utente)
OUTPUT: {formatted_context} con calendario + fonti web

1.  // Recupera TUTTI i calendari disponibili
    calendars ← GET_ALL_CALENDARS()
    // { "Scuola di Ingegneria": [{sessione, url}, ...],
    //   "Polo Economico-Giuridico": [...], ... }

2.  // LLM sceglie il calendario corretto
    options ← []
    FOR EACH (polo, sessions) IN calendars:
        FOR EACH session IN sessions:
            IF session.url IS NOT NULL:
                options.append({index, polo, sessione, url})

    prompt ← "Oggi è {data}. L'utente chiede: {query}.
              Calendari disponibili: {options}.
              Scegli il NUMERO del calendario corretto.
              IMPORTANTE: scegli in base alla domanda, non al profilo."

    llm_response ← LLM.invoke(prompt)
    chosen ← PARSE_CHOICE(llm_response, option_map)
    // Se parsing fallisce → fallback al primo link disponibile

3.  // Estrazione contenuto dal calendario scelto
    IF chosen.url IS NOT NULL:
        extract ← TavilyClient.extract(urls=[chosen.url])
        calendar_content ← extract.results[0].raw_content

4.  // Ricerca web supplementare (top 3)
    web_results ← WebSearch(query).top_results[0:3]

5.  // Composizione del contesto formattato
    formatted ← ""
    formatted += "CALENDARIO ESAMI ESTRATTO\n"
    formatted += "Polo: " + chosen.polo + "\n"
    formatted += "Sessione: " + chosen.sessione + "\n"
    formatted += calendar_content + "\n"
    formatted += "FONTI WEB AGGIUNTIVE\n"
    FOR EACH result IN web_results:
        formatted += result.title + "\n" + result.content + "\n"

6.  RETURN { formatted_context: formatted }
```

### 2.4 Analisi di Complessità

Sia:
- $N$ = numero di risultati Tavily (max 30)
- $T$ = tempo di chiamata API Tavily
- $P$ = numero di pagine dei PDF trovati
- $L$ = costo invocazione LLM (solo per exam_extract)
- $K$ = numero totale di calendari disponibili

**Web Search Standard:**

| Operazione | Complessità |
|---|---|
| Chiamata Tavily search | $O(T)$ — I/O di rete |
| Ordinamento risultati | $O(N \log N)$ — con $N \leq 30$ è $O(1)$ |
| Selezione top-5 | $O(1)$ — slice |
| Estrazione link PDF (per ogni PDF nei top-5) | $O(P)$ — scansione pagine |
| Formattazione | $O(5)$ = $O(1)$ |
| **Totale** | $O(T + P)$ |

**Exam Extract:**

| Operazione | Complessità |
|---|---|
| Recupero calendari | $O(1)$ — dizionario statico |
| Costruzione opzioni | $O(K)$ — iterazione su tutti i poli/sessioni |
| Invocazione LLM (scelta calendario) | $O(L)$ |
| Parsing risposta LLM | $O(m)$ — $m$ = lunghezza risposta |
| Tavily Extract | $O(T)$ |
| Web Search supplementare | $O(T + N \log N)$ |
| Formattazione | $O(1)$ |
| **Totale** | $O(L + 2T)$ |

Il costo totale del sotto-flusso exam_extract è circa il doppio di una ricerca standard, a causa dell'invocazione LLM aggiuntiva per la scelta del calendario e della doppia chiamata Tavily (extract + search).

---

## 3. Algoritmo 2: Pipeline Logger (PipelineLogger)

### 3.1 Descrizione

Il PipelineLogger cattura l'intera esecuzione della pipeline per ogni query utente e la scrive su un file di testo strutturato. Il log include: informazioni utente, query originale, storico conversazione, prompt/risposta di ogni agente, tempi di esecuzione. Il file viene salvato con nome `log_{matricola}_{timestamp}.txt`.

### 3.2 Pseudocodice

```
ALGORITHM WriteLog(state, workflow_steps, total_time)

INPUT:  state (AgentState finale),
        workflow_steps (lista dei passi eseguiti con timing),
        total_time (tempo totale pipeline in secondi)
OUTPUT: filepath (percorso del file di log creato)

1.  timestamp ← NOW()
    matricola ← state.user_matricola OR "ospite"
    filename ← "log_" + matricola + "_" + FORMAT(timestamp) + ".txt"
    filepath ← LOGS_DIR / filename

2.  lines ← []

3.  // SEZIONE: Intestazione
    lines.append("=" * 80)
    lines.append("AGENTIC UNIBG - PIPELINE LOG")
    lines.append("Timestamp: " + FORMAT(timestamp))
    lines.append("Status: " + state.status)

4.  // SEZIONE: Informazioni utente
    IF state.user_status == "loggato":
        lines.append("Nome: " + state.user_name + " " + state.user_surname)
        lines.append("Matricola: " + state.user_matricola)
        lines.append("Corso: " + state.user_course)
        // ... altri campi
    ELSE:
        lines.append("(Utente ospite)")

5.  // SEZIONE: Query e storico
    lines.append("QUERY: " + state.query)
    IF state.conversation_history:
        FOR EACH msg IN conversation_history[-6:]:
            lines.append("[" + msg.role + "]: " + msg.content[:300])

6.  // SEZIONE: Step della pipeline
    step_map ← BUILD_MAP(workflow_steps, key=step_name)

    FOR EACH step_name IN ["classification", "query_generation",
                            "web_search|exam_extract", "generation", "revision"]:
        step ← step_map[step_name]
        lines.append("STEP: " + step.agent)
        lines.append("Status: " + step.result.status)
        lines.append("System Prompt: " + step.result.system_prompt)
        lines.append("User Prompt: " + step.result.user_prompt)
        lines.append("Risposta: " + step.result.raw_response)
        lines.append("Tempo: " + FORMAT(step.elapsed_time) + "s")

7.  // SEZIONE: Risposta finale
    lines.append("RISPOSTA FINALE: " + state.final_response)

8.  // SEZIONE: Tempi di esecuzione
    FOR EACH step IN workflow_steps:
        lines.append(step.agent + ": " + step.elapsed_time + "s")
    lines.append("TEMPO TOTALE: " + total_time + "s")

9.  // Scrittura su file
    WRITE_FILE(filepath, JOIN(lines, "\n"))

10. RETURN filepath
```

### 3.3 Analisi di Complessità

Sia:
- $S$ = numero di step nel workflow (costante, $S = 5$)
- $H$ = messaggi nello storico conversazione (max 6 visualizzati)
- $R$ = dimensione totale delle risposte e prompt (in caratteri)

| Operazione | Complessità |
|---|---|
| Costruzione nome file | $O(1)$ |
| Costruzione sezione utente | $O(1)$ |
| Costruzione sezione storico | $O(H)$ = $O(1)$ con $H \leq 6$ |
| Costruzione sezioni agenti ($S$ step) | $O(S \cdot R)$ |
| Costruzione sezione tempi | $O(S)$ = $O(1)$ |
| Scrittura su file | $O(R)$ — I/O su disco |
| **Totale** | $O(R)$ |

La complessità è dominata dalla dimensione totale del contenuto da scrivere ($R$), che include i prompt di sistema, i prompt utente e le risposte di tutti gli agenti. In pratica $R$ può variare da pochi KB (domanda semplice) a decine di KB (exam_extract con calendario completo), ma resta un'operazione singola di I/O su disco.

**Complessità spaziale**: $O(R)$ — tutte le righe del log vengono accumulate in una lista prima della scrittura.

---

## 4. Workflow Completo dell'Iterazione 4

```
                    ┌──────────┐
                    │ CLASSIFY │
                    └────┬─────┘
                         │
                    ┌────┴─────┐
                    │  QUERY   │
                    │  AGENT   │
                    └────┬─────┘
                         │
                   ┌─────┴─────┐
                   │ category? │
                   └──┬─────┬──┘
                      │     │
          date_esami  │     │  (altri)
                      ▼     ▼
              ┌───────────┐ ┌───────────┐
              │   EXAM    │ │   WEB     │
              │  EXTRACT  │ │  SEARCH   │
              └─────┬─────┘ └─────┬─────┘
                    │             │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  GENERATOR  │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │   REVISER   │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │   LOGGER    │
                    └─────────────┘
```
