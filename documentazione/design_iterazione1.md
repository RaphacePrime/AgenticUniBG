# Design Document — Iterazione 1: Inviare Domanda e Ricevere Risposta

## 1. Obiettivo dell'iterazione

Implementare il flusso base del sistema multi-agent: l'utente invia una domanda in linguaggio naturale e riceve una risposta generata dal pipeline di agenti orchestrato da LangGraph.

---

## 2. Algoritmo 1: Pipeline Orchestrator (LangGraph Workflow)

### 2.1 Descrizione

L'Orchestrator coordina la pipeline sequenziale di agenti: **Classifier → Generator → Reviser**. Il workflow è modellato come un grafo orientato aciclico (DAG) tramite LangGraph `StateGraph`. Ogni nodo del grafo è una funzione asincrona che modifica lo stato condiviso `AgentState`.

### 2.2 Pseudocodice

```
ALGORITHM OrchestratorPipeline(query)

INPUT:  query (stringa in linguaggio naturale)
OUTPUT: final_response (stringa con la risposta generata)

1.  state ← INIT_STATE(query)
    // Inizializza AgentState con la query e tutti i campi a null

2.  // STEP 1 — Classificazione
    state ← CLASSIFY(state)
    //  2a. Costruisci system_prompt con le categorie disponibili
    //  2b. Invoca LLM con [SystemMessage(prompt), HumanMessage(query)]
    //  2c. Estrai la categoria dalla risposta (una tra CATEGORIES.keys())
    //  2d. Se la categoria non è valida → category = "altro"
    //  2e. Aggiorna state.category, state.category_description, state.confidence

3.  // STEP 2 — Generazione
    state ← GENERATE(state)
    //  3a. Seleziona il prompt di sistema dalla mappa CATEGORY_PROMPTS[state.category]
    //  3b. Costruisci messages = [SystemMessage(category_prompt), HumanMessage(query)]
    //  3c. Invoca LLM
    //  3d. Aggiorna state.generated_response

4.  // STEP 3 — Revisione
    state ← REVISE(state)
    //  4a. Costruisci prompt di revisione con query originale + risposta generata
    //  4b. Invoca LLM con prompt di revisione
    //  4c. Aggiorna state.final_response, state.has_revisions

5.  RETURN state.final_response
```

### 2.3 Analisi di Complessità

Sia:
- $n$ = lunghezza della query in token
- $k$ = numero di categorie (costante, $k = 7$)
- $L$ = costo di una singola invocazione LLM (tempo dominante)

| Operazione | Complessità Temporale |
|---|---|
| Inizializzazione stato | $O(1)$ |
| Classificazione (invocazione LLM) | $O(L)$ |
| Validazione categoria (lookup in dizionario) | $O(1)$ ammortizzato |
| Generazione (invocazione LLM) | $O(L)$ |
| Revisione (invocazione LLM) | $O(L)$ |
| **Totale pipeline** | $O(3L) = O(L)$ |

La complessità è **dominata dalle invocazioni LLM**, che sono operazioni I/O-bound con latenza variabile (tipicamente 1-5 secondi ciascuna). Le operazioni computazionali locali (costruzione prompt, parsing, lookup) sono $O(1)$ o $O(n)$ rispetto alla lunghezza dell'input, ma trascurabili rispetto a $L$.

**Complessità spaziale**: $O(n + R)$ dove $R$ è la dimensione della risposta LLM, dovuta al mantenimento dello stato `AgentState` in memoria.

---

## 3. Algoritmo 2: Classificazione della Query (ClassifierAgent)

### 3.1 Descrizione

Il ClassifierAgent prende una query in linguaggio naturale e la classifica in una delle 7 categorie predefinite usando un approccio **zero-shot classification via LLM**: il modello riceve un prompt con le categorie e deve restituire esattamente il nome della categoria corretta.

### 3.2 Pseudocodice

```
ALGORITHM ClassifyQuery(query, categories)

INPUT:  query (stringa), categories (dizionario {chiave: descrizione})
OUTPUT: classification (dizionario {category, description, confidence})

1.  // Costruisci il prompt di sistema
    prompt ← "Sei un agente classificatore..."
    FOR EACH (cat, desc) IN categories:
        prompt ← prompt + "- " + cat + ": " + desc + "\n"
    prompt ← prompt + "Rispondi SOLO con il nome della categoria"

2.  // Invoca il modello
    messages ← [SystemMessage(prompt), HumanMessage(query)]
    response ← LLM.invoke(messages)

3.  // Parsing e validazione
    category ← response.content.strip().lower()
    IF category NOT IN categories.keys():
        category ← "altro"    // Fallback

4.  RETURN {
        category: category,
        description: categories[category],
        confidence: "high"
    }
```

### 3.3 Analisi di Complessità

| Operazione | Complessità Temporale |
|---|---|
| Costruzione prompt (iterazione su $k$ categorie) | $O(k)$ — costante con $k=7$ |
| Invocazione LLM | $O(L)$ |
| Parsing risposta (strip + lower) | $O(m)$ — $m$ = lunghezza risposta |
| Validazione categoria (lookup in dict) | $O(1)$ ammortizzato |
| **Totale** | $O(L)$ |

La classificazione è essenzialmente un singolo round-trip al modello LLM. La validazione con fallback garantisce che il sistema non si blocchi mai su risposte malformate del modello: nel caso peggiore si ottiene la categoria "altro", mantenendo il flusso funzionante.

---

## 4. Strutture Dati Chiave

### AgentState (TypedDict)
Stato condiviso immutabile tra i nodi del grafo. I campi principali per l'iterazione 1:

| Campo | Tipo | Descrizione |
|---|---|---|
| `query` | `str` | Query originale dell'utente |
| `category` | `Optional[str]` | Categoria classificata |
| `generated_response` | `Optional[str]` | Risposta del GeneratorAgent |
| `final_response` | `Optional[str]` | Risposta dopo la revisione |
| `workflow_steps` | `List[Dict]` | Tracking dei passi eseguiti |
| `status` | `str` | "processing" / "success" / "error" |

### LangGraph StateGraph
Il workflow è modellato come:

```
[classify] → [generate] → [revise] → END
```

Ogni arco è un edge nel grafo. LangGraph gestisce la propagazione automatica dello stato tra nodi consecutivi.
