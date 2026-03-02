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
- Massimo 6-8 parole

ESEMPIO:
Conversazione: Lo studente chiede "Quali sono le tasse universitarie per il primo anno di ingegneria?"
Query generata: tasse universitarie primo anno ingegneria unibg

ESEMPIO:
Conversazione: Lo studente chiede "Come posso iscrivermi al test di ammissione?"
Query generata: iscrizione test ammissione unibg

ESEMPIO:
Conversazione: Lo studente chiede "Dove trovo gli orari delle lezioni di informatica?"
Query generata: orari lezioni informatica unibg

ESEMPIO:
Conversazione: Lo studente chiede "Cos'è il top 10 student program?"
Query generata: top 10 student program unibg

Rispondi SOLO con la query generata, nient'altro."""

    async def generate_query(self, query: str, conversation_history: List[Dict] = None) -> Dict[str, str]:
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

            prompt_text = f"""{context_text}Ultima richiesta dello studente: {query}

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
