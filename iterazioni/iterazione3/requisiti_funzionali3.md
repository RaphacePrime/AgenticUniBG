# Requisiti Funzionali e Non Funzionali - Iterazione 3

---

## Introduzione

L'Iterazione 3 introduce la **gestione sicura della sessione tramite JWT httpOnly cookie**, il **ripristino automatico della sessione al ricaricamento della pagina**, il **logout sicuro** e la **memoria conversazionale** basata su `localStorage`. I requisiti funzionali delle iterazioni precedenti sono confermati e arricchiti.

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

### UC-01: Registrazione Studente *(confermato)*

- **ID**: UC-01
- **Nome**: Registrazione Studente
- **Descrizione**: Permette a un nuovo studente di creare un account. In questa iterazione, al termine della registrazione viene generato un JWT e impostato come httpOnly cookie.
- **Attori**: Studente
- **Precondizioni**: Lo studente non è ancora registrato.
- **Flusso Principale**:
  1. Lo studente compila il form di registrazione.
  2. Il frontend invia `POST /api/auth/register`.
  3. Il backend valida l'unicità della matricola tramite `ProfileRepository.exists()`.
  4. Il backend hasha la password con bcrypt e salva il documento su MongoDB.
  5. `JWTManager.generateToken({ matricola, status: "loggato" })` genera il token.
  6. `AuthController._set_auth_cookie()` imposta il cookie httpOnly `access_token`.
  7. Il backend restituisce il profilo pubblico (senza `passwordHash`).
  8. Il frontend salva il profilo in memoria e mostra la chat.
- **Flussi Alternativi**:
  - 3a. Matricola già registrata: `409 Conflict`.
  - 1a. Campi obbligatori mancanti: il frontend blocca l'invio.
- **Postcondizioni**: Profilo salvato su MongoDB; cookie JWT impostato nel browser.
- **Priorità**: Alta

---

### UC-02: Login Studente *(aggiornato)*

- **ID**: UC-02
- **Nome**: Login Studente
- **Descrizione**: Autentica uno studente e imposta il JWT come httpOnly cookie per la gestione della sessione.
- **Attori**: Studente
- **Precondizioni**: Lo studente è registrato nel sistema.
- **Flusso Principale**:
  1. Lo studente inserisce matricola e password.
  2. Il frontend invia `POST /api/auth/login`.
  3. `AuthService.authenticate()` verifica le credenziali tramite bcrypt.
  4. `JWTManager.generateToken()` genera il token JWT (scadenza 7 giorni).
  5. `AuthController._set_auth_cookie()` imposta `access_token` come httpOnly cookie.
  6. Il backend restituisce il profilo pubblico.
  7. Il frontend salva il profilo e carica la conversazione da `localStorage`.
- **Flussi Alternativi**:
  - 3a. Credenziali errate: `401 Unauthorized`.
- **Postcondizioni**: Cookie JWT impostato; profilo in memoria; conversazione precedente ripristinata.
- **Priorità**: Alta

---

### UC-08: Ripristino Sessione Automatica

- **ID**: UC-08
- **Nome**: Ripristino Sessione Automatica
- **Descrizione**: Al caricamento o ricaricamento dell'applicazione, il sistema verifica automaticamente la validità del cookie JWT e ripristina la sessione senza richiedere un nuovo login.
- **Attori**: Utente (Studente)
- **Precondizioni**: Il browser contiene un cookie `access_token` valido.
- **Flusso Principale**:
  1. Il browser carica l'applicazione React.
  2. Il frontend esegue `GET /api/auth/verify` con `credentials: "include"`.
  3. Il backend chiama `JWTManager.validateFromRequest(request)` per estrarre e validare il cookie.
  4. Il backend decodifica il payload e recupera la matricola.
  5. `ProfileRepository.findById(matricola)` recupera il profilo da MongoDB.
  6. Il backend restituisce il profilo completo.
  7. Il frontend imposta `isAuthenticated = true` e carica la conversazione da `localStorage`.
- **Flussi Alternativi**:
  - 2a. Cookie assente: il frontend mostra la pagina di login.
  - 3a. Token scaduto o invalido: `401 Unauthorized`; il frontend mostra la pagina di login.
  - 5a. Profilo non trovato in MongoDB: `404 Not Found`; il frontend mostra la pagina di login.
- **Postcondizioni**: La sessione è ripristinata e la conversazione precedente è disponibile.
- **Priorità**: Alta

---

### UC-09: Logout Sicuro

