from typing import Dict, List, Optional
# from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage


class QueryAgent:
    """
    Agente che genera una query di ricerca web ottimizzata
    a partire dalla cronologia della conversazione e dall'ultima richiesta dell'utente.
    """

    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm

    def _build_system_prompt(self) -> str:
        return """Sei un agente specializzato nel generare query di ricerca web per il sito dell'Università degli Studi di Bergamo (unibg.it).

Il tuo compito è trasformare la richiesta dello studente in una SINGOLA query di ricerca breve e ottimizzata, composta solo da parole chiave semplici.

REGOLE:
- Genera SOLO la query, senza spiegazioni o commenti
- Usa parole chiave brevi e pertinenti, come faresti in una ricerca Google
- Rimuovi articoli, congiunzioni e parole inutili
- Non formulare domande, solo parole chiave
- Tieni conto del contesto della conversazione per capire cosa cerca lo studente
- La query deve essere in italiano
- Massimo 12 parole

INFORMAZIONI STUDENTE E QUANDO USARLE:
Ti verranno fornite le informazioni del profilo dello studente (corso di laurea, dipartimento, anno, tipologia).
Devi decidere AUTONOMAMENTE se includerle nella query in base al tipo di domanda:

INCLUDI le info studente quando la domanda riguarda:
- Materie, insegnamenti, piano di studi (es. "che materie ho?" → aggiungi corso + anno + tipologia)
- Orari delle lezioni del proprio corso
- Piano di studi, crediti, curriculum del proprio corso
- Qualsiasi domanda dove il corso/anno specifico cambia la risposta

NON INCLUDERE le info studente quando la domanda riguarda:
- Procedure generiche (iscrizioni, tasse, borse di studio)
- Informazioni su docenti specifici
- Servizi universitari (mensa, biblioteca, aule)
- Informazioni generali sull'ateneo
- Erasmus, tirocini, laurea
- Qualsiasi domanda che ha la stessa risposta indipendentemente dal corso

ESEMPIO con info studente (corso: ingegneria informatica, anno: 1, tipologia: magistrale):
Domanda: "che materie ho al secondo anno?"
Query: materie secondo anno ingegneria informatica magistrale unibg

ESEMPIO con info studente (corso: scienze della comunicazione, anno: 2, tipologia: triennale):
Domanda: "quali esami devo dare quest'anno?"
Query: piano studi secondo anno scienze comunicazione triennale unibg

ESEMPIO senza info studente:
Domanda: "come faccio a iscrivermi al test di ammissione?"
Query: iscrizione test ammissione unibg

ESEMPIO senza info studente:
Domanda: "chi è il docente di algoritmi?"
Query: docente algoritmi unibg

ESEMPIO senza info studente:
Domanda: "dove si trova la mensa?"
Query: mensa universitaria unibg

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
