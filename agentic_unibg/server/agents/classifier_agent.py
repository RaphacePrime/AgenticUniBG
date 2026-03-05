from typing import Dict, List, Optional
# from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage


class ClassifierAgent:
    """
    Agente che classifica le query degli utenti in categorie
    """
    
    CATEGORIES = {
        "informazioni_corso": "Richieste su corsi, programmi, docenti",
        "orari": "Richieste su orari delle lezioni, ricevimenti",
        "date_esami": "Richieste su date e orari degli esami, sessioni d'esame, quando si svolge un esame",
        "procedure": "Richieste su procedure amministrative, iscrizioni, tasse",
        "servizi": "Richieste su servizi universitari (mensa, biblioteche, aule studio)",
        "generale": "Domande generiche sull'università",
        "altro": "Altre richieste non classificabili"
    }
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
    
    def _build_system_prompt(self, user_context: str = "") -> str:
        categories_text = "\n".join([f"- {cat}: {desc}" for cat, desc in self.CATEGORIES.items()])
        
        user_section = f"\n\n{user_context}\n" if user_context else ""
        
        return f"""Sei un agente classificatore per l'Università di Bergamo.
Il tuo compito è classificare le richieste degli studenti nelle seguenti categorie:

{categories_text}
{user_section}
Tieni conto delle informazioni dell'utente per classificare meglio la richiesta.
Se lo studente è autenticato, usa le informazioni del suo profilo per capire il contesto della domanda.
Se è un ospite, classifica la domanda in modo generico.

Rispondi SOLO con il nome della categoria (una delle chiavi sopra elencate), senza spiegazioni.
Esempi:
- "Quali sono gli orari del corso di matematica?" -> orari
- "Come faccio a iscrivermi all'esame?" -> procedure
- "Chi è il docente di algoritmi?" -> informazioni_corso
- "Dove si trova la mensa?" -> servizi
- "Quando è l'esame di analisi?" -> date_esami
- "Che esami ho alla prossima sessione?" -> date_esami
- "In che date sono gli esami della sessione estiva?" -> date_esami
- "Quando posso dare l'esame di basi di dati?" -> date_esami
"""
    
    async def classify(self, query: str, user_context: str = "", conversation_history: List[Dict] = None) -> Dict[str, str]:
        """
        Classifica una query e restituisce la categoria
        """
        try:
            query_text = query
            if conversation_history:
                recent = conversation_history[-4:]  # Ultimi 2 turni per contesto
                ctx_lines = ["Contesto conversazione recente:"]
                for msg in recent:
                    role = "Studente" if msg.get('role') == 'user' else "Assistente"
                    ctx_lines.append(f"- {role}: {msg.get('content', '')[:150]}")
                query_text = "\n".join(ctx_lines) + f"\n\nNuova domanda: {query}"

            system_prompt = self._build_system_prompt(user_context)
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query_text)
            ]
            
            response = await self.llm.ainvoke(messages)
            category = response.content.strip().lower()
            
            # Verifica che la categoria sia valida
            if category not in self.CATEGORIES:
                category = "altro"
            
            return {
                "category": category,
                "description": self.CATEGORIES.get(category, "Non classificata"),
                "confidence": "high",
                "system_prompt": system_prompt,
                "user_prompt": query_text,
                "raw_response": response.content.strip()
            }
        except Exception as e:
            return {
                "category": "altro",
                "description": "Errore nella classificazione",
                "confidence": "low",
                "error": str(e)
            }
