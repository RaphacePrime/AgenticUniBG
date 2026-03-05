# Design Document — Iterazione 3: Memoria Conversazionale e Gestione Sessione

## 1. Obiettivo dell'iterazione

Implementare la memoria conversazionale lato client (localStorage), il mantenimento del contesto tra messaggi successivi nella pipeline di agenti, e la gestione della sessione browser tramite JWT httpOnly cookie con auto-verifica al caricamento.

---

## 2. Algoritmo 1: Gestione del Contesto Conversazionale nella Pipeline

### 2.1 Descrizione

Il contesto conversazionale viene mantenuto lato client (React `useState` + `localStorage`) e inviato ad ogni richiesta come parametro `conversation_history`. Ogni agente nella pipeline utilizza la cronologia in modo diverso:

- **ClassifierAgent**: usa gli ultimi 2 turni (4 messaggi) per disambiguare domande di follow-up
- **QueryAgent**: usa gli ultimi 3 turni (6 messaggi) per generare query di ricerca contestuali
- **GeneratorAgent**: inietta l'intero storico ricevuto come messaggi LLM nativi (`HumanMessage`/`AIMessage`) per una vera memoria conversazionale
- **RevisionAgent**: usa gli ultimi 2 turni per verificare la coerenza della risposta col contesto

### 2.2 Pseudocodice

```
ALGORITHM ProcessQueryWithContext(query, conversation_history, user_info)

INPUT:  query (stringa), 
        conversation_history (lista di {role, content}),
        user_info (dizionario con profilo utente)
OUTPUT: final_response (stringa)

// === LATO CLIENT (React) ===

1.  // Recupero storico dalla memoria locale
    history ← localStorage.getItem("conversation_" + user_matricola)
    IF history IS NOT NULL:
        conversation ← JSON.parse(history)

2.  // Preparazione contesto per l'API
    recent_history ← conversation
        .filter(msg => msg.type IN {"user", "agent"})
        .slice(-10)                    // Ultimi 5 turni (10 messaggi)
        .map(msg => {
            role: (msg.type == "user") ? "user" : "assistant",
            content: msg.content
        })

3.  // Invio richiesta
    response ← POST /api/agent/query {
        query: query,
        user_info: user_info,
        conversation_history: recent_history
    }

// === LATO SERVER (Pipeline) ===

4.  state ← INIT_STATE(query, user_info, conversation_history)

5.  // CLASSIFY con contesto (ultimi 2 turni)
    recent_ctx ← conversation_history[-4:]
    classify_input ← FORMAT_CONTEXT(recent_ctx) + "\nNuova domanda: " + query
    state.category ← CLASSIFY(classify_input)

6.  // QUERY AGENT con contesto (ultimi 3 turni)
    query_ctx ← conversation_history[-6:]
    search_query ← GENERATE_SEARCH_QUERY(query, query_ctx, user_context)
    state.search_query ← search_query

7.  // GENERATOR con contesto completo (memoria nativa LLM)
    messages ← [SystemMessage(category_prompt)]
    FOR EACH msg IN conversation_history:
        IF msg.role == "user":
            messages.append(HumanMessage(msg.content))
        ELSE:
            messages.append(AIMessage(msg.content))
    messages.append(HumanMessage(query))
    state.generated_response ← LLM.invoke(messages)

8.  // REVISE con contesto
    state.final_response ← REVISE(query, generated_response, 
                                    conversation_history[-4:])

// === LATO CLIENT (salvataggio) ===

9.  // Salva in localStorage
    conversation.push({type: "user", content: query})
    conversation.push({type: "agent", content: response})
    localStorage.setItem("conversation_" + user_matricola, 
                          JSON.stringify(conversation))

10. RETURN final_response
```

### 2.3 Analisi di Complessità

Sia:
- $H$ = numero totale di messaggi nella cronologia
- $W$ = finestra di contesto (costante: 10 messaggi max inviati)
- $L$ = costo di una invocazione LLM
- $T$ = numero di token totali nella cronologia troncata

