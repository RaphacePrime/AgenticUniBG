from typing import TypedDict, Optional, Dict, List


class AgentState(TypedDict):
    """
    Stato condiviso tra tutti gli agenti nel workflow
    """
    # Input originale
    query: str
    context: Optional[Dict]
    
    # Informazioni utente
    user_status: Optional[str]       # "loggato" | "ospite"
    user_name: Optional[str]         # Nome dello studente o None
    user_surname: Optional[str]      # Cognome dello studente o None
    user_department: Optional[str]   # Dipartimento o None
    user_course: Optional[str]       # Corso di laurea o None
    user_tipology: Optional[str]     # Triennale/Magistrale o None
    user_year: Optional[int]         # Anno di frequentazione o None
    user_matricola: Optional[str]    # Matricola o None
    
    # Risultati classificazione
    category: Optional[str]
    category_description: Optional[str]
    confidence: Optional[str]
    
    # Risultati generazione
    generated_response: Optional[str]
    generation_status: Optional[str]
    
    # Risultati revisione
    final_response: Optional[str]
    has_revisions: Optional[bool]
    
    # Workflow tracking
    workflow_steps: List[Dict]
    current_step: Optional[str]
    
    # Error handling
    error: Optional[str]
    status: str


def build_user_context(state: AgentState) -> str:
    """
    Costruisce una stringa di contesto utente da inserire nei prompt degli agenti.
    """
    if state.get("user_status") == "loggato":
        parts = [
            "INFORMAZIONI STUDENTE (autenticato):",
            f"- Nome: {state.get('user_name', 'N/D')}",
            f"- Cognome: {state.get('user_surname', 'N/D')}",
            f"- Matricola: {state.get('user_matricola', 'N/D')}",
            f"- Dipartimento: {state.get('user_department', 'N/D')}",
            f"- Corso di laurea: {state.get('user_course', 'N/D')}",
            f"- Tipologia: {state.get('user_tipology', 'N/D')}",
            f"- Anno di frequentazione: {state.get('user_year', 'N/D')}",
        ]
        return "\n".join(parts)
    else:
        return (
            "INFORMAZIONI UTENTE: L'utente è un OSPITE (non autenticato). "
            "Non sono disponibili informazioni personali sullo studente. "
            "Fornisci risposte generiche senza poter personalizzare in base "
            "al percorso di studio specifico."
        )
