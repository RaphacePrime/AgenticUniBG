# Iterazione 0 – Visione Iniziale e Analisi Preliminare
---

# 1. Introduzione

## 1.1 Visione del Progetto

Agentic UniBG nasce con l’obiettivo di sviluppare un sistema intelligente multi-agent in grado di assistere studenti e utenti nella navigazione del sito universitario, in modo da ottenere in poco tempo una risposta a qualsiasi domanda adeguata al contesto. Il sito dell'università [unibg.it](www.unibg.it) presenta una struttura gerarchica complessa, informazioni distribuite su molte pagine, difficoltà nella ricerca di informazioni specifiche. Gli utenti devono navigare manualmente tra molte sezioni o consultare documenti lunghi per ricercare un'informazione singola, comportando perdite di tempo risolvibili. 

Il sistema è concepito come un assistente conversazionale avanzato, capace di:

- Comprendere richieste in linguaggio naturale
- Fornire risposte strutturate e contestualizzate
- Accedere a fonti informative interne ed esterne
- Personalizzare l’esperienza utente

L’idea iniziale prevede un’architettura modulare composta da agenti specializzati coordinati da un Orchestrator centrale.

---

# 2. Obiettivi Iniziali del Sistema

Il sistema, nella sua concezione iniziale, dovrebbe supportare:

- Autenticazione studenti
- Accesso ospiti
- Profilazione utente
- Recupero informazioni da database
- Recupero documenti
- Consultazione orari
- Consultazione occupazione aule
- Recupero informazioni corsi
- Guida passo-passo per procedure
- Sistema di feedback

Questa rappresenta la **visione completa target**, che potrà essere ridefinita o ridimensionata nelle iterazioni successive secondo approccio Agile + AMDD.

---

# 3. User Stories – Visione Iniziale

## US-01 – Accesso Studente
Come studente autenticato, voglio accedere al sistema con il mio profilo, in modo da ottenere risposte personalizzate

## US-02 – Accesso Ospite
Come visitatore esterno, voglio porre domande senza autenticazione, così da ottenere informazioni generali

## US-03 – Richiesta Informazione Corso
Come studente, voglio poter chiedere informazioni su un corso, in modo da ottenere dettagli aggiornati rapidamente

## US-04 – Consultazione Orari
Come studente, voglio conoscere l’orario delle lezioni, così posso organizzare la mia giornata

## US-05 – Verifica Aule
Come studente voglio sapere se un’aula è libera, affinchè io possa usarla per studiare

## US-06 – Recupero Documento
Come studente voglio trovare un regolamento o documento ufficiale così posso consultarlo senza cercare manualmente

## US-07 – Guida Procedurale
Come studente voglio essere guidato passo-passo in una procedura, così non commetto errori amministrativi

## US-08 – Persistenza Conversazione
Come studente autenticato voglio che il sistema ricordi le conversazioni precedenti, così da non dover ripetere le stesse informazioni

## US-09 – Feedback
Come utente voglio fornire un feedback sulla risposta, affinché il sistema possa migliorare

# 4. Analisi dei Requisiti

## 4.1 Requisiti Funzionali

Il sistema deve implementare i seguenti macro-casi d’uso:

- Autenticazione e registrazione studenti (UC-01, UC-02)
- Gestione profilo utente (UC-03)
- Accesso ospite (UC-04)
- Invio richiesta conversazionale (UC-05)
- Recupero informazioni specifiche (UC-06 → UC-11)
- Fornire risposta (UC-12)
- Raccolta feedback (UC-13)

---

## 4.2 Requisiti Non Funzionali

- Architettura modulare e scalabile
- Estensibilità degli agenti
- Separazione responsabilità
- Tempo di risposta accettabile
- Supporto utenti autenticati e ospiti
- Persistenza dati

---

# 5. Architettura Iniziale Proposta

## 5.1 Component Diagram – Visione Completa

L’architettura iniziale prevede:

### Frontend
- React Native App (comunicazione via REST `/api/v1` e WebSocket `/ws`)

