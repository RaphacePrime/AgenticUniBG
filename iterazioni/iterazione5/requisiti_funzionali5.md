# Requisiti Funzionali e Non Funzionali - Iterazione 5

---

## Introduzione

L'Iterazione 5 consolida e raffina la pipeline multi-agente con interventi trasversali: **timestamp temporale** per la consapevolezza della data corrente negli agenti, **prompt engineering estensivo** con test manuali iterativi su tutti i prompt, **pagina impostazioni profilo** (`SettingsPage`) per la modifica dei dati personali e della password, e **tempi di esecuzione nel PipelineLogger** per il monitoraggio delle performance. Due nuovi endpoint REST (`PUT /api/auth/profile`, `PUT /api/auth/password`) supportano le operazioni di aggiornamento profilo. Tutti i requisiti delle iterazioni precedenti rimangono validi.

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

### UC-01 – UC-13 _(confermati dall'Iterazione 4)_

Tutti i use case UC-01 (Registrazione), UC-02 (Login), UC-04 (Invia Richiesta), UC-05 (Ricevi Risposta), UC-06 (Recupero Profilo), UC-07 (Risposta Personalizzata), UC-08 (Ripristino Sessione), UC-09 (Logout Sicuro), UC-10 (Richiesta Contestuale), UC-11 (Risposta con Dati Reali da UniBG), UC-12 (Logging della Pipeline) e UC-13 (Risposta su Date Esami con Calendario Ufficiale) rimangono validi e invariati rispetto all'Iterazione 4.

---

### UC-14: Modifica Profilo Utente

- **ID**: UC-14
- **Nome**: Modifica Profilo Utente
- **Descrizione**: L'utente autenticato può modificare i propri dati personali (nome, cognome, dipartimento, corso di laurea, anno) tramite la pagina impostazioni, senza necessità di re-registrazione.
- **Attori**: Utente autenticato
- **Precondizioni**: L'utente è autenticato (JWT valido nel cookie). L'utente ha effettuato il login (UC-02).
- **Flusso Principale**:
  1. L'utente clicca il pulsante ⚙ (impostazioni) nell'header della chat.
  2. Si apre il pannello `SettingsPage` come overlay.
  3. Il form "Dati Profilo" è precompilato con i dati correnti dell'utente.
  4. L'utente modifica uno o più campi:
     - **Nome** e **Cognome**: campi di testo libero.
     - **Dipartimento**: dropdown con tutti i dipartimenti dell'Università di Bergamo (da `DIPARTIMENTI_CORSI`).
     - **Corso di Laurea**: dropdown filtrato dai corsi del dipartimento selezionato.
     - **Tipologia**: campo auto-impostato in base al tipo del corso selezionato (Triennale, Magistrale, Ciclo Unico).
     - **Anno**: dropdown con range 1-N dove N dipende dalla tipologia (3, 2 o 5).
  5. L'utente clicca "Salva Modifiche".
  6. Il frontend invia `PUT /api/auth/profile` con i campi modificati e il cookie JWT.
  7. Il backend estrae la matricola dal token JWT.
  8. `AuthController.update_profile()` delega ad `AuthService.updateProfile()`.
  9. `AuthService` verifica l'esistenza dell'utente su MongoDB e chiama `ProfileRepository.updateProfile()`.
  10. `ProfileRepository` esegue `update_one` con `$set` dei campi forniti.
  11. Il backend restituisce il profilo aggiornato (senza `passwordHash`).
  12. Il frontend aggiorna `userInfo` nello stato React tramite la callback `onProfileUpdate`.
  13. Un messaggio di successo ("Profilo aggiornato con successo!") viene mostrato nel pannello.
  14. Tutte le successive query invieranno il profilo aggiornato agli agenti.
- **Flussi Alternativi**:
  - 6a. Token JWT scaduto o invalido: il backend risponde con `401 Unauthorized`; il frontend mostra il messaggio di errore.
  - 9a. Utente non trovato in MongoDB: il backend risponde con `404 Not Found`.
  - 5a. L'utente non ha modificato alcun campo: il frontend invia comunque la richiesta; MongoDB esegue un update idempotente.
  - 4a. L'utente cambia dipartimento: il campo corso viene resettato; il dropdown mostra solo i corsi del nuovo dipartimento.
  - 4b. L'utente seleziona un corso: la tipologia viene impostata automaticamente; l'anno viene resettato a 1.
