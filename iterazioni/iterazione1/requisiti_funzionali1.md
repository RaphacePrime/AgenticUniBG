# Requisiti Funzionali e Non Funzionali - Iterazione 1

---

## Introduzione

Questa iterazione implementa il **Minimum Viable Product (MVP)** del sistema ad agenti. Il focus è esclusivamente sulla pipeline conversazionale: ricezione della domanda, classificazione dell'intento, generazione e revisione della risposta. Non è prevista autenticazione, persistenza su database né personalizzazione utente.

---

## Requisiti Funzionali

### Template Use Case

Ogni use case è descritto secondo il seguente template:

- **ID**: Identificatore univoco
- **Nome**: Nome del caso d'uso
- **Attori**: Chi interagisce con il sistema
- **Precondizioni**: Condizioni necessarie prima dell'esecuzione
- **Flusso Principale**: Sequenza di passi
- **Flussi Alternativi**: Variazioni e casi d'errore
- **Postcondizioni**: Stato del sistema dopo l'esecuzione
- **Priorità**: Alta / Media / Bassa

---

### UC-I1: Invio Richiesta

- **ID**: UC-I1
- **Nome**: Invio Richiesta
- **Descrizione**: L'utente invia una domanda testuale al sistema tramite l'interfaccia frontend.
- **Attori**: Utente
- **Precondizioni**: Il frontend è raggiungibile e il backend è in esecuzione.
- **Flusso Principale**:
  1. L'utente apre l'interfaccia web.
  2. L'utente digita una domanda nel campo di input.
  3. L'utente invia il messaggio (invio o bottone).
  4. Il frontend invia la query al backend tramite `POST /api/agent/query`.
  5. Il sistema elabora la richiesta e restituisce la risposta.
  6. Il frontend visualizza la risposta all'utente.
- **Flussi Alternativi**:
  - 3a. La query è vuota: il frontend non invia la richiesta.
  - 5a. Il backend restituisce un errore: il frontend mostra un messaggio di errore generico.
- **Postcondizioni**: L'utente visualizza la risposta generata dal sistema.
- **Priorità**: Alta

---

### UC-I2: Classificazione Intento

- **ID**: UC-I2
- **Nome**: Classificazione Intento
- **Descrizione**: Il `ClassifierAgent` analizza la query e la assegna a una categoria semantica (es. `informazioni_corso`, `orari`, `procedure`, `servizi`, `generale`).
- **Attori**: Sistema (ClassifierAgent)
- **Precondizioni**: La query è stata ricevuta dall'OrchestratorAgent.
- **Flusso Principale**:
  1. L'`OrchestratorAgent` passa la query al `ClassifierAgent`.
  2. Il `ClassifierAgent` invia un prompt strutturato all'LLM.
  3. L'LLM restituisce la categoria e il livello di confidence.
  4. L'`OrchestratorAgent` memorizza categoria e confidence nello stato.
- **Flussi Alternativi**:
  - 3a. L'LLM restituisce una categoria non riconosciuta: viene usata la categoria `altro` come fallback.
  - 2a. Timeout LLM: il sistema propaga un errore nello stato (`status: "error"`).
- **Postcondizioni**: Lo stato contiene `category`, `category_description`, `confidence`.
- **Priorità**: Alta

---

### UC-I3: Generazione Risposta

- **ID**: UC-I3
- **Nome**: Generazione Risposta
- **Descrizione**: Il `GeneratorAgent` produce una risposta alla domanda dell'utente, sfruttando la categoria classificata e un prompt ottimizzato.
- **Attori**: Sistema (GeneratorAgent)
- **Precondizioni**: La classificazione è stata completata con successo.
- **Flusso Principale**:
  1. L'`OrchestratorAgent` passa query e categoria al `GeneratorAgent`.
  2. Il `GeneratorAgent` costruisce un prompt contestualizzato per categoria.
  3. L'LLM genera la risposta.
  4. La bozza viene salvata nello stato come `generated_response`.
- **Flussi Alternativi**:
  - 3a. Errore LLM: il sistema registra l'errore e propaga `status: "error"`.
- **Postcondizioni**: Lo stato contiene `generated_response` e `generation_status`.
- **Priorità**: Alta

---

### UC-I4: Revisione Risposta

- **ID**: UC-I4
- **Nome**: Revisione Risposta
- **Descrizione**: Il `RevisionAgent` rivede la bozza generata per correggere imprecisioni, migliorare chiarezza e verificare la coerenza con la domanda originale.
- **Attori**: Sistema (RevisionAgent)
- **Precondizioni**: La generazione è completata e `generated_response` è presente nello stato.
- **Flusso Principale**:
  1. L'`OrchestratorAgent` passa query originale, bozza e categoria al `RevisionAgent`.
  2. Il `RevisionAgent` invia un prompt di revisione all'LLM.
  3. L'LLM restituisce la risposta revisionata e segnala se ha apportato modifiche.
  4. La risposta finale viene salvata nello stato come `final_response`.
- **Flussi Alternativi**:
  - 3a. Errore LLM in revisione: viene usata la `generated_response` come `final_response` (fallback graceful).
- **Postcondizioni**: Lo stato contiene `final_response` e `has_revisions`.
- **Priorità**: Alta

---

## Requisiti Non Funzionali

### RNF-I1 – Tempo di Risposta
Il sistema deve restituire una risposta all'utente entro **10 secondi** dalla ricezione della query, in condizioni normali di carico.

### RNF-I2 – Modularità
Ogni agente (`ClassifierAgent`, `GeneratorAgent`, `RevisionAgent`) deve essere indipendente dal punto di vista del codice, con responsabilità ben separate. L'aggiunta o la sostituzione di un agente non deve richiedere modifiche agli altri.

### RNF-I3 – Robustezza della Pipeline
Il fallimento di un singolo agente non deve interrompere il sistema. In caso di errore nel `RevisionAgent`, la risposta bozza del `GeneratorAgent` deve essere comunque restituita all'utente.

### RNF-I4 – Statelessness
In questa iterazione il sistema è completamente stateless: non memorizza nulla tra una richiesta e l'altra. Ogni chiamata è indipendente.

### RNF-I5 – Estensibilità
L'architettura basata su LangGraph deve permettere l'aggiunta di nuovi nodi (agenti) al workflow senza modificare la logica esistente.

### RNF-I6 – Documentazione API
Il backend espone una documentazione OpenAPI automatica (Swagger UI) tramite FastAPI accessibile a `/docs`.
