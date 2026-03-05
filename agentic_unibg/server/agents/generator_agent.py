from typing import Dict, List, Optional
# from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from .web_agent import get_italian_timestamp


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
Cerca di comprendere la richiesta e fornire una risposta utile o indirizzare l'utente verso la risorsa giusta.""",

        "date_esami": """Sei un assistente specializzato nelle date e orari degli esami dell'Università di Bergamo.
Aiuta gli studenti a trovare quando si svolgono gli esami, in quale sessione e in quali date.
Ti vengono fornite informazioni estratte dai calendari ufficiali degli esami.
Cerca le date degli esami specifici richiesti dallo studente all'interno del contenuto fornito.
Se non trovi l'esame specifico, indica chiaramente che non è presente nel calendario fornito e suggerisci di controllare il portale esami.
Se lo studente è un ospite e non sai il suo corso, chiedigli gentilmente quale corso frequenta per poterti aiutare meglio.
IMPORTANTE: Se non è stato possibile determinare quale calendario consultare (perché l'utente è ospite e non ha specificato il corso), NON aggiungere 'Pagina di riferimento' in fondo alla risposta. Non includere nella risposta dettagli interni come numeri di selezione, motivi della scelta o metadati del processo."""
    }

    # Istruzioni comuni per l'uso delle fonti web
    SOURCE_INSTRUCTIONS = """\n\nISTRUZIONI PER L'USO DELLE FONTI WEB:
Ti vengono fornite informazioni estratte dal sito ufficiale dell'Università di Bergamo.

REGOLE FONDAMENTALI:
1. Basa la tua risposta ESCLUSIVAMENTE sulle informazioni contenute nelle fonti fornite.
2. NON inventare date, scadenze, procedure o informazioni non presenti nelle fonti.
3. Estrai dalle fonti SOLO le parti pertinenti alla domanda dello studente, ignorando il resto.
4. Se le fonti contengono date e scadenze specifiche, riportale fedelmente.
5. Se le fonti non contengono informazioni sufficienti per rispondere, dillo chiaramente e suggerisci di contattare la Segreteria Studenti o consultare il sito.
6. In fondo alla risposta, indica la pagina di riferimento con il formato: "Pagina di riferimento: [URL]", usando l'URL della fonte principale utilizzata.
7. Le fonti possono contenere testo lungo e non perfettamente ordinato: analizzalo con attenzione per estrarre le informazioni corrette.
8. Alcune fonti sono documenti PDF: in quel caso vengono forniti anche i link ipertestuali estratti direttamente dal PDF con la pagina di provenienza. Se uno di questi link è rilevante per la risposta dello studente, includilo nella risposta in forma cliccabile (formato Markdown: [testo](url)) indicando anche da quale parte del documento proviene."""
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
    
    def _build_system_prompt(self, category: str, context: Dict = None, user_context: str = "") -> str:
        """
        Costruisce il prompt di sistema basato sulla categoria e contesto utente
        """
        base_prompt = self.CATEGORY_PROMPTS.get(category, self.CATEGORY_PROMPTS["altro"])
        
        # Timestamp italiano
        today = get_italian_timestamp()
        timestamp_section = f"\n\nDATA ODIERNA: {today} (Anno accademico 2025/2026)"
        
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
        
        source_instructions = self.SOURCE_INSTRUCTIONS if additional_context else ""

        return f"""{base_prompt}
{timestamp_section}
{user_section}
Rispondi in italiano in modo chiaro, conciso e professionale.
Se la domanda è fuori dal tuo ambito, indirizza cortesemente l'utente verso la risorsa appropriata.{source_instructions}{additional_context}"""
    
    async def generate(self, query: str, category: str, context: Dict = None, user_context: str = "", conversation_history: List[Dict] = None) -> Dict[str, str]:
        """
        Genera una risposta basata sulla query e categoria
        """
        try:
            system_prompt = self._build_system_prompt(category, context, user_context)

            messages = [SystemMessage(content=system_prompt)]

            # Aggiungi storico come messaggi LLM nativi per vera memoria conversazionale
            if conversation_history:
                for msg in conversation_history:
                    if msg.get('role') == 'user':
                        messages.append(HumanMessage(content=msg['content']))
                    elif msg.get('role') == 'assistant':
                        messages.append(AIMessage(content=msg['content']))

            messages.append(HumanMessage(content=query))
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "response": response.content,
                "category_used": category,
                "status": "success",
                "system_prompt": system_prompt,
                "user_prompt": query,
                "raw_response": response.content
            }
        except Exception as e:
            return {
                "response": f"Mi dispiace, si è verificato un errore nell'elaborazione della tua richiesta.",
                "category_used": category,
                "status": "error",
                "error": str(e)
            }