- **Postcondizioni**: I dati del profilo utente sono aggiornati su MongoDB. Lo stato React dell'applicazione riflette le modifiche. Gli agenti riceveranno il profilo aggiornato nelle query successive.
- **Priorità**: Alta

---

### UC-15: Cambio Password

- **ID**: UC-15
- **Nome**: Cambio Password
- **Descrizione**: L'utente autenticato può cambiare la propria password dalla pagina impostazioni, fornendo la password corrente come verifica e la nuova password desiderata.
- **Attori**: Utente autenticato
- **Precondizioni**: L'utente è autenticato (JWT valido nel cookie). L'utente conosce la propria password corrente.
- **Flusso Principale**:
  1. L'utente apre la pagina impostazioni (⚙).
  2. L'utente compila il form "Cambia Password":
     - **Password Corrente**: campo password.
     - **Nuova Password**: campo password (minimo 6 caratteri).
     - **Conferma Nuova Password**: campo password.
  3. Il frontend valida localmente:
     - Tutti i campi sono compilati.
     - La nuova password ha almeno 6 caratteri.
     - La nuova password e la conferma coincidono.
  4. Il frontend invia `PUT /api/auth/password` con `current_password` e `new_password` e il cookie JWT.
  5. Il backend estrae la matricola dal token JWT.
  6. `AuthController.change_password()` delega ad `AuthService.changePassword()`.
  7. `AuthService` recupera il profilo utente da MongoDB.
  8. `AuthService` verifica la password corrente con `bcrypt.checkpw()`.
  9. La nuova password viene hashata con `bcrypt.hashpw()`.
  10. Il nuovo hash viene aggiornato su MongoDB.
  11. Il backend restituisce `{ status: "success", message: "Password aggiornata con successo" }`.
  12. Il frontend mostra il messaggio di successo e resetta i campi password.
- **Flussi Alternativi**:
  - 3a. Validazione locale fallita: il frontend mostra il messaggio d'errore appropriato; nessuna richiesta al backend.
  - 8a. Password corrente errata: `bcrypt.checkpw()` restituisce `False`; il backend risponde con `401 Unauthorized` e messaggio "Password corrente non corretta"; il frontend mostra l'errore.
  - 7a. Utente non trovato: il backend risponde con `404 Not Found`.
  - 4a. Token JWT scaduto: il backend risponde con `401 Unauthorized`.
- **Postcondizioni**: La password dell'utente è aggiornata su MongoDB con il nuovo hash bcrypt. La sessione JWT resta attiva (il token non viene invalidato). Le prossime autenticazioni useranno la nuova password.
- **Priorità**: Alta

---

### UC-16: Risposta Temporalmente Consapevole