### Backend (LangChain)
- API Gateway
- Orchestrator Agent (coordina tutti gli agenti tramite interfacce dedicate)
- Classifier Agent
- Profile Agent
- Memory Agent
- Web Agent
- Documents Agent
- Generator Agent
- Revision Agent
- Feedback Agent

### Persistence Layer
- **Student Profile DB** (SQL) — dati anagrafici e di profilo degli studenti
- **Q&A History DB** (NoSQL) — cronologia delle conversazioni

### Componenti Esterni
- **LLM Provider (Ollama)** — modello linguistico locale interrogato da Generator Agent e Revision Agent tramite interfaccia `LLM API`
- **Web / Internet** — sorgente esterna consultata dal Web Agent per recupero informazioni

---

## 5.2 Flusso di Interazione tra Agenti

Il flusso teorico completo prevede:

1. Il **Frontend** invia la richiesta all'**API Gateway** via REST o WebSocket.
2. L'**API Gateway** la inoltra all'**Orchestrator Agent**.
3. L'**Orchestrator** instrada la richiesta agli agenti specializzati nell'ordine opportuno:
   - **Classifier Agent** → classifica l'intento
   - **Profile Agent** → recupera il profilo da Student Profile DB (SQL)
   - **Memory Agent** → recupera la cronologia da Q&A History DB (NoSQL)
   - **Web Agent** → eventuale ricerca su Internet
   - **Documents Agent** → eventuale ricerca su documenti interni
   - **Generator Agent** → genera la risposta chiamando l'**LLM Provider (Ollama)**
   - **Revision Agent** → revisiona la bozza chiamando l'**LLM Provider (Ollama)**
   - **Feedback Agent** → raccoglie il feedback utente
4. La risposta finale risale all'**Orchestrator** e viene restituita al **Frontend**.

---

# 6. Use Case Diagram – Visione Completa

Il sistema supporta due tipologie di attori principali:

- **Studente** — utente autenticato con profilo personale
- **Ospite** — utente non autenticato con accesso limitato alle funzionalità generali

I macro-casi d'uso della visione completa sono:

| ID | Nome | Attore |
|----|------|--------|
| UC-01 | Login come Studente | Studente |
| UC-02 | Registrazione Studente | Studente |
| UC-03 | Accesso come Ospite | Ospite |
| UC-04 | Gestione Profilo | Studente |
| UC-05 | Inviare Domanda/Richiesta | Studente, Ospite |
| UC-06 | Richiedere Guida Procedurale | Studente |
| UC-07 | Recupero Documento Ufficiale | Studente |
| UC-08 | Informazioni su un Corso | Studente |
| UC-09 | Consultazione Orari Lezioni | Studente |
| UC-10 | Verifica Occupazione Aule | Studente |
| UC-11 | Informazioni Generali | Studente, Ospite |
| UC-12 | Ricevere Risposta | Studente, Ospite |
| UC-13 | Fornire Feedback | Studente, Ospite |

La descrizione dettagliata di ciascun caso d'uso (precondizioni, flusso principale, flussi alternativi, postcondizioni) è riportata nel file allegato:
`requisiti_funzionali.md`

---

# 7. Assunzioni Iniziali

- Il sistema utilizzerà LLM tramite framework LangChain
- L’Orchestrator coordina tutti gli agenti
- Gli agenti sono indipendenti e specializzati
- Le fonti dati sono accessibili tramite API o database interni
- Il sistema è progettato per evolvere iterativamente

---

# 8. Rischi Iniziali Identificati

- Complessità architetturale elevata
- Dipendenza da servizi LLM esterni
- Incertezza sulla qualità delle risposte generate

---

# 9. Strategia di Evoluzione (Approccio Agile + AMDD)

Data la complessità dell’idea iniziale, il team ha deciso di:

- Scomporre lo sviluppo in iterazioni incrementali
- Implementare inizialmente un "minimum viable product" ridotto
- Evolvere l’architettura progressivamente
- Aggiornare i modelli UML ad ogni iterazione

---