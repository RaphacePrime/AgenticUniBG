from typing import Dict, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


class ClassifierAgent:
    """
    Agente che classifica le query degli utenti in categorie
    """
    
    CATEGORIES = {
        "informazioni_corso": "Richieste su corsi, programmi, docenti",
        "orari": "Richieste su orari delle lezioni, esami, ricevimenti",
        "procedure": "Richieste su procedure amministrative, iscrizioni, tasse",
        "servizi": "Richieste su servizi universitari (mensa, biblioteche, aule studio)",
        "generale": "Domande generiche sull'università",
        "altro": "Altre richieste non classificabili"
    }
    
    def __init__(self, llm: ChatGroq):
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
"""
    
    async def classify(self, query: str, user_context: str = "") -> Dict[str, str]:
        """
        Classifica una query e restituisce la categoria
        """
        try:
            messages = [
                SystemMessage(content=self._build_system_prompt(user_context)),
                HumanMessage(content=query)
            ]
            
            response = await self.llm.ainvoke(messages)
            category = response.content.strip().lower()
            
            # Verifica che la categoria sia valida
            if category not in self.CATEGORIES:
                category = "altro"
            
            return {
                "category": category,
                "description": self.CATEGORIES.get(category, "Non classificata"),
                "confidence": "high"
            }
        except Exception as e:
            return {
                "category": "altro",
                "description": "Errore nella classificazione",
                "confidence": "low",
                "error": str(e)
            }