- **ID**: UC-09
- **Nome**: Logout Sicuro
- **Descrizione**: L'utente termina la sessione in modo sicuro: il cookie JWT viene eliminato lato server e la conversazione viene rimossa dal `localStorage`.
- **Attori**: Studente
- **Precondizioni**: L'utente è autenticato (cookie JWT presente).
- **Flusso Principale**:
  1. L'utente clicca sul pulsante di logout.
  2. Il frontend invia `POST /api/auth/logout` con `credentials: "include"`.
  3. Il backend esegue `response.delete_cookie("access_token")`.
  4. Il backend risponde con `{ status: "success", message: "Logout effettuato" }`.
  5. Il frontend cancella il profilo dallo stato React (`setUserInfo(null)`).
  6. Il frontend imposta `isAuthenticated = false`.
  7. Il frontend rimuove la conversazione da `localStorage`.
  8. Il frontend reindirizza alla pagina di login.
- **Flussi Alternativi**:
  - 2a. Errore di rete: il frontend esegue comunque il cleanup locale (passi 5-8).
- **Postcondizioni**: Cookie eliminato; profilo e conversazione rimossi; utente reindirizzato al login.
- **Priorità**: Alta

---

### UC-10: Richiesta Contestuale (con History)

- **ID**: UC-10
- **Nome**: Richiesta Contestuale con Memoria Conversazionale
- **Descrizione**: Ogni query inviata al sistema include gli ultimi messaggi della conversazione come contesto, permettendo agli agenti di generare risposte coerenti con il filo del dialogo.
- **Attori**: Utente
- **Precondizioni**: L'utente ha già inviato almeno un messaggio precedente nella sessione corrente.
- **Flusso Principale**:
  1. L'utente digita una nuova domanda.
  2. Il frontend filtra i messaggi di tipo `user` e `agent` dalla conversazione corrente.
  3. Il frontend seleziona gli ultimi 10 messaggi (5 turni) e li converte in `{ role, content }`.
  4. Il frontend invia `POST /api/agent/query` con `query`, `user_info` e `conversation_history`.
  5. L'`OrchestratorAgent` popola `AgentState.conversation_history`.
  6. `ClassifierAgent`, `GeneratorAgent` e `RevisionAgent` ricevono la history nei loro prompt.
  7. La risposta generata è coerente con il contesto della conversazione.
  8. La risposta viene aggiunta alla UI e la conversazione aggiornata viene salvata in `localStorage`.
- **Flussi Alternativi**:
  - 1a. Prima domanda della sessione: `conversation_history` è un array vuoto; la pipeline funziona normalmente.
- **Postcondizioni**: La risposta tiene conto del contesto conversazionale; `localStorage` è aggiornato.
- **Priorità**: Alta

---

### UC-04 – UC-07 *(confermati dall'Iterazione 2)*

I use case UC-04 (Inviare Richiesta), UC-05 (Ricevere Risposta), UC-06 (Recupero Profilo) e UC-07 (Risposta Personalizzata) rimangono validi e invariati rispetto all'Iterazione 2.

---

## Requisiti Non Funzionali

### RNF-1 – Sicurezza del Token JWT
Il token JWT deve essere trasmesso esclusivamente tramite cookie httpOnly, inaccessibile da JavaScript del frontend. L'attributo `SameSite=lax` deve essere impostato per protezione CSRF di base.

### RNF-2 – Scadenza della Sessione
Il token JWT deve avere una scadenza configurabile (default: 7 giorni). Alla scadenza, il sistema deve restituire `401 Unauthorized` e il frontend deve reindirizzare al login senza errori visibili all'utente.

### RNF-3 – Persistenza Locale della Conversazione
La cronologia delle conversazioni deve essere persistita in `localStorage` con chiave univoca per utente (`conversation_{matricola}`). Il frontend deve caricarla automaticamente al ripristino della sessione.

### RNF-4 – Pulizia Dati al Logout
Al logout, tutti i dati locali dell'utente (profilo in memoria, conversazione in `localStorage`) devono essere rimossi. Questa operazione deve avvenire anche in caso di errore di rete.

### RNF-5 – Limitazione del Contesto Conversazionale
La `conversation_history` trasmessa al backend deve contenere al massimo **10 messaggi** (5 turni) per evitare superamento del context window del modello LLM.

### RNF-6 – CORS Ristretto
`allow_origins=["*"]` non è più accettabile. Le origini autorizzate devono essere elencate esplicitamente. `allow_credentials=True` è obbligatorio per la trasmissione dei cookie.

### RNF-7 – Refactoring Layer Autenticazione
Il codice di autenticazione deve essere organizzato nel pacchetto `auth/` con separazione netta tra `JWTManager`, `AuthService`, `AuthController` e `ProfileRepository`. Nessuna logica di autenticazione deve risiedere in `main.py`.

### RNF-8 – Tempo di Risposta
Il ripristino della sessione (`/api/auth/verify`) deve completarsi entro **2 secondi**. La pipeline di query deve completarsi entro **15 secondi**.
