# Requisiti Funzionali e Non Funzionali - Iterazione 4

---

## Introduzione

L'Iterazione 4 estende la pipeline agente con due nuovi nodi LangGraph: **QueryAgent** (ottimizzazione delle keyword di ricerca) e **WebAgent** (ricerca web su dominio `unibg.it` tramite Tavily API). Viene introdotto il **PipelineLogger** per tracciabilità diagnostica. Il modello LLM viene sostituito con **Google Gemini 2.5 Flash**. Tutti i requisiti delle iterazioni precedenti rimangono validi.

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

### UC-01 – UC-10 *(confermati dall'Iterazione 3)*

Tutti i use case UC-01 (Registrazione), UC-02 (Login), UC-04 (Invia Richiesta), UC-05 (Ricevi Risposta), UC-06 (Recupero Profilo), UC-07 (Risposta Personalizzata), UC-08 (Ripristino Sessione), UC-09 (Logout Sicuro) e UC-10 (Richiesta Contestuale) rimangono validi e invariati rispetto all'Iterazione 3.

---

### UC-11: Risposta con Dati Reali da UniBG

- **ID**: UC-11
- **Nome**: Risposta con Dati Reali da UniBG
- **Descrizione**: Il sistema arricchisce ogni risposta con contenuti estratti in tempo reale dal sito ufficiale dell'Università di Bergamo (`unibg.it`), tramite una pipeline che ottimizza la query, esegue ricerca web e inietta il contesto estratto nel prompt del generatore.
- **Attori**: Utente (innescato automaticamente dalla pipeline ad ogni query)
- **Precondizioni**: L'utente ha inviato una query tramite UC-04. La variabile d'ambiente `TAVILY_API_KEY` è configurata.
- **Flusso Principale**:
  1. La query dell'utente entra nel nodo `classify` dell'`OrchestratorAgent`.
  2. Il `ClassifierAgent` categorizza la domanda e produce `search_query` di base.
  3. Il controllo passa al nodo `query`.
  4. `QueryAgent.generate_query()` invoca Gemini per riformulare la query in **6-8 keyword ottimizzate** per motori di ricerca.
  5. Il `QueryAgent` decide autonomamente se includere il profilo studente nelle keyword (es. corsi specifici: sì; servizi generici: no).
  6. Il controllo passa al nodo `web_search`.
  7. `WebAgent.search(optimized_query)` chiama la Tavily API con i parametri: `search_depth="advanced"`, `include_domains=["unibg.it","unibg.coursecatalogue.cineca.it"]`, `max_results=30`.
  8. Il `WebAgent` ordina i risultati per score e seleziona i **top 5**.
  9. Per ogni risultato con URL che termina in `.pdf`, `WebAgent._extract_pdf_links()` estrae i link dal PDF tramite PyMuPDF.
  10. I risultati vengono formattati in `web_context` e iniettati nello stato.
  11. Il controllo passa al nodo `generate`.
  12. Il `GeneratorAgent` include `web_context` nel prompt per produrre una risposta ancorata a dati reali.
  13. Il nodo `revise` esegue il controllo qualità.
  14. `PipelineLogger.write_log()` scrive il log della pipeline nel file `logs/log_{matricola}_{timestamp}.txt`.
  15. La risposta finale viene restituita all'utente.
- **Flussi Alternativi**:
  - 4a. Errore nella generazione della query ottimizzata: il `QueryAgent` usa la query originale come fallback.
  - 7a. Errore API Tavily o nessun risultato: `web_context` è vuoto; il `GeneratorAgent` procede senza dati web, basandosi solo sulla knowledge interna.
  - 9a. PyMuPDF non disponibile o PDF inaccessibile: il link PDF viene saltato silenziosamente.
  - 14a. Errore di scrittura del log: l'errore viene ingoiato silenziosamente; la risposta non è bloccata.
- **Postcondizioni**: L'utente riceve una risposta arricchita con dati reali da `unibg.it`; il log della pipeline è salvato su disco.
- **Priorità**: Alta

---

### UC-12: Logging della Pipeline

