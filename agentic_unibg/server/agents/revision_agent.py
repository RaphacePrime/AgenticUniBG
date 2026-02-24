from typing import Dict
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


class RevisionAgent:
    """
    Agente che rivede e migliora le risposte generate
    """
    
    def __init__(self, llm: ChatGroq):
        self.llm = llm
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        return """Sei un agente di revisione per le risposte dell'assistente universitario.

Il tuo compito è:
1. Verificare che la risposta sia chiara, completa e professionale
2. Controllare la correttezza grammaticale e ortografica
3. Assicurarti che il tono sia appropriato per un contesto universitario
4. Aggiungere eventuali precisazioni o disclaimer se necessario
5. Formattare la risposta per essere visualizzata in HTML

IMPORTANTE - REGOLE DI FORMATTAZIONE:
- NON usare markdown (no **, *, #, ecc.)
- NON usare formattazioni speciali
- Usa SOLO testo semplice e punteggiatura
- Per elenchi usa punti o numeri seguiti da spazio (es: "1. ", "- ", "• ")
- Per enfasi usa MAIUSCOLE o ripetizione del concetto
- La risposta deve essere pronta per essere inserita in un tag <p> HTML

Criteri di qualità:
- La risposta risponde effettivamente alla domanda?
- È chiara e comprensibile?
- È completa ma concisa?
- Il tono è professionale ma amichevole?
- Ci sono errori da correggere?
- Il formato è compatibile con HTML standard?

Se la risposta è già buona, restituiscila invariata o con minime modifiche.
Se necessita miglioramenti, rielaborala mantenendo il significato originale.

Rispondi SOLO con la risposta migliorata in formato testo semplice, senza commenti aggiuntivi."""
    
    async def revise(self, original_query: str, generated_response: str, category: str, user_context: str = "") -> Dict[str, str]:
        """
        Rivede e migliora una risposta generata
        """
        try:
            user_section = f"\n{user_context}\n" if user_context else ""
            
            revision_prompt = f"""Domanda originale: {original_query}
Categoria: {category}
{user_section}
Risposta generata: {generated_response}

Rivedi e migliora questa risposta se necessario. Se lo studente è autenticato, assicurati che la risposta sia personalizzata e pertinente al suo percorso di studio. Se è un ospite, assicurati che la risposta sia generica e orientativa."""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=revision_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            revised_response = response.content.strip()
            
            # Calcola se ci sono state modifiche significative
            has_changes = revised_response != generated_response
            
            return {
                "revised_response": revised_response,
                "original_response": generated_response,
                "has_changes": has_changes,
                "status": "success"
            }
        except Exception as e:
            # In caso di errore, restituisci la risposta originale
            return {
                "revised_response": generated_response,
                "original_response": generated_response,
                "has_changes": False,
                "status": "error",
                "error": str(e)
            }
    
    async def quick_check(self, response: str) -> Dict[str, any]:
        """
        Effettua un controllo rapido della qualità della risposta
        """
        try:
            check_prompt = f"""Analizza questa risposta e valutala su questi criteri (1-10):
- Chiarezza
- Completezza
- Professionalità
- Correttezza grammaticale

Risposta: {response}

Rispondi con un JSON con i punteggi e un commento breve."""
            
            messages = [
                SystemMessage(content="Sei un valutatore di qualità delle risposte."),
                HumanMessage(content=check_prompt)
            ]
            
            result = await self.llm.ainvoke(messages)
            
            return {
                "quality_check": result.content,
                "status": "success"
            }
        except Exception as e:
            return {
                "quality_check": "Check non disponibile",
                "status": "error",
                "error": str(e)
            }
