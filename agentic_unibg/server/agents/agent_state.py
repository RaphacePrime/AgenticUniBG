from typing import TypedDict, Optional, Dict, List


class AgentState(TypedDict):
    """
    Stato condiviso tra tutti gli agenti nel workflow
    """
    # Input originale
    query: str
    context: Optional[Dict]
    
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