- **ID**: UC-12
- **Nome**: Logging Diagnostico della Pipeline
- **Descrizione**: Ogni esecuzione della pipeline multi-agente genera un file di log strutturato che traccia input/output di ogni nodo per fini diagnostici e di audit.
- **Attori**: Sistema (automatico)
- **Precondizioni**: La pipeline è stata eseguita per rispondere a una query.
- **Flusso Principale**:
  1. Al termine di `workflow.ainvoke()`, l'`OrchestratorAgent` chiama `PipelineLogger.write_log(state)`.
  2. Il `PipelineLogger` crea la directory `logs/` se non esiste.
  3. Il filename viene generato come `log_{matricola}_{YYYYMMDD_HHMMSS_ffffff}.txt`.
  4. Il logger scrive le sezioni: Header, User Info, Original Query, Conversation History, Step1-Classifier, Step2-QueryAgent, Step3-WebAgent, Step4-Generator, Step5-Reviser.
  5. Il file viene chiuso.
- **Flussi Alternativi**:
  - Qualsiasi eccezione: l'errore è ingoiato silenziosamente tramite `try/except`.
- **Postcondizioni**: Un file di log strutturato è disponibile nella directory `logs/`.
- **Priorità**: Media

---

## Requisiti Non Funzionali

### RNF-1 – Accuratezza della Ricerca Web
La ricerca Tavily deve essere limitata ai domini `unibg.it` e `unibg.coursecatalogue.cineca.it` per garantire che i dati provengano da fonti ufficiali dell'ateneo.

### RNF-2 – Latenza della Ricerca Web
La fase di web search (`WebAgent.search()`) non deve superare **10 secondi**. La pipeline complessiva (dalla query alla risposta) deve completarsi entro **30 secondi**.

### RNF-3 – Fallback della Pipeline
In caso di fallimento di qualsiasi nodo intermedio (QueryAgent, WebAgent), la pipeline deve continuare con i dati disponibili senza sollevare eccezioni verso l'utente. La risposta finale deve essere sempre prodotta.

### RNF-4 – Gestione PDF
L'estrazione di link da PDF tramite PyMuPDF deve essere non bloccante. Se la libreria non è installata o il PDF non è accessibile, il risultato viene silenziosamente ignorato. PyMuPDF è una dipendenza opzionale.

### RNF-5 – Logging Non Bloccante
La scrittura del log su file non deve mai bloccare la restituzione della risposta all'utente. Qualsiasi errore I/O nel logger deve essere catturato e ignorato.

### RNF-6 – Struttura del Log
Ogni file di log deve contenere tutte le sezioni della pipeline (Header, User Info, Query, History, Step 1-5). Il nome del file deve includere matricola e timestamp con microsecondo per unicità garantita.

### RNF-7 – Context Window LLM
Google Gemini 2.5 Flash supporta fino a **1 milione di token**. Il `web_context` iniettato nel prompt del `GeneratorAgent` deve essere limitato ai top 5 risultati per evitare superamento pratico della finestra e contenimento dei costi API.

### RNF-8 – Ottimizzazione Query
Il `QueryAgent` deve produrre keyword compatte (6-8 termini) per massimizzare la rilevanza dei risultati Tavily e minimizzare i costi API. L'inclusione del profilo studente nelle keyword deve essere una decisione autonoma del modello, non hardcodata.

### RNF-9 – Sostituzione LLM
Il passaggio da Groq `llama-3.3-70b` a Google Gemini 2.5 Flash deve essere trasparente per tutti gli agenti: nessuno dei nodi pipeline deve contenere riferimenti hardcodati al modello. Il modello è iniettato dall'`OrchestratorAgent` come dependency.

### RNF-10 – Retention dei Log
I file di log nella directory `logs/` devono essere conservati per un periodo minimo di 30 giorni. La directory `logs/` non deve essere inclusa nel repository git (aggiungere a `.gitignore`).

### RNF-11 – Sicurezza e Sessione *(ereditati dall'Iterazione 3)*
Tutti i requisiti di sicurezza JWT (RNF-1 through RNF-8 dell'Iterazione 3) rimangono validi e vincolanti.