- **ID**: UC-16
- **Nome**: Risposta Temporalmente Consapevole
- **Descrizione**: Il sistema inietta automaticamente la data corrente in formato italiano nei prompt di sistema degli agenti, consentendo risposte temporalmente accurate su sessioni, scadenze e periodi accademici.
- **Attori**: Sistema (automatico, trasparente per l'utente)
- **Precondizioni**: L'utente ha inviato una query tramite UC-04.
- **Flusso Principale**:
  1. La pipeline viene attivata dal `OrchestratorAgent`.
  2. Al nodo `query`, il `QueryAgent` invoca `get_italian_timestamp()` che restituisce la data corrente in formato italiano (es. "06 marzo 2026").
  3. Il system prompt del `QueryAgent` include: `DATA ODIERNA: {today} (Anno accademico 2025/2026)`.
  4. Il `QueryAgent` produce una search query che include riferimenti temporali se la domanda riguarda date o sessioni (es. "sessione estiva 2026").
  5. Al nodo `generate`, il `GeneratorAgent` invoca nuovamente `get_italian_timestamp()`.
  6. Il system prompt del `GeneratorAgent` include: `DATA ODIERNA: {today} (Anno accademico 2025/2026)`.
  7. Il `GeneratorAgent` può determinare "prossima sessione", "scadenza imminente", "periodo corrente" basandosi sulla data iniettata.
  8. Il nodo `exam_extract` (se attivato) include la data odierna nel contesto formattato del calendario esami per permettere al generatore di posizionare le date nel tempo.
- **Flussi Alternativi**:
  - Nessuno. La funzione `get_italian_timestamp()` non può fallire (usa `datetime.now()` di Python).
- **Postcondizioni**: La risposta contiene riferimenti temporali coerenti con la data reale.
- **Priorità**: Media

---

## Requisiti Non Funzionali

### RNF-1 – RNF-13 _(confermati dall'Iterazione 4)_

Tutti i requisiti non funzionali dell'Iterazione 4 rimangono validi e vincolanti.

---

### RNF-14 – Validazione Lato Client dei Dati Profilo

La `SettingsPage` deve validare localmente che i campi dipartimento/corso siano selezionati dal dizionario `DIPARTIMENTI_CORSI`. La tipologia deve essere derivata automaticamente dal tipo del corso selezionato e non editabile manualmente. L'anno massimo deve essere calcolato in base alla tipologia (Triennale: 3, Magistrale: 2, Ciclo Unico: 5).

### RNF-15 – Sicurezza Cambio Password

Il cambio password deve sempre richiedere la verifica della password corrente tramite `bcrypt.checkpw()` prima di accettare la nuova password. La nuova password deve essere hashata con `bcrypt.hashpw()` e `bcrypt.gensalt()` prima della persistenza. La lunghezza minima della password è di 6 caratteri (validata sia lato client sia lato server).

### RNF-16 – Idempotenza della Modifica Profilo

L'endpoint `PUT /api/auth/profile` deve essere idempotente: inviare gli stessi dati più volte produce lo stesso risultato senza effetti collaterali. Solo i campi presenti nel body vengono aggiornati (`$set` selettivo).

### RNF-17 – Precisione Temporale

La funzione `get_italian_timestamp()` deve restituire la data del server in formato "dd mese yyyy" con il nome del mese in italiano minuscolo. La precisione richiesta è al giorno (non ore/minuti). L'anno accademico deve essere hardcoded nel prompt e aggiornato manualmente ad ogni cambio di anno accademico.

### RNF-18 – Performance della Pipeline con Timing

La registrazione dei tempi di esecuzione (`time.time()`) non deve introdurre overhead misurabile nella pipeline. Il tempo totale della pipeline deve rimanere sotto i **30 secondi** (invariato da RNF-2).

### RNF-19 – Formato Log con Timing

La sezione "TEMPI DI ESECUZIONE" nel log deve riportare il tempo di ogni agente con 3 cifre decimali (secondi) e il tempo totale della pipeline. Gli step labels devono essere tradotti in etichette leggibili (es. `classification` → `Classifier Agent`).

### RNF-20 – Prompt Engineering — Regole di Formato

Tutte le risposte prodotte dal `RevisionAgent` devono essere in **testo semplice** compatibile con tag HTML `<p>`. Non è ammesso Markdown (`**`, `*`, `#`, `` ` ``), emoji o caratteri speciali di formattazione. L'enfasi è espressa esclusivamente tramite MAIUSCOLE.

### RNF-21 – Prompt Engineering — Priorità Contesto Conversazionale

Il `QueryAgent` e il `GeneratorAgent` devono dare **sempre** priorità al contesto della conversazione rispetto al profilo studente. Se la conversazione menziona un corso diverso dal profilo, la query e la risposta devono riferirsi al corso menzionato nella conversazione.

### RNF-22 – Prompt Engineering — Gestione Fonti Web

Quando il `GeneratorAgent` riceve `web_context`, deve seguire le `SOURCE_INSTRUCTIONS`: non inventare informazioni, non modificare URL, gestire link PDF estratti, e aggiungere in fondo "Pagina di riferimento: [URL]". Il `RevisionAgent` deve preservare gli URL in fondo alla risposta.
