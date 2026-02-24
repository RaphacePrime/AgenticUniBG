from typing import Dict
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
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        categories_text = "\n".join([f"- {cat}: {desc}" for cat, desc in self.CATEGORIES.items()])
        
        return f"""Sei un agente classificatore per l'Università di Bergamo.
Il tuo compito è classificare le richieste degli studenti nelle seguenti categorie:

{categories_text}

Rispondi SOLO con il nome della categoria (una delle chiavi sopra elencate), senza spiegazioni.
Esempi:
- "Quali sono gli orari del corso di matematica?" -> orari
- "Come faccio a iscrivermi all'esame?" -> procedure
- "Chi è il docente di algoritmi?" -> informazioni_corso
- "Dove si trova la mensa?" -> servizi
"""
    
    async def classify(self, query: str) -> Dict[str, str]:
        """
        Classifica una query e restituisce la categoria
        """
        try:
            messages = [
                SystemMessage(content=self.system_prompt),
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
                "confidence": "high"  # Potremmo implementare un sistema di confidence
            }
        except Exception as e:
            return {
                "category": "altro",
                "description": "Errore nella classificazione",
                "confidence": "low",
                "error": str(e)
            }
