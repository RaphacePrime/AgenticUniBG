from typing import Dict, List, Optional
from langchain_groq import ChatGroq
import os

from langgraph.graph import StateGraph, END
from .agent_state import AgentState
from .classifier_agent import ClassifierAgent
from .generator_agent import GeneratorAgent
from .revision_agent import RevisionAgent


class OrchestratorAgent:
    """
    Orchestrator che coordina il flusso tra gli agenti usando LangGraph:
    Classifier → Generator → Reviser
    """
    
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        # Inizializza gli agenti specializzati
        self.classifier = ClassifierAgent(self.llm)
        self.generator = GeneratorAgent(self.llm)
        self.reviser = RevisionAgent(self.llm)
        
        # Cronologia conversazioni
        self.conversation_history: List[Dict] = []
        
        # Costruisci il grafo
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """
        Costruisce il workflow graph con LangGraph
        """
        # Crea il grafo
        workflow = StateGraph(AgentState)
        
        # Aggiungi i nodi (agenti)
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("revise", self._revise_node)
        
        # Definisci il flusso
        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "generate")
        workflow.add_edge("generate", "revise")
        workflow.add_edge("revise", END)
        
        # Compila il grafo
        return workflow.compile()
    
    async def _classify_node(self, state: AgentState) -> AgentState:
        """
        Nodo per la classificazione della query
        """
        try:
            classification = await self.classifier.classify(state["query"])
            
            state["category"] = classification["category"]
            state["category_description"] = classification["description"]
            state["confidence"] = classification.get("confidence", "unknown")
            state["current_step"] = "classification"
            
            # Aggiungi al workflow tracking
            state["workflow_steps"].append({
                "step": "classification",
                "agent": "ClassifierAgent",
                "result": classification
            })
            
        except Exception as e:
            state["error"] = f"Classification error: {str(e)}"
            state["status"] = "error"
        
        return state
    
    async def _generate_node(self, state: AgentState) -> AgentState:
        """
        Nodo per la generazione della risposta
        """
        try:
            generation = await self.generator.generate(
                query=state["query"],
                category=state["category"],
                context=state.get("context")
            )
            
            state["generated_response"] = generation["response"]
            state["generation_status"] = generation.get("status", "success")
            state["current_step"] = "generation"
            
            # Aggiungi al workflow tracking
            state["workflow_steps"].append({
                "step": "generation",
                "agent": "GeneratorAgent",
                "result": generation
            })
            
        except Exception as e:
            state["error"] = f"Generation error: {str(e)}"
            state["status"] = "error"
        
        return state
    
    async def _revise_node(self, state: AgentState) -> AgentState:
        """
        Nodo per la revisione della risposta
        """
        try:
            revision = await self.reviser.revise(
                original_query=state["query"],
                generated_response=state["generated_response"],
                category=state["category"]
            )
            
            state["final_response"] = revision["revised_response"]
            state["has_revisions"] = revision.get("has_changes", False)
            state["current_step"] = "revision"
            state["status"] = "success"
            
            # Aggiungi al workflow tracking
            state["workflow_steps"].append({
                "step": "revision",
                "agent": "RevisionAgent",
                "result": revision
            })
            
        except Exception as e:
            # Se la revisione fallisce, usa la risposta generata
            state["final_response"] = state.get("generated_response", "")
            state["has_revisions"] = False
            state["error"] = f"Revision error: {str(e)}"
        
        return state
    
    async def process_query(
        self, 
        query: str, 
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Processa una query attraverso il workflow LangGraph
        """
        try:
            # Inizializza lo stato
            initial_state: AgentState = {
                "query": query,
                "context": context,
                "category": None,
                "category_description": None,
                "confidence": None,
                "generated_response": None,
                "generation_status": None,
                "final_response": None,
                "has_revisions": None,
                "workflow_steps": [],
                "current_step": None,
                "error": None,
                "status": "processing"
            }
            
            # Esegui il workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Salva nella cronologia
            conversation_entry = {
                "query": query,
                "category": final_state.get("category"),
                "response": final_state.get("final_response"),
                "workflow": final_state.get("workflow_steps", [])
            }
            self.conversation_history.append(conversation_entry)
            
            # Restituisci il risultato
            return {
                "response": final_state.get("final_response", "Nessuna risposta"),
                "agent_used": "orchestrator",
                "category": final_state.get("category"),
                "metadata": {
                    "model": "llama-3.3-70b-versatile",
                    "workflow_steps": final_state.get("workflow_steps", []),
                    "has_revisions": final_state.get("has_revisions", False),
                    "status": final_state.get("status", "unknown"),
                    "confidence": final_state.get("confidence")
                }
            }
            
        except Exception as e:
            return {
                "response": f"Errore nell'elaborazione: {str(e)}",
                "agent_used": None,
                "metadata": {"error": str(e), "status": "error"}
            }
    
    def get_available_agents(self) -> List[Dict]:
        """
        Restituisce la lista degli agenti disponibili
        """
        return [
            {"name": "classifier", "description": "Classifica le query in categorie"},
            {"name": "generator", "description": "Genera risposte basate sulla categoria"},
            {"name": "reviser", "description": "Rivede e migliora le risposte"},
        ]
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Restituisce la cronologia delle conversazioni
        """
        if limit:
            return self.conversation_history[-limit:]
        return self.conversation_history
    
    def clear_conversation_history(self):
        """
        Pulisce la cronologia delle conversazioni
        """
        self.conversation_history = []
    
    async def analyze_query(self, query: str) -> Dict:
        """
        Analizza una query senza eseguirla (utile per debug)
        """
        classification = await self.classifier.classify(query)
        
        return {
            "query": query,
            "predicted_category": classification["category"],
            "confidence": classification.get("confidence", "unknown"),
            "workflow_plan": [
                "1. Classification → " + classification["category"],
                "2. Generation → Using category-specific prompt",
                "3. Revision → Quality check and improvements"
            ]
        }
