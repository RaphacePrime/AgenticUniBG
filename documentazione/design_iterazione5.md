# Design Document — Iterazione 5: Timestamp Temporale, Prompt Engineering, Gestione Profilo e Timing Logger

## 1. Obiettivo dell'iterazione

Consolidare la pipeline multi-agente con interventi trasversali: (1) **Timestamp Temporale** per la consapevolezza della data corrente da parte degli agenti, (2) **Prompt Engineering Estensivo** con revisione sistematica dei prompt di tutti gli agenti tramite test manuali iterativi, (3) **Gestione Profilo Utente** con nuova `SettingsPage` e due endpoint REST per modifica profilo e cambio password, (4) **Timing nel PipelineLogger** per il monitoraggio dei tempi di esecuzione per agente.

Il workflow LangGraph rimane strutturalmente invariato: `Classifier → QueryAgent → [WebSearch | ExamExtract] → Generator → Reviser`, con l'aggiunta del timestamp nei prompt e della sezione timing nel log.

---

## 2. Algoritmo 1: Iniezione Timestamp Temporale (get_italian_timestamp)

### 2.1 Descrizione

Gli LLM non hanno consapevolezza della data corrente. La funzione `get_italian_timestamp()` genera la data del server in formato italiano e viene iniettata nei system prompt di `QueryAgent` e `GeneratorAgent`, consentendo risposte temporalmente accurate (es. "prossima sessione", "scadenza imminente").

### 2.2 Pseudocodice

```
ALGORITHM GetItalianTimestamp()

INPUT:  (nessuno)
OUTPUT: data_string (stringa in formato "dd mese yyyy")

COSTANTI:
    MESI_ITALIANI ← ["gennaio", "febbraio", "marzo", "aprile",
                      "maggio", "giugno", "luglio", "agosto",
                      "settembre", "ottobre", "novembre", "dicembre"]

1.  now ← DATETIME.NOW()
2.  giorno ← FORMAT(now.day, "02d")       // es. "06"
3.  mese ← MESI_ITALIANI[now.month - 1]   // es. "marzo"
4.  anno ← now.year                         // es. 2026
5.  RETURN giorno + " " + mese + " " + anno
    // es. "06 marzo 2026"
```

### 2.3 Iniezione nei Prompt

```
ALGORITHM InjectTimestamp(system_prompt)

INPUT:  system_prompt (prompt di sistema dell'agente)
OUTPUT: system_prompt arricchito con data odierna

1.  today ← GetItalianTimestamp()
2.  timestamp_line ← "DATA ODIERNA: " + today + " (Anno accademico 2025/2026)"
3.  system_prompt ← system_prompt + "\n" + timestamp_line
4.  RETURN system_prompt
```

**Agenti che utilizzano il timestamp:**
- **QueryAgent**: per includere riferimenti temporali nelle search query (es. "sessione estiva 2026 unibg ingegneria").
- **GeneratorAgent**: per determinare il contesto temporale nella risposta (es. "la prossima sessione è...").
- **WebAgent** (`_format_exam_results`): per includere la data odierna nel contesto del calendario esami.

### 2.4 Analisi di Complessità

| Operazione | Complessità |
|---|---|
| `datetime.now()` | $O(1)$ — chiamata di sistema |
| Accesso array mesi | $O(1)$ — indice diretto |
| Formattazione stringa | $O(1)$ — lunghezza fissa |
| Concatenazione al prompt | $O(1)$ — append |
| **Totale** | $O(1)$ |

La funzione è deterministica, priva di effetti collaterali e non può fallire. L'overhead della doppia invocazione (QueryAgent + GeneratorAgent) è trascurabile.

---

## 3. Algoritmo 2: Prompt Engineering — SOURCE_INSTRUCTIONS e History Nativa

### 3.1 Descrizione

