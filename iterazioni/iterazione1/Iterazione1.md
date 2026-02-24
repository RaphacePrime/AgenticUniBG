# Iterazione 1

## 1. Obiettivo dell'Iterazione
L'obiettivo dell'Iterazione 1 è realizzare un primo **Minimum Viable Product (MVP)** funzionante del sistema multi-agent, limitato alle seguenti fasi:

* **Input Management**: Gestione dell'input utente.
* **Intent Classification**: Classificazione della richiesta tramite **Classifier Agent**.
* **Response Generation**: Generazione della risposta tramite **Generator Agent** e **LLM Provider** esterno.
* **Review**: Revisione della risposta tramite **Revision Agent**.
* **Output**: Restituzione del risultato finale all'utente.

---

## 2. Obiettivo dell'Incremento

### User Stories incluse
* **US-10 – Invio Richiesta**: *As a* utente, voglio inviare una richiesta testuale *so that* ricevo una risposta dal sistema.
* **US-11 – Classificazione Intento**: *As a* sistema, voglio classificare la richiesta *so that* posso generare una risposta coerente.
* **US-12 – Generazione Risposta**: *As a* sistema, voglio generare una risposta tramite **LLM** *so that* l'utente riceva una risposta pertinente.
* **US-13 – Revisione Risposta**: *As a* sistema, voglio verificare la qualità della risposta *so that* riduco errori o incoerenze.

---

## 3. Architettura Implementata

### Componenti Sviluppati
* **Client** (Frontend minimale)
* **Web Server** (con interfaccia HTTP)
* **App Server** (con interfaccia BusinessLogic)
* **Orchestrator Agent**
* **Classifier Agent**
* **Generator Agent**
* **Revision Agent**
* **Database** (con interfaccia JDBC/SQL)

L'architettura è organizzata in tre tier:
- **Client Tier**: interfaccia utente minimale.
- **Application Logic Tier**: Web Server e App Server che ospitano la logica degli agenti.
- **Data Tier**: Database per la persistenza dei dati.

---

## 4. Design – Algoritmi Rilevanti

### 4.1 Classificazione
Algoritmo semplificato per il **routing** delle richieste:
1. Ricezione **User Input**.
2. Invio di un **Prompt Template** strutturato al modello.
3. Output: **Intent Label** (categoria).

**Pseudo-flow:**
`User Input` → `Prompt Template` → `LLM` → `Intent Label`

### 4.2 Pipeline di Generazione
`User Input` → `Classifier Agent` → `Generator Agent` → `Revision Agent` → `Orchestrator Agent` → `Utente`

---

## 5. Analisi Dinamica
Il flusso, come descritto nel Sequence Diagram, è il seguente:

1. L'utente invia la **query** all'**Orchestrator Agent**.
2. L'**Orchestrator** invia la query al **Classifier Agent** per la classificazione.
3. Il **Classifier Agent** restituisce la **classificazione** all'**Orchestrator**.
4. L'**Orchestrator** invoca il **Generator Agent** passando query e classificazione.
5. Il **Generator Agent** produce la bozza di risposta e la restituisce all'**Orchestrator**.
6. L'**Orchestrator** invia la bozza al **Revision Agent** per la revisione.
7. Il **Revision Agent** restituisce la **risposta revisionata** all'**Orchestrator**.
8. L'**Orchestrator** restituisce la risposta finale all'**Utente**.

---

## 6. Analisi Statica
Struttura delle classi e relazioni principali (come da Class Diagram):

* **OrchestratorAgent**: Coordina l'esecuzione dei vari agenti. Contiene riferimenti a `ClassifierAgent`, `GeneratorAgent` e `RevisionAgent`. Espone il metodo `handleQuery(query: String): String`.
* **ClassifierAgent**: Espone il metodo `classify(query: String): String`.
* **GeneratorAgent**: Espone il metodo `generate(query: String, classification: String): String`.
* **RevisionAgent**: Espone il metodo `revise(draft: String): String`.
* **AgentState**: Mantiene lo stato condiviso della pipeline, contenente `query`, `classification`, `generatedResponse` e `finalResponse`. Ha una dipendenza verso `OrchestratorAgent`.

---

## 7. Testing

### 7.1 Test Funzionali
* Richieste generiche.
* Richiesta informazione corso.
* Richiesta non riconosciuta.

### 7.2 Test di Robustezza
* Gestione di **input** vuoti o ambigui.
* Gestione di **input** con lunghezza eccessiva.

### 7.3 Risultati
Il sistema dimostra una corretta classificazione degli intenti semplici e una generazione coerente entro tempi di latenza accettabili.

---

## 8. Limitazioni dell'Iterazione 1
* Nessun accesso a dati reali.
* Nessuna personalizzazione del profilo utente.
* Possibili allucinazioni tipiche degli **LLM** non vincolati a documenti.
* Architettura a tre tier semplificata: funzionalità avanzate degli agenti (es. memoria, ricerca web, documenti) rimandate alle iterazioni successive.