| Operazione | Complessità |
|---|---|
| Recupero da localStorage | $O(H)$ — parsing JSON dell'array |
| Filtraggio e slicing | $O(H)$ |
| Serializzazione JSON per API | $O(W)$ = $O(1)$ con $W$ costante |
| Costruzione contesto Classifier (4 msg) | $O(1)$ |
| Costruzione contesto QueryAgent (6 msg) | $O(1)$ |
| Costruzione messaggi Generator ($W$ messaggi) | $O(W)$ = $O(1)$ |
| Invocazioni LLM (con contesto allargato) | $O(L(T))$ — $L$ dipende da $T$ |
| Salvataggio in localStorage | $O(H)$ |
| **Totale pipeline (server)** | $O(L(T))$ |
| **Totale complessivo (client+server)** | $O(H + L(T))$ |

**Nota importante**: la finestra di 10 messaggi (5 turni) è una scelta progettuale che limita $T$ e impedisce che il costo LLM cresca linearmente con la lunghezza della conversazione. Questo è un trade-off tra qualità del contesto e costo/latenza.

**Complessità spaziale client**: $O(H)$ — tutta la cronologia è memorizzata in localStorage (limite ~5MB per dominio).

---

## 3. Algoritmo 2: Gestione Sessione e Auto-Verifica Token (Frontend)

### 3.1 Descrizione

All'avvio dell'applicazione React, il sistema verifica automaticamente la validità del token JWT presente nel cookie httpOnly. Il flusso gestisce tre stati: (1) loading iniziale, (2) sessione valida → accesso diretto, (3) token assente/scaduto → pagina di login.

### 3.2 Pseudocodice

```
ALGORITHM InitSession()

OUTPUT: stato di autenticazione dell'utente

1.  isInitialLoading ← TRUE
    isAuthenticated ← FALSE
    userInfo ← NULL

2.  // Verifica connessione backend
    TRY:
        health ← GET /api/health
        connectionStatus ← "connected"
    CATCH:
        connectionStatus ← "error"

3.  // Verifica token JWT dal cookie httpOnly
    TRY:
        response ← GET /api/auth/verify  (credentials: "include")
        IF response.status != 200:
            THROW "Token invalido"

        userData ← response.json()
        // { status, name, surname, department, course, ... }

        userInfo ← userData
        isAuthenticated ← TRUE

        // Ripristina la conversazione salvata
        saved ← localStorage.getItem("conversation_" + userData.matricola)
        IF saved IS NOT NULL:
            conversation ← JSON.parse(saved)

    CATCH error:
        // Token assente, scaduto o invalido
        // L'utente vedrà la pagina di login
        isAuthenticated ← FALSE

4.  isInitialLoading ← FALSE

5.  // Rendering condizionale
    IF isInitialLoading:
        RENDER LoadingScreen
    ELSE IF NOT isAuthenticated:
        RENDER LoginPage
    ELSE:
        RENDER ChatInterface(userInfo, conversation)
```

### 3.3 Analisi di Complessità

| Operazione | Complessità |
|---|---|
| GET /api/health (ping) | $O(N_{net})$ — latenza di rete |
| GET /api/auth/verify | $O(N_{net} + D)$ — rete + lookup DB |
| JWT decode (server-side) | $O(1)$ — decodifica HMAC costante |
| localStorage read + parse | $O(H)$ — proporzionale allo storico |
| **Totale** | $O(N_{net} + D + H)$ |

Il costo è dominato dalla latenza di rete. L'operazione di verifica JWT è a costo costante ($O(1)$) poiché HMAC-SHA256 opera su payload di dimensione fissa. Il ripristino della conversazione è $O(H)$ ma avviene una sola volta all'avvio.

---

## 4. Persistenza della Conversazione — Architettura

```
                     +-------------------+
                     |   React State     |
                     |  (conversation[]) |
                     +--------+----------+
                              |
                   onChange    |    onMount
                     ↓        ↓       ↓
              +------+--------+-------+------+
              |       localStorage           |
              | key: conversation_{matricola}|
              | value: JSON array            |
              +------------------------------+
                              |
                   ogni richiesta
                     ↓
              +------+--------+------+
              |  POST /api/agent/query|
              |  conversation_history |
              |  (ultimi 10 messaggi) |
              +----------------------+
```

### Scelte progettuali

- **Client-side storage**: la conversazione è salvata in `localStorage`, non nel database, per semplicità e privacy
- **Finestra mobile**: solo gli ultimi 10 messaggi vengono inviati al server, evitando prompt troppo lunghi
- **Persistenza per utente**: la chiave è `conversation_{matricola}`, ogni utente ha il proprio storico
- **Pulizia al logout**: il `localStorage` viene svuotato al logout per sicurezza