Il `GeneratorAgent` è stato arricchito con due meccanismi chiave: (1) un blocco `SOURCE_INSTRUCTIONS` che viene aggiunto al system prompt quando il contesto web è disponibile, con 8 regole per l'uso corretto delle fonti; (2) l'iniezione della `conversation_history` come messaggi LLM nativi (`HumanMessage` / `AIMessage`) anziché come stringa testuale nel prompt.

### 3.2 Pseudocodice — Costruzione Prompt con Fonti

```
ALGORITHM BuildGeneratorPrompt(query, category, context, user_context, history)

INPUT:  query (stringa), category (stringa), context (dict con web_context),
        user_context (stringa dal profilo), history (lista messaggi)
OUTPUT: messages (lista di messaggi LLM pronti per l'invocazione)

COSTANTI:
    CATEGORY_PROMPTS ← {
        "informazioni_corso": "Sei un assistente per i corsi UniBG...",
        "orari": "Aiuta lo studente a trovare orari...",
        "date_esami": "L'utente chiede informazioni su DATE ESAMI...
                       REGOLE CRITICHE: cerca le date nel calendario...
                       non esporre metadati interni...",
        "procedure": "Guida lo studente nelle procedure...",
        "servizi": "Informa lo studente sui servizi...",
        "generale": "Rispondi alla domanda sull'Università di Bergamo...",
        "altro": "Gestisci domande non universitarie con cortesia..."
    }

    SOURCE_INSTRUCTIONS ← "
        REGOLE PER L'USO DEL CONTESTO WEB:
        1. Usa SOLO le informazioni dal contesto web fornito
        2. NON inventare informazioni non presenti nelle fonti
        3. NON modificare gli URL delle fonti
        4. Per ogni informazione chiave, cita la fonte
        5. In fondo, aggiungi 'Pagina di riferimento: [URL]'
        6. Se trovi link a PDF nelle fonti, citali come risorse utili
        7. Se le fonti non contengono info sufficienti, dì che
           non hai trovato dati specifici e suggerisci di consultare
           il sito ufficiale
        8. Il contesto web contiene un massimo di 5 risultati
    "

1.  // Costruzione system prompt base
    base_prompt ← CATEGORY_PROMPTS[category]

2.  // Iniezione timestamp
    today ← GetItalianTimestamp()
    base_prompt += "\nDATA ODIERNA: " + today + " (Anno accademico 2025/2026)"

3.  // Iniezione contesto utente (se presente)
    IF user_context IS NOT EMPTY:
        base_prompt += "\n\nPROFILO STUDENTE:\n" + user_context

4.  // Iniezione SOURCE_INSTRUCTIONS (se web context disponibile)
    web_context ← context.get("web_context", "")
    IF web_context IS NOT EMPTY:
        base_prompt += "\n\n" + SOURCE_INSTRUCTIONS

5.  // Costruzione lista messaggi
    messages ← [SystemMessage(base_prompt)]

6.  // Iniezione history come messaggi nativi
    IF history IS NOT EMPTY:
        last_messages ← history[-6:]     // ultimi 3 turni (3 user + 3 assistant)
        FOR EACH msg IN last_messages:
            IF msg.role == "user":
                messages.append(HumanMessage(msg.content))
            ELSE IF msg.role == "assistant":
                messages.append(AIMessage(msg.content))

7.  // Messaggio utente finale con contesto web
    user_content ← "Domanda: " + query
    IF web_context IS NOT EMPTY:
        user_content += "\n\nCONTESTO WEB:\n" + web_context
    messages.append(HumanMessage(user_content))

8.  RETURN messages
```

### 3.3 Pseudocodice — Prompt RevisionAgent con Regole di Formato

