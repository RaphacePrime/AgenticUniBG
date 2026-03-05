# Analisi Statica — Report Metriche del Codice

## 1. Introduzione

L'analisi statica del codebase AgenticUniBG è stata condotta utilizzando **radon** (Python) per il calcolo di:
- **Complessità Ciclomatica** (McCabe) — misura la complessità decisionale del codice
- **Indice di Manutenibilità** (Maintainability Index) — stima della facilità di manutenzione
- **Metriche Raw** (LOC, SLOC, commenti) — conteggio linee di codice
- **Metriche di Halstead** — misure basate su operatori e operandi

### Strumenti utilizzati
- `radon cc` — Cyclomatic Complexity
- `radon mi` — Maintainability Index
- `radon raw` — Raw metrics (LOC)
- `radon hal` — Halstead metrics

---

## 2. Complessità Ciclomatica (McCabe)

La complessità ciclomatica misura il numero di cammini lineari indipendenti nel codice. I gradi sono:

| Grado | CC | Rischio |
|---|---|---|
| **A** | 1–5 | Basso, semplice |
| **B** | 6–10 | Medio, moderatamente complesso |
| **C** | 11–15 | Alto, complesso |
| **D** | 16–20 | Molto alto |
| **F** | 21+ | Ingestibile |

### 2.1 Riepilogo per file

| File | Grado Max | Funzione Più Complessa | CC |
|---|---|---|---|
| `agents/orchestrator_agent.py` | A | `_generate_node` | 4 |
| `agents/classifier_agent.py` | B | `classify` | 6 |
| `agents/generator_agent.py` | B | `generate` | 6 |
| `agents/query_agent.py` | B | `generate_query` | 6 |
| `agents/revision_agent.py` | B | `revise` | 6 |
| `agents/web_agent.py` | **C** | `_select_calendar_link` | **11** |
| `agents/agent_state.py` | A | `build_user_context` | 2 |
| `auth/controller.py` | A | Tutte le funzioni | 1 |
| `auth/service.py` | A | `authenticate` | 3 |
| `auth/jwt_manager.py` | A | `__init__` | 2 |
| `auth/profile_repository.py` | A | `updateProfile` | 4 |
| `logger/pipeline_logger.py` | B | `_build_log_content` | 8 |
| `models/user.py` | A | Tutte | 1 |
| `main.py` | A | `verify_auth` | 3 |
| `config.py` | A | `Settings` | 1 |

### 2.2 Distribuzione per grado

| Grado | N. blocchi | Percentuale |
|---|---|---|
| A (1–5) | 93 | 90.3% |
| B (6–10) | 9 | 8.7% |
| C (11–15) | 1 | 1.0% |
| D/F (16+) | 0 | 0.0% |
| **Totale** | **103** | **100%** |

**Media complessità: A (2.37)**

### 2.3 Funzioni a complessità più alta

| Funzione | File | CC | Grado | Note |
|---|---|---|---|---|
| `WebAgent._select_calendar_link` | web_agent.py | 11 | C | Parsing risposta LLM, fallback multipli |
| `PipelineLogger._build_log_content` | pipeline_logger.py | 8 | B | Formattazione log con molte sezioni |
| `WebAgent._extract_pdf_links` | web_agent.py | 7 | B | Estrazione link da PDF con gestione errori |
| `ClassifierAgent.classify` | classifier_agent.py | 6 | B | Costruzione contesto + validazione |
| `GeneratorAgent.generate` | generator_agent.py | 6 | B | Gestione contesto e invocazione LLM |
| `QueryAgent.generate_query` | query_agent.py | 6 | B | Costruzione prompt con storico |
| `RevisionAgent.revise` | revision_agent.py | 6 | B | Costruzione prompt di revisione |
| `WebAgent._format_results` | web_agent.py | 6 | B | Formattazione con check PDF |

### 2.4 Osservazioni

- **Punto critico**: `WebAgent._select_calendar_link` (CC=11, grado C) è la funzione più complessa del sistema. La complessità è dovuta alla costruzione dinamica delle opzioni, all'invocazione LLM per la scelta e al parsing multi-pattern della risposta con fallback. Un possibile refactoring potrebbe estrarre il parsing in una funzione separata.
- **Layer Auth**: tutti i metodi del layer di autenticazione hanno complessità A (1–3), indicando un design pulito con responsabilità ben separate (Controller → Service → Repository).
- **Agenti**: i metodi principali degli agenti (classify, generate, revise, generate_query) hanno tutti complessità B (6), dovuta alla gestione del contesto conversazionale e alla costruzione dei prompt. Questa è una complessità strutturale intrinseca al dominio.

---

## 3. Indice di Manutenibilità

L'indice di manutenibilità (MI) è una metrica composita calcolata su: volume di Halstead, complessità ciclomatica e LOC. Scala 0–100, dove valori più alti indicano codice più manutenibile.

| Grado | MI | Interpretazione |
|---|---|---|
| **A** | 20–100 | Alta manutenibilità |
| **B** | 10–19 | Moderata |
| **C** | 0–9 | Bassa manutenibilità |

### 3.1 Risultati per file

