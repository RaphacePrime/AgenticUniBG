# Requisiti Funzionali e Non Funzionali - Iterazione 2

---

## Introduzione

L'Iterazione 2 estende il sistema MVP dell'Iterazione 1 introducendo **autenticazione utente**, **registrazione**, **persistenza su MongoDB** e **personalizzazione delle risposte** in base al profilo dello studente. Il frontend diventa una SPA React completa con pagina di login e interfaccia chat.

---

## Requisiti Funzionali

### Template Use Case

- **ID**: Identificatore univoco
- **Nome**: Nome del caso d'uso
- **Descrizione**: Breve descrizione della funzionalità
- **Attori**: Chi interagisce con il sistema
- **Precondizioni**: Condizioni necessarie prima dell'esecuzione
- **Flusso Principale**: Sequenza di passi
- **Flussi Alternativi**: Variazioni e casi d'errore
- **Postcondizioni**: Stato del sistema dopo l'esecuzione
- **Priorità**: Alta / Media / Bassa

---

### UC-01: Registrazione Studente

- **ID**: UC-01
- **Nome**: Registrazione Studente
- **Descrizione**: Permette a un nuovo studente di creare un account nel sistema fornendo i propri dati anagrafici e accademici.
- **Attori**: Studente
- **Precondizioni**: Lo studente non è ancora registrato nel sistema.
- **Flusso Principale**:
  1. Lo studente seleziona "Registrazione" nel frontend.
  2. Il sistema mostra il form con i campi: nome, cognome, matricola, password, dipartimento, corso, tipologia, anno.
  3. Lo studente compila e invia il form.
  4. Il frontend invia `POST /api/auth/register` con i dati.
  5. Il backend verifica che la matricola non sia già registrata.
  6. Il backend hasha la password con bcrypt e salva il documento su MongoDB.
  7. Il sistema restituisce il profilo dello studente registrato.
  8. Il frontend mostra l'interfaccia chat.
- **Flussi Alternativi**:
  - 5a. Matricola già registrata: il backend risponde con `409 Conflict`; il frontend mostra un messaggio di errore.
  - 3a. Campi obbligatori mancanti: il frontend blocca l'invio e segnala i campi vuoti.
- **Postcondizioni**: Il profilo dello studente è salvato su MongoDB; l'utente accede all'interfaccia chat.
- **Priorità**: Alta

---

### UC-02: Login Studente

- **ID**: UC-02
- **Nome**: Login Studente
- **Descrizione**: Permette a uno studente registrato di autenticarsi e accedere alle funzionalità personalizzate.
- **Attori**: Studente
- **Precondizioni**: Lo studente è già registrato nel sistema.
- **Flusso Principale**:
  1. Lo studente inserisce matricola e password nel form di login.
  2. Il frontend invia `POST /api/auth/login`.
  3. Il backend cerca il documento sulla collezione `users` tramite matricola.
  4. Il backend verifica la password con `bcrypt.checkpw`.
  5. Il sistema restituisce il profilo completo dello studente.
  6. Il frontend salva il profilo in memoria e mostra l'interfaccia chat.
- **Flussi Alternativi**:
  - 3a. Matricola non trovata: il backend risponde con `401 Unauthorized`.
  - 4a. Password errata: il backend risponde con `401 Unauthorized`.
- **Postcondizioni**: Il profilo dell'utente è disponibile nello stato React; l'utente accede alla chat.
- **Priorità**: Alta

---

### UC-04: Inviare Richiesta

- **ID**: UC-04
- **Nome**: Inviare Richiesta
- **Descrizione**: L'utente (autenticato o ospite) invia una domanda testuale al sistema.
- **Attori**: Utente (Studente o Ospite)
- **Precondizioni**: L'utente ha effettuato il login oppure ha scelto l'accesso come ospite.
- **Flusso Principale**:
  1. L'utente digita la domanda nell'interfaccia chat.
  2. Il frontend invia `POST /api/agent/query` con `query` e `user_info` (profilo).
  3. Il backend avvia la pipeline di elaborazione.
  4. La risposta viene restituita al frontend.
- **Flussi Alternativi**:
  - 2a. Query vuota: il frontend blocca l'invio.
  - 3a. Errore backend: il frontend mostra un messaggio di errore.
- **Postcondizioni**: La risposta viene aggiunta alla conversazione nel frontend.
- **Priorità**: Alta

---

### UC-05: Ricevere Risposta