```
ALGORITHM BuildRevisionPrompt(query, draft, category, user_context, history)

INPUT:  query (stringa), draft (risposta generata), category (stringa),
        user_context (stringa), history (lista messaggi)
OUTPUT: messages (lista di messaggi LLM)

COSTANTI:
    REVISION_SYSTEM_PROMPT ← "
        Sei un revisore esperto dell'Università di Bergamo.
        
        REGOLE DI FORMATO:
        - Testo semplice compatibile con tag <p> HTML
        - MAI usare Markdown (**, *, #, ```)
        - MAI usare emoji o caratteri speciali
        - Usa MAIUSCOLE per enfatizzare parole importanti
        
        LUNGHEZZA TARGET:
        - Risposte semplici: 1-3 frasi
        - Risposte articolate: max 10-15 punti
        - Date e scadenze NON vengono MAI compresse o rimosse
        
        PRIORITÀ ACCURATEZZA:
        - Le date, scadenze, URL e dati specifici NON vanno MAI rimossi
        - Preserva SEMPRE 'Pagina di riferimento: [URL]'
        - Non contraddire risposte precedenti nella conversazione
    "

1.  messages ← [SystemMessage(REVISION_SYSTEM_PROMPT)]

2.  // Aggiunta contesto conversazionale (ultimi 2 turni)
    IF history IS NOT EMPTY:
        last_4 ← history[-4:]
        FOR EACH msg IN last_4:
            IF msg.role == "user":
                messages.append(HumanMessage(msg.content))
            ELSE:
                messages.append(AIMessage(msg.content))

3.  // Messaggio con la bozza da revisionare
    user_message ← "Domanda originale: " + query + "\n"
    user_message += "Categoria: " + category + "\n"
    IF user_context IS NOT EMPTY:
        user_message += "Profilo studente: " + user_context + "\n"
    user_message += "\nRISPOSTA DA REVISIONARE:\n" + draft

    messages.append(HumanMessage(user_message))

4.  RETURN messages
```

### 3.4 Analisi di Complessità

Sia:
- $H$ = numero di messaggi nella history (max 6 usati dal Generator, max 4 dal Reviser)
- $W$ = dimensione del web_context in caratteri
- $P$ = dimensione del prompt di categoria

| Operazione | Complessità |
|---|---|
| Lookup CATEGORY_PROMPTS | $O(1)$ — dizionario |
| GetItalianTimestamp() | $O(1)$ |
| Concatenazione user_context | $O(|user\_context|)$ |
| Concatenazione SOURCE_INSTRUCTIONS | $O(1)$ — stringa costante |
| Costruzione messaggi history | $O(H)$ = $O(1)$ con $H \leq 6$ |
| Costruzione messaggio utente con web_context | $O(W)$ |
| **Totale GeneratorAgent** | $O(W)$ |
| **Totale RevisionAgent** | $O(|draft|)$ |

La complessità è dominata dalla dimensione del contenuto testuale (web context o draft da revisionare), che è già limitato a 5 risultati web dal WebAgent.

**Vantaggio dell'history come messaggi nativi**: il modello LLM gestisce nativamente la sequenza di messaggi multi-turno, producendo risposte più coerenti nei follow-up rispetto all'approccio testuale "STORICO CONVERSAZIONE:\n..." dell'Iterazione 4.

---

## 4. Algoritmo 3: Gestione Profilo Utente (UpdateProfile + ChangePassword)

### 4.1 Descrizione

Due nuovi flussi backend consentono la modifica del profilo e il cambio password. Entrambi richiedono autenticazione JWT e operano direttamente su MongoDB tramite il `ProfileRepository`.

### 4.2 Pseudocodice — Modifica Profilo

```
ALGORITHM UpdateProfile(jwt_token, update_fields)

INPUT:  jwt_token (stringa dal cookie httpOnly),
        update_fields (dict con campi opzionali: name, surname, department, course, tipology, year)
OUTPUT: public_profile (dict senza passwordHash)

1.  // Estrazione matricola dal JWT
    payload ← JWTManager.validateToken(jwt_token)
    IF payload IS NULL:
        RAISE HTTPException(401, "Token non valido")
    matricola ← payload.sub