| File | MI | Grado | Valutazione |
|---|---|---|---|
| `agents/__init__.py` | 100.00 | A | Eccellente |
| `auth/controller.py` | 100.00 | A | Eccellente |
| `auth/__init__.py` | 100.00 | A | Eccellente |
| `logger/__init__.py` | 100.00 | A | Eccellente |
| `models/__init__.py` | 100.00 | A | Eccellente |
| `models/user.py` | 100.00 | A | Eccellente |
| `config.py` | 100.00 | A | Eccellente |
| `db.py` | 100.00 | A | Eccellente |
| `auth/jwt_manager.py` | 86.28 | A | Molto buono |
| `agents/agent_state.py` | 84.86 | A | Molto buono |
| `auth/profile_repository.py` | 81.33 | A | Molto buono |
| `auth/service.py` | 80.09 | A | Molto buono |
| `agents/query_agent.py` | 75.73 | A | Buono |
| `agents/classifier_agent.py` | 73.03 | A | Buono |
| `agents/generator_agent.py` | 72.44 | A | Buono |
| `agents/revision_agent.py` | 71.59 | A | Buono |
| `main.py` | 64.17 | A | Accettabile |
| `agents/orchestrator_agent.py` | 56.60 | A | Accettabile |
| `agents/web_agent.py` | 52.21 | A | Accettabile |
| `logger/pipeline_logger.py` | 51.85 | A | Accettabile |

### 3.2 Osservazioni

- **Tutti i file hanno grado A** (MI > 20), indicando alta manutenibilità dell'intero codebase.
- I file con MI più basso (~52–56: `web_agent.py`, `pipeline_logger.py`, `orchestrator_agent.py`) sono i più complessi ma restano ampiamente nel range "buono".
- Il layer Auth ha MI eccellente (80–100), confermando la qualità del design a livelli separati.
- Il file `main.py` (MI=64) potrebbe beneficiare dall'estrazione di route handlers in moduli separati.

---

## 4. Metriche Raw (LOC)

### 4.1 Riepilogo generale

| Metrica | Valore |
|---|---|
| **LOC** (righe totali) | 2423 |
| **LLOC** (righe logiche) | 1217 |
| **SLOC** (righe di codice sorgente) | 1655 |
| **Commenti** | 120 |
| **Righe vuote** | 383 |
| **Commenti multi-linea** | 272 |
| **Rapporto commenti/LOC** | 5% |
| **Rapporto (commenti + multi)/LOC** | 16% |

### 4.2 Dettaglio per modulo

| Modulo | LOC | SLOC | Commenti | Commenti % |
|---|---|---|---|---|
| `agents/` (7 file) | 1408 | 1000 | 83 | 6% |
| `auth/` (5 file) | 327 | 194 | 4 | 1% |
| `logger/` (2 file) | 350 | 243 | 22 | 6% |
| `models/` (2 file) | 69 | 43 | 0 | 0% |
| `main.py` | 224 | 153 | 5 | 2% |
| `config.py` + `db.py` | 45 | 22 | 6 | 13% |
| **Totale** | **2423** | **1655** | **120** | **5%** |

### 4.3 Distribuzione LOC per modulo

```
agents/       ████████████████████████████████████  58.1%
logger/       ██████████████                        14.4%
auth/         █████████████                         13.5%
main.py       █████████                              9.2%
models/       ██                                     2.8%
config+db     █                                      1.9%
```

### 4.4 File più grandi

| File | LOC | SLOC |
|---|---|---|
| `agents/orchestrator_agent.py` | 437 | 307 |
| `agents/web_agent.py` | 398 | 282 |
| `logger/pipeline_logger.py` | 343 | 241 |
| `main.py` | 224 | 153 |
| `agents/revision_agent.py` | 131 | 96 |
| `agents/generator_agent.py` | 128 | 89 |
| `agents/query_agent.py` | 123 | 89 |

---

## 5. Riepilogo e Raccomandazioni

### 5.1 Punti di forza
- **Complessità bassa**: media CC = 2.37 (grado A), solo 1 funzione su 103 in grado C
- **Alta manutenibilità**: tutti i file in grado A (MI > 20), media ~80
- **Design pulito del layer Auth**: separazione Controller → Service → Repository con CC ≤ 3
- **Codebase compatto**: 2423 LOC totali, ben organizzato in moduli coesi

### 5.2 Aree di miglioramento
| Area | File | Problema | Suggerimento |
|---|---|---|---|
| Complessità | `web_agent.py` (`_select_calendar_link`, CC=11) | Troppa logica in un singolo metodo | Estrarre il parsing della risposta LLM in un metodo dedicato |
| Commenti | `auth/`, `models/` | Basso rapporto commenti/codice (0–1%) | Aggiungere docstring ai metodi del repository |
| LOC | `orchestrator_agent.py` (437 LOC) | File lungo con molti nodi | Considerare l'estrazione dei nodi del workflow in file separati |
| Duplicazione | `LoginPage.jsx`, `SettingsPage.jsx` | `DIPARTIMENTI_CORSI` duplicato | Estrarre in un file condiviso `constants.js` |