- **ID**: UC-05
- **Nome**: Ricevere Risposta
- **Descrizione**: Il sistema elabora la query tramite la pipeline classify → generate → revise e restituisce la risposta finale.
- **Attori**: Sistema (OrchestratorAgent, ClassifierAgent, GeneratorAgent, RevisionAgent)
- **Precondizioni**: Una query è stata ricevuta via `POST /api/agent/query`.
- **Flusso Principale**:
  1. L'`OrchestratorAgent` inizializza l'`AgentState` con query e profilo utente.
  2. Il `ClassifierAgent` classifica l'intento.
  3. Il `GeneratorAgent` genera la risposta contestualizzata al profilo.
  4. Il `RevisionAgent` revisiona la risposta.
  5. La risposta finale viene restituita all'API Gateway.
- **Flussi Alternativi**:
  - 3a. Errore in generazione: viene propagato `status: "error"`.
  - 4a. Errore in revisione: viene usata la risposta bozza come fallback.
- **Postcondizioni**: La risposta finale è disponibile nel frontend.
- **Priorità**: Alta

---

### UC-06: Recupero Profilo

- **ID**: UC-06
- **Nome**: Recupero Profilo
- **Descrizione**: Dopo il login, il sistema recupera il profilo completo dello studente da MongoDB e lo rende disponibile per la personalizzazione delle risposte.
- **Attori**: Sistema (ProfileRepository)
- **Precondizioni**: Lo studente ha effettuato il login con credenziali valide.
- **Flusso Principale**:
  1. Il backend riceve le credenziali validate da `AuthService`.
  2. `ProfileRepository.findById(matricola)` interroga MongoDB.
  3. Il documento utente viene restituito senza il campo `passwordHash`.
  4. I dati del profilo sono inclusi nella risposta al frontend.
- **Flussi Alternativi**:
  - 2a. Documento non trovato: il backend risponde con `404 Not Found`.
- **Postcondizioni**: Il profilo è disponibile nel frontend per le richieste successive.
- **Priorità**: Alta

---

### UC-07: Risposta Personalizzata

- **ID**: UC-07
- **Nome**: Risposta Personalizzata
- **Descrizione**: Se l'utente è autenticato, la pipeline degli agenti utilizza le informazioni del profilo (corso, anno, dipartimento, tipologia) per generare una risposta pertinente al percorso specifico dello studente.
- **Attori**: Sistema (OrchestratorAgent, GeneratorAgent)
- **Precondizioni**: L'utente è autenticato e il profilo è stato recuperato (UC-06).
- **Flusso Principale**:
  1. L'`OrchestratorAgent` chiama `build_user_context(state)` con i dati del profilo.
  2. La stringa di contesto viene iniettata nel prompt del `ClassifierAgent` e del `GeneratorAgent`.
  3. L'LLM genera una risposta tenendo conto di corso, anno, dipartimento e tipologia.
- **Flussi Alternativi**:
  - 1a. Utente ospite: `build_user_context` restituisce un disclaimer generico; la risposta non è personalizzata.
- **Postcondizioni**: La risposta è contestualizzata al profilo dello studente.
- **Priorità**: Alta

---

## Requisiti Non Funzionali

### RNF-1 – Sicurezza delle Password
Le password devono essere salvate esclusivamente come hash bcrypt (salt incluso). Non devono mai essere salvate in chiaro né trasmesse nelle risposte API.

### RNF-2 – Persistenza
I dati degli studenti devono essere persistiti su MongoDB Atlas. La perdita di connessione al database deve restituire un errore gestito (`503 Service Unavailable`) senza esporre dettagli interni.

### RNF-3 – Separazione dei Dati
L'API non deve mai restituire il campo `passwordHash` nelle risposte. Il metodo `_public_profile` deve filtrare i campi sensibili prima di ogni risposta.

### RNF-4 – Tempo di Risposta
La pipeline classify → generate → revise deve completarsi entro **15 secondi** in condizioni normali (latenza LLM inclusa).

### RNF-5 – Disponibilità del Backend
Il backend deve essere disponibile e raggiungibile tramite l'endpoint `/api/health`. In caso di errore, l'endpoint deve rispondere con stato `200` solo se il servizio è operativo.

### RNF-6 – Containerizzazione
Il sistema deve essere deployabile tramite `docker-compose up` senza configurazione manuale. Frontend (Nginx) e backend (uvicorn) devono essere servizi separati.

### RNF-7 – CORS
Il middleware CORS deve essere configurato per accettare richieste solo dai domini esplicitamente autorizzati (in produzione). In sviluppo sono accettate le origini localhost.