2.  // Verifica esistenza utente
    user ← ProfileRepository.findById(matricola)
    IF user IS NULL:
        RAISE HTTPException(404, "Utente non trovato")

3.  // Filtro campi validi (rimuove campi None)
    valid_fields ← {}
    FOR EACH (key, value) IN update_fields:
        IF value IS NOT NULL AND key IN ["name", "surname", "department",
                                          "course", "tipology", "year"]:
            valid_fields[key] ← value

4.  // Aggiornamento atomico su MongoDB
    ProfileRepository.updateProfile(matricola, valid_fields)
    // → db.users.update_one({"matricola": matricola}, {"$set": valid_fields})

5.  // Recupero profilo aggiornato
    updated_user ← ProfileRepository.findById(matricola)

6.  // Rimozione campo sensibile
    public_profile ← COPY(updated_user)
    DELETE public_profile["passwordHash"]
    DELETE public_profile["_id"]

7.  RETURN public_profile
```

### 4.3 Pseudocodice — Cambio Password

```
ALGORITHM ChangePassword(jwt_token, current_password, new_password)

INPUT:  jwt_token (stringa dal cookie httpOnly),
        current_password (stringa), new_password (stringa)
OUTPUT: success_message (dict)

1.  // Estrazione matricola dal JWT
    payload ← JWTManager.validateToken(jwt_token)
    IF payload IS NULL:
        RAISE HTTPException(401, "Token non valido")
    matricola ← payload.sub

2.  // Recupero utente
    user ← ProfileRepository.findById(matricola)
    IF user IS NULL:
        RAISE HTTPException(404, "Utente non trovato")

3.  // Verifica password corrente
    is_valid ← bcrypt.checkpw(
        current_password.encode("utf-8"),
        user["passwordHash"].encode("utf-8")
    )
    IF NOT is_valid:
        RAISE HTTPException(401, "Password corrente non corretta")

4.  // Hash nuova password
    salt ← bcrypt.gensalt()
    new_hash ← bcrypt.hashpw(new_password.encode("utf-8"), salt)

5.  // Aggiornamento su MongoDB
    ProfileRepository.updateProfile(matricola, {"passwordHash": new_hash.decode("utf-8")})

6.  RETURN { status: "success", message: "Password aggiornata con successo" }
```

### 4.4 Analisi di Complessità

Sia:
- $V$ = numero di campi nel body della richiesta (max 6)

**UpdateProfile:**

| Operazione | Complessità |
|---|---|
| Validazione JWT | $O(1)$ — decodifica token |
| findById (MongoDB) | $O(1)$ — lookup per chiave primaria |
| Filtro campi validi | $O(V)$ = $O(1)$ con $V \leq 6$ |
| update_one (MongoDB) | $O(1)$ — aggiornamento per chiave primaria |
| findById (recupero) | $O(1)$ |
| **Totale** | $O(1)$ |

**ChangePassword:**

| Operazione | Complessità |
|---|---|
| Validazione JWT | $O(1)$ |
| findById (MongoDB) | $O(1)$ |
| bcrypt.checkpw | $O(B)$ — $B$ = fattore di costo bcrypt (tipicamente 12 round) |
| bcrypt.hashpw | $O(B)$ |
| update_one (MongoDB) | $O(1)$ |
| **Totale** | $O(B)$ |

Il costo dominante del cambio password è il double hashing bcrypt (~100ms per round 12), che è intenzionale come misura di sicurezza.

---

## 5. Algoritmo 4: Timing nel PipelineLogger (_format_timing_section)

### 5.1 Descrizione

Ogni nodo del workflow LangGraph misura il proprio tempo di esecuzione tramite `time.time()`. Il PipelineLogger raccoglie i dati di timing da `workflow_steps` e produce una sezione formattata nel log con etichette leggibili e tempo totale.

### 5.2 Pseudocodice

```
ALGORITHM FormatTimingSection(workflow_steps, total_time)

