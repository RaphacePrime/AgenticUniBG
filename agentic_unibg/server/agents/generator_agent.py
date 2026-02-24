from typing import Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


class GeneratorAgent:
    """
    Agente che genera risposte basate sulla categoria della query
    """
    
    CATEGORY_PROMPTS = {
        "informazioni_corso": """Sei un esperto dei corsi dell'Università di Bergamo.
Fornisci informazioni dettagliate e accurate sui corsi, programmi di studio e docenti.
Se non hai informazioni specifiche, suggerisci dove lo studente può trovarle (sito del corso, segreteria, etc.).""",
        
        "orari": """Sei un assistente per gli orari dell'Università di Bergamo.
Aiuta gli studenti a trovare informazioni su orari delle lezioni, date degli esami e ricevimenti docenti.
Se non hai l'informazione esatta, indica dove possono consultare gli orari ufficiali.""",
        
        "procedure": """Sei un esperto delle procedure amministrative dell'Università di Bergamo.
Guida gli studenti attraverso procedure come iscrizioni, pagamento tasse, richieste documenti.
Fornisci istruzioni chiare e passo-passo.""",
        
        "servizi": """Sei un assistente per i servizi universitari dell'Università di Bergamo.
Fornisci informazioni su mense, biblioteche, aule studio, servizi agli studenti.
Indica orari di apertura e location quando possibile.""",
        
        "generale": """Sei un assistente generale dell'Università di Bergamo.
Fornisci informazioni utili e orientamento agli studenti e visitatori.""",
        
        "altro": """Sei un assistente dell'Università di Bergamo.
Cerca di comprendere la richiesta e fornire una risposta utile o indirizzare l'utente verso la risorsa giusta."""
    }
    
    def __init__(self, llm: ChatGroq):
        self.llm = llm
    
    def _build_system_prompt(self, category: str, context: Dict = None, user_context: str = "") -> str:
        """
        Costruisce il prompt di sistema basato sulla categoria e contesto utente
        """
        base_prompt = self.CATEGORY_PROMPTS.get(category, self.CATEGORY_PROMPTS["altro"])
        
        additional_context = ""
        if context and "additional_info" in context:
            additional_context = f"\n\nInformazioni aggiuntive:\n{context['additional_info']}"
        
        user_section = ""
        if user_context:
            user_section = f"""

{user_context}

Usa queste informazioni per personalizzare la risposta. Se lo studente è autenticato,
puoi fare riferimento al suo corso, dipartimento e anno per dare risposte più mirate.
Se è un ospite, fornisci risposte generiche e orientative."""
        
        return f"""{base_prompt}
{user_section}
Rispondi in italiano in modo chiaro, conciso e professionale.
Se la domanda è fuori dal tuo ambito, indirizza cortesemente l'utente verso la risorsa appropriata.{additional_context}"""
    
    async def generate(self, query: str, category: str, context: Dict = None, user_context: str = "") -> Dict[str, str]:
        """
        Genera una risposta basata sulla query e categoria
        """
        try:
            system_prompt = self._build_system_prompt(category, context, user_context)
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "response": response.content,
                "category_used": category,
                "status": "success"
            }
        except Exception as e:
            return {
                "response": f"Mi dispiace, si è verificato un errore nell'elaborazione della tua richiesta.",
                "category_used": category,
                "status": "error",
                "error": str(e)
            }
