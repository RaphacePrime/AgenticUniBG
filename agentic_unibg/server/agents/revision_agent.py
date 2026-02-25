from typing import Dict, List, Optional
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
        return """Sei un agente di revisione per le risposte dell'assistente universitario. Il tuo obiettivo principale è produrre risposte BREVI, DIRETTE e SCHEMATICHE.

PRIORITÀ ASSOLUTE:
1. BREVITÀ: elimina tutto il superfluo. Se una frase non aggiunge valore, toglila.
2. CHIAREZZA: una sola idea per frase. Evita subordinate lunghe e perifrasi.
3. SCHEMA: quando la risposta elenca più elementi, usa sempre un elenco puntato invece di un paragrafo.
4. NIENTE DISPERSIONE: no introduzioni del tipo "Ottima domanda", no conclusioni ridondanti, no ripetizioni del concetto già espresso.

REGOLE DI FORMATO (testo semplice, compatibile con tag <p> HTML):
- NON usare markdown (no **, *, #, ecc.)
- Per elenchi usa "- " oppure "1. " con un elemento per riga
- Per enfasi usa MAIUSCOLE
- Niente emoji o simboli decorativi
- La risposta deve iniziare direttamente con il contenuto, senza formule di apertura

LUNGHEZZA TARGET:
- Risposta semplice (un fatto, un'informazione): 1-3 frasi
- Risposta articolata (procedura, elenco): max 6-8 punti brevi
- NON superare mai le 150 parole salvo casi eccezionali

PROCESSO DI REVISIONE:
- Se la risposta è già concisa e corretta, restituiscila invariata
- Se è troppo lunga, elimina le parti ridondanti e le introduzioni inutili
- Se è un paragrafo con più elementi, convertila in elenco puntato
- Correggi eventuali errori grammaticali

Rispondi SOLO con la risposta rivista, senza commenti aggiuntivi."""
    
    async def revise(self, original_query: str, generated_response: str, category: str, user_context: str = "", conversation_history: List[Dict] = None) -> Dict[str, str]:
        """
        Rivede e migliora una risposta generata
        """
        try:
            user_section = f"\n{user_context}\n" if user_context else ""

            conversation_ctx = ""
            if conversation_history:
                recent = conversation_history[-4:]  # Ultimi 2 turni
                lines = ["Contesto conversazione:"]
                for msg in recent:
                    role = "Studente" if msg.get('role') == 'user' else "Assistente"
                    lines.append(f"- {role}: {msg.get('content', '')[:150]}")
                conversation_ctx = "\n".join(lines) + "\n\n"

            revision_prompt = f"""{conversation_ctx}Domanda originale: {original_query}
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