INPUT:  workflow_steps (lista di dict con campo elapsed_time),
        total_time (float, tempo totale pipeline in secondi)
OUTPUT: lines (lista di stringhe formattate)

COSTANTI:
    STEP_LABELS ← {
        "classification": "Classifier Agent",
        "query_generation": "Query Agent",
        "web_search": "Web Agent",
        "exam_extract": "Web Agent (Exam Extract)",
        "generation": "Generator Agent",
        "revision": "Revision Agent"
    }

1.  lines ← []
    lines.append("─" * 60)
    lines.append("TEMPI DI ESECUZIONE")
    lines.append("─" * 60)

2.  FOR EACH step IN workflow_steps:
        step_name ← step.get("step", "unknown")
        elapsed ← step.get("elapsed_time", 0.0)
        label ← STEP_LABELS.get(step_name, step_name)
        // Formattazione allineata
        lines.append("  " + LJUST(label, 25) + ": " + FORMAT(elapsed, ".3f") + "s")

3.  lines.append("")
    lines.append("  " + LJUST("TEMPO TOTALE", 25) + ": " + FORMAT(total_time, ".3f") + "s")

4.  RETURN lines
```

### 5.3 Raccolta dei Tempi nel Workflow

```
ALGORITHM CollectTiming(node_function, step_name, agent_name)

