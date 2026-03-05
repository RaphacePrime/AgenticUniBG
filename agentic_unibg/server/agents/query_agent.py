from typing import Dict, List, Optional
# from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from .web_agent import get_italian_timestamp


class QueryAgent:
    """
    Agente che genera una query di ricerca web ottimizzata
    a partire dalla cronologia della conversazione e dall'ultima richiesta dell'utente.
    """

    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm

    def _build_system_prompt(self) -> str:
        today = get_italian_timestamp()
        return f"""Sei un agente specializzato nel generare query di ricerca web per il sito dell'Università degli Studi di Bergamo (unibg.it).

DATA ODIERNA: {today} (Anno accademico 2025/2026)

Il tuo compito è trasformare la richiesta dello studente in una SINGOLA query di ricerca breve e ottimizzata, composta solo da parole chiave semplici.

REGOLE FONDAMENTALI:
- Genera SOLO la query, senza spiegazioni o commenti
- Usa parole chiave brevi e pertinenti, come faresti in una ricerca Google
- Rimuovi articoli, congiunzioni e parole inutili
- Non formulare domande, solo parole chiave
- La query deve essere in italiano
- Massimo 8 parole
- Quando la domanda riguarda date, sessioni o periodi temporali, includi l'anno accademico (2025/2026) o il periodo specifico (es. "marzo 2026", "sessione estiva 2026") nella query

REGOLA CRITICA - CONTESTO CONVERSAZIONE:
Il contesto della conversazione ha SEMPRE la priorità sul profilo dello studente.
Se la conversazione indica che l'utente sta chiedendo informazioni su un corso/dipartimento DIVERSO dal proprio, la query DEVE riferirsi al corso/dipartimento menzionato nella conversazione, NON a quello del profilo.

Esempio critico:
- Profilo studente: Ingegneria informatica, Magistrale
- Conversazione precedente: lo studente chiedeva degli esami di Giurisprudenza
- Nuova domanda: "invece nella sessione estiva?"
- Query CORRETTA: date esami giurisprudenza sessione estiva 2025/2026 unibg
- Query SBAGLIATA: esami sessione estiva ingegneria informatica magistrale unibg
Motivo: dalla conversazione è chiaro che "invece" si riferisce sempre a Giurisprudenza, non al suo corso.

QUANDO USARE LE INFORMAZIONI DEL PROFILO STUDENTE:
INCLUDI le info del profilo SOLO quando:
- La domanda riguarda esplicitamente il PROPRIO corso dello studente (es. "che materie ho?", "i miei esami")
- Non c'è contesto conversazionale che indichi un argomento diverso
- La domanda usa pronomi possessivi ("mio", "miei", "il mio corso")

NON INCLUDERE le info del profilo quando:
- La conversazione indica un argomento/corso diverso dal profilo
- La domanda è generica (procedure, servizi, docenti, mensa, erasmus)
- La domanda menziona esplicitamente un altro corso o dipartimento
- La domanda è un follow-up ("e nella sessione X?", "invece per...", "e gli orari?") e il contesto conversazionale indica un corso diverso

ESEMPI CON PROFILO (corso: ingegneria informatica, anno: 1, magistrale):
- "che materie ho al secondo anno?" → materie secondo anno ingegneria informatica magistrale unibg
- "i miei esami della prossima sessione" → esami prossima sessione ingegneria informatica magistrale 2025/2026 unibg

ESEMPI SENZA PROFILO:
- "come faccio a iscrivermi al test di ammissione?" → iscrizione test ammissione unibg
- "chi è il docente di algoritmi?" → docente algoritmi unibg
- "dove si trova la mensa?" → mensa universitaria unibg
- "esami giurisprudenza terzo anno" → date esami giurisprudenza terzo anno 2025/2026 unibg

ESEMPIO FOLLOW-UP (contesto: si parlava di esami di giurisprudenza):
- "invece nella sessione estiva?" → date esami giurisprudenza sessione estiva 2025/2026 unibg
- "e quelli del quarto anno?" → date esami giurisprudenza quarto anno 2025/2026 unibg

Rispondi SOLO con la query generata, nient'altro."""

    async def generate_query(self, query: str, conversation_history: List[Dict] = None, user_context: str = "") -> Dict[str, str]:
        """
        Genera una query di ricerca web ottimizzata a partire dalla richiesta dell'utente
        e dalla cronologia della conversazione.
        """
        try:
            # Costruisci il contesto dalla conversazione recente
            context_text = ""
            if conversation_history:
                recent = conversation_history[-6:]  # Ultimi 3 turni
                ctx_lines = ["Contesto conversazione recente:"]
                for msg in recent:
                    role = "Studente" if msg.get('role') == 'user' else "Assistente"
                    ctx_lines.append(f"- {role}: {msg.get('content', '')[:200]}")
                context_text = "\n".join(ctx_lines) + "\n\n"

            # Aggiungi informazioni utente se disponibili
            user_info_text = ""
            if user_context:
                user_info_text = f"\nInformazioni studente:\n{user_context}\n\n"

            prompt_text = f"""{context_text}{user_info_text}Ultima richiesta dello studente: {query}

Genera la query di ricerca web:"""

            system_prompt = self._build_system_prompt()
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=prompt_text)
            ]

            response = await self.llm.ainvoke(messages)
            search_query = response.content.strip()

            return {
                "search_query": search_query,
                "original_query": query,
                "status": "success",
                "system_prompt": system_prompt,
                "user_prompt": prompt_text,
                "raw_response": search_query
            }
        except Exception as e:
            # Fallback: usa la query originale semplificata
            return {
                "search_query": query,
                "original_query": query,
                "status": "error",
                "error": str(e)
            }
