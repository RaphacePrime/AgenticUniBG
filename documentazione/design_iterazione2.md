# Design Document — Iterazione 2: Registrazione, Login e Personalizzazione Risposte

## 1. Obiettivo dell'iterazione

Implementare il sistema di autenticazione (registrazione e login con bcrypt) e integrare le informazioni del profilo utente nell'`AgentState` per personalizzare le risposte degli agenti. Non è prevista memoria conversazionale in questa iterazione.

---

## 2. Algoritmo 1: Autenticazione con bcrypt (AuthService)

### 2.1 Descrizione

Il flusso di autenticazione implementa la verifica delle credenziali con hashing bcrypt (cost factor = 12 round di default). La password è protetta con hashing bcrypt. Il flusso è:
1. L'utente invia matricola + password
2. Il server cerca l'utente in MongoDB
3. Verifica la password con `bcrypt.checkpw()`
4. Se valida, restituisce il profilo dello studente

### 2.2 Pseudocodice

```
ALGORITHM Authenticate(matricola, password)

INPUT:  matricola (stringa), password (stringa)
OUTPUT: {student} oppure HTTPException 401

1.  // Lookup utente nel database
    student ← ProfileRepository.findById(matricola)
    IF student IS NULL:
        RAISE HTTPException(401, "Matricola non trovata")

2.  // Verifica password con bcrypt
    stored_hash ← student.passwordHash
    is_valid ← bcrypt.checkpw(password.encode("utf-8"),
                               stored_hash.encode("utf-8"))
    IF NOT is_valid:
        RAISE HTTPException(401, "Password errata")

3.  RETURN { student: student }
```

```
ALGORITHM Register(name, surname, matricola, password, department, course, tipology, year)

INPUT:  dati di registrazione completi
OUTPUT: {student} oppure HTTPException 409

1.  // Verifica unicità matricola
    IF ProfileRepository.exists(matricola):
        RAISE HTTPException(409, "Matricola già registrata")

2.  // Hash della password con bcrypt
    salt ← bcrypt.gensalt()    // 12 round di default
    hashed ← bcrypt.hashpw(password.encode("utf-8"), salt)

3.  // Salva il documento utente su MongoDB
    student_doc ← {
        name, surname, matricola,
        passwordHash: hashed.decode("utf-8"),
        department, course, tipology, year
    }
    saved ← ProfileRepository.save(student_doc)

4.  RETURN { student: saved }
```

### 2.3 Analisi di Complessità

Sia:
- $D$ = tempo di accesso al database MongoDB (query per chiave primaria)
- $B$ = tempo di esecuzione bcrypt (dipende dal cost factor, ~100ms per round 12)

| Operazione | Complessità |
|---|---|
| `findById(matricola)` — lookup per chiave indexed | $O(D)$ — $O(\log N)$ su B-tree MongoDB |
| `bcrypt.checkpw()` — verifica hash | $O(B)$ — costante, ~100ms |
| `bcrypt.hashpw()` — generazione hash (solo registrazione) | $O(B)$ — costante, ~100ms |
| `exists()` — lookup per chiave | $O(D)$ — $O(\log N)$ |
| `save()` — insert in MongoDB | $O(D)$ |
| **Totale Login** | $O(D + B)$ |
| **Totale Registrazione** | $O(2D + B)$ |

**Nota di sicurezza**: il costo $O(B)$ di bcrypt è intenzionalmente elevato (design by intent) per resistere ad attacchi brute-force. Con cost factor 12, ogni verifica richiede ~100ms, rendendo impraticabile un attacco a forza bruta online.

**Complessità spaziale**: $O(1)$ — solo il documento utente viene mantenuto in memoria.

---

## 3. Algoritmo 2: Costruzione Contesto Utente per Personalizzazione (build_user_context)

### 3.1 Descrizione

La funzione `build_user_context()` prende lo stato corrente della pipeline e costruisce una stringa di contesto che viene iniettata nei prompt di **tutti** gli agenti (Classifier, QueryAgent, Generator, Reviser). In base allo stato di autenticazione, produce un contesto personalizzato (utente loggato) oppure un contesto generico (ospite).

### 3.2 Pseudocodice

```
ALGORITHM BuildUserContext(state)

INPUT:  state (AgentState con campi user_*)
OUTPUT: context_string (stringa testuale per i prompt LLM)

1.  IF state.user_status == "loggato":
        parts ← []
        parts.append("INFORMAZIONI STUDENTE (autenticato):")
        parts.append("- Nome: " + (state.user_name OR "N/D"))
        parts.append("- Cognome: " + (state.user_surname OR "N/D"))
        parts.append("- Matricola: " + (state.user_matricola OR "N/D"))
        parts.append("- Dipartimento: " + (state.user_department OR "N/D"))
        parts.append("- Corso di laurea: " + (state.user_course OR "N/D"))
        parts.append("- Tipologia: " + (state.user_tipology OR "N/D"))
        parts.append("- Anno: " + str(state.user_year OR "N/D"))
        RETURN join(parts, "\n")

2.  ELSE:
        RETURN "INFORMAZIONI UTENTE: L'utente è un OSPITE (non autenticato). ..."
```

### 3.3 Analisi di Complessità

| Operazione | Complessità |
|---|---|
| Test dello stato utente | $O(1)$ |
| Concatenazione di $p=8$ stringhe di contesto | $O(p)$ = $O(1)$ con $p$ costante |
| **Totale** | $O(1)$ |

La funzione è puramente computazionale e a costo costante. Viene chiamata una volta per ogni nodo del grafo (5 agenti nel pipeline completo = 5 invocazioni), per un costo totale di $O(5) = O(1)$.

---

## 4. Architettura del Layer di Autenticazione

### Pattern architetturale: Controller → Service → Repository

```
AuthController (HTTP layer)
    └──→ AuthService (business logic, bcrypt, validation)
            └──→ ProfileRepository (MongoDB persistence)
                    └──→ AsyncIOMotorCollection (driver MongoDB)
```

### Flusso dati per l'integrazione con gli agenti

```
1. Client invia POST /api/agent/query con:
   - query: "che materie ho al secondo anno?"
   - user_info: { status: "loggato", name: "Luca", department: "Scuola di Ingegneria", 
                   course: "Ingegneria informatica", tipology: "Magistrale", year: 2 }

2. OrchestratorAgent.process_query() riceve user_info

3. Inizializza AgentState con i campi user_*:
   - user_status = "loggato"
   - user_department = "Scuola di Ingegneria"
   - user_course = "Ingegneria informatica"
   - ...

4. Ogni nodo chiama build_user_context(state) e lo inietta nel prompt LLM

5. L'LLM genera risposte personalizzate per lo studente specifico
```