INPUT:  node_function (funzione del nodo da eseguire),
        step_name (identificatore dello step),
        agent_name (nome dell'agente)
OUTPUT: state aggiornato con elapsed_time nello step

1.  start ← time.time()
2.  result ← node_function(state)     // esecuzione agente
3.  elapsed ← time.time() - start

4.  state["workflow_steps"].append({
        "step": step_name,
        "agent": agent_name,
        "result": result,
        "elapsed_time": elapsed
    })

5.  RETURN state
```

### 5.4 Esempio di Output

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

### 5.5 Analisi di Complessità

Sia:
- $S$ = numero di step nel workflow (costante, $S = 5$)

| Operazione | Complessità |
|---|---|
| `time.time()` per step (2 × S chiamate) | $O(S)$ = $O(1)$ |
| Iterazione su workflow_steps | $O(S)$ = $O(1)$ |
| Lookup STEP_LABELS | $O(1)$ — dizionario |
| Formattazione stringa per step | $O(1)$ |
| **Totale** | $O(1)$ |

L'overhead introdotto dal timing è strettamente $O(1)$ e non introduce latenza misurabile nella pipeline. Le chiamate `time.time()` sono operazioni di sistema con costo nell'ordine dei nanosecondi.

---

## 6. Algoritmo 5: Selezione Gerarchica Dipartimento-Corso (Frontend)

### 6.1 Descrizione

La `SettingsPage` implementa una selezione a cascata: la scelta del dipartimento filtra i corsi disponibili, la scelta del corso determina automaticamente la tipologia, e la tipologia determina l'anno massimo.

### 6.2 Pseudocodice

```
ALGORITHM HandleDepartmentCourseSelection(selectedDepartment, selectedCourse)

INPUT:  selectedDepartment (stringa), selectedCourse (stringa opzionale)
OUTPUT: profileData aggiornato (dict con department, course, tipology, year)

COSTANTI:
    DIPARTIMENTI_CORSI ← {
        "Scuola di Ingegneria": [
            { nome: "Ingegneria informatica", tipo: "Laurea" },
            { nome: "Ingegneria informatica", tipo: "Laurea Magistrale" },
            ...
        ],
        "Dipartimento di Giurisprudenza": [
            { nome: "Giurisprudenza", tipo: "Laurea Magistrale a ciclo unico (5 anni)" },
            ...
        ],
        ...
    }

    TIPO_TO_TIPOLOGY ← {
        "Laurea" → "Triennale",
        "Laurea Magistrale" → "Magistrale",
        "Laurea Magistrale a ciclo unico (5 anni)" → "Ciclo Unico"
    }

    TIPOLOGY_TO_MAX_YEAR ← {
        "Triennale" → 3,
        "Magistrale" → 2,
        "Ciclo Unico" → 5
    }

1.  // Cambio dipartimento
    IF selectedDepartment IS CHANGED:
        profileData.department ← selectedDepartment
        profileData.course ← ""          // Reset corso
        profileData.tipology ← ""        // Reset tipologia
        profileData.year ← 1             // Reset anno

2.  // Cambio corso
    IF selectedCourse IS NOT EMPTY:
        availableCourses ← DIPARTIMENTI_CORSI[selectedDepartment]
        matchedCourse ← FIND(availableCourses, c → c.nome == selectedCourse)

        IF matchedCourse IS NOT NULL:
            profileData.course ← matchedCourse.nome
            profileData.tipology ← TIPO_TO_TIPOLOGY[matchedCourse.tipo]
            profileData.year ← 1          // Reset anno al cambio corso

3.  // Calcolo anno massimo per il dropdown
    maxYear ← TIPOLOGY_TO_MAX_YEAR[profileData.tipology] OR 3
    yearOptions ← [1, 2, ..., maxYear]

4.  RETURN profileData, yearOptions
```

### 6.3 Analisi di Complessità

Sia:
- $D$ = numero di dipartimenti (costante, ~8)
- $C$ = numero di corsi per dipartimento (max ~10)

| Operazione | Complessità |
|---|---|
| Lookup dipartimento | $O(1)$ — chiave dict |
| Ricerca corso nel dipartimento | $O(C)$ — scansione lineare |
| Lookup tipologia | $O(1)$ — chiave dict |
| Calcolo anno massimo | $O(1)$ — chiave dict |
| **Totale** | $O(C)$ = $O(1)$ con $C \leq 10$ |

---

## 7. Workflow Completo dell'Iterazione 5

```
                    ┌──────────┐
                    │ CLASSIFY │
                    │ (+ hist) │
                    └────┬─────┘
                         │
                    ┌────┴─────┐
                    │  QUERY   │
                    │  AGENT   │
                    │ (+ TS)   │
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
              │ (+ TS)    │ │           │
              └─────┬─────┘ └─────┬─────┘
                    │             │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  GENERATOR  │
                    │ (+ TS +    │
                    │  SOURCES + │
                    │  native H) │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │   REVISER   │
                    │ (+ format  │
                    │   rules)   │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │   LOGGER   │
                    │ (+ timing) │
                    └─────────────┘

Legenda:
  TS = Timestamp (get_italian_timestamp())
  hist = Conversation History per classificazione
  native H = History come HumanMessage/AIMessage
  SOURCES = SOURCE_INSTRUCTIONS per fonti web
  format rules = Regole no-Markdown, lunghezza target
  timing = _format_timing_section() nel log
```

### 7.1 Flusso Parallelo: Impostazioni Profilo

```
    ┌──────────┐
    │  BROWSER │
    │  (⚙ btn) │
    └────┬─────┘
         │
    ┌────┴──────────┐
    │ SETTINGS PAGE │
    └──┬─────────┬──┘
       │         │
       ▼         ▼
  ┌─────────┐ ┌───────────┐
  │ UPDATE  │ │  CHANGE   │
  │ PROFILE │ │ PASSWORD  │
  └────┬────┘ └─────┬─────┘
       │            │
       ▼            ▼
  ┌─────────┐ ┌───────────┐
  │ Auth    │ │ Auth      │
  │ Service │ │ Service   │
  │ update  │ │ changePwd │
  └────┬────┘ └─────┬─────┘
       │            │
       ▼            ▼
  ┌────────────────────┐
  │   MongoDB Atlas    │
  │   (profiles)       │
  └────────────────────┘
```
