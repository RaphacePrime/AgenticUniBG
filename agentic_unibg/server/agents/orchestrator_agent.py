from typing import Dict, List, Optional
# from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import time

from langgraph.graph import StateGraph, END
from .agent_state import AgentState, build_user_context
from .classifier_agent import ClassifierAgent
from .query_agent import QueryAgent
from .web_agent import WebAgent
from .generator_agent import GeneratorAgent
from .revision_agent import RevisionAgent
from logger.pipeline_logger import PipelineLogger


class OrchestratorAgent:
    """
    Orchestrator che coordina il flusso tra gli agenti usando LangGraph:
    Classifier → QueryAgent → WebAgent → Generator → Reviser
    """
    
    def __init__(self):
        # self.llm = ChatGroq(
        #     model="llama-3.3-70b-versatile",
        #     temperature=0.3,
        #     api_key=os.getenv("GROQ_API_KEY")
        # )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # Inizializza gli agenti specializzati
        self.classifier = ClassifierAgent(self.llm)
        self.query_agent = QueryAgent(self.llm)
        self.web_agent = WebAgent()
        self.generator = GeneratorAgent(self.llm)
        self.reviser = RevisionAgent(self.llm)
        self.logger = PipelineLogger()

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
        workflow.add_node("query", self._query_node)
        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("revise", self._revise_node)
        
        # Definisci il flusso
        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "query")
        workflow.add_edge("query", "web_search")
        workflow.add_edge("web_search", "generate")
        workflow.add_edge("generate", "revise")
        workflow.add_edge("revise", END)
        
        # Compila il grafo
        return workflow.compile()
    
    async def _classify_node(self, state: AgentState) -> AgentState:
        """
        Nodo per la classificazione della query
        """
        try:
            start = time.time()
            user_ctx = build_user_context(state)
            classification = await self.classifier.classify(state["query"], user_context=user_ctx, conversation_history=state.get("conversation_history"))
            elapsed = time.time() - start
            
            state["category"] = classification["category"]
            state["category_description"] = classification["description"]
            state["confidence"] = classification.get("confidence", "unknown")
            state["current_step"] = "classification"
            
            # Aggiungi al workflow tracking
            state["workflow_steps"].append({
                "step": "classification",
                "agent": "ClassifierAgent",
                "result": classification,
                "elapsed_time": elapsed
            })
            
        except Exception as e:
            state["error"] = f"Classification error: {str(e)}"
            state["status"] = "error"
        
        return state
    
    async def _query_node(self, state: AgentState) -> AgentState:
        """
        Nodo per la generazione della query di ricerca web
        """
        try:
            start = time.time()
            user_ctx = build_user_context(state)
            result = await self.query_agent.generate_query(
                query=state["query"],
                conversation_history=state.get("conversation_history"),
                user_context=user_ctx
            )
            elapsed = time.time() - start
            
            state["search_query"] = result["search_query"]
            state["current_step"] = "query_generation"
            
            # Aggiungi al workflow tracking
            state["workflow_steps"].append({
                "step": "query_generation",
                "agent": "QueryAgent",
                "result": result,
                "elapsed_time": elapsed
            })
            
        except Exception as e:
            state["search_query"] = state["query"]  # Fallback alla query originale
            state["error"] = f"Query generation error: {str(e)}"
        
        return state
    
    async def _web_search_node(self, state: AgentState) -> AgentState:
        """
        Nodo per la ricerca web tramite Tavily
        """
        try:
            start = time.time()
            search_query = state.get("search_query", state["query"])
            result = await self.web_agent.search(search_query)
            elapsed = time.time() - start
            
            state["web_results"] = result.get("web_results", [])
            state["web_context"] = result.get("formatted_context", "")
            state["current_step"] = "web_search"
            
            # Aggiungi al workflow tracking
            state["workflow_steps"].append({
                "step": "web_search",
                "agent": "WebAgent",
                "result": {
                    "search_query": search_query,
                    "total_results": result.get("total_results", 0),
                    "top_results_count": result.get("top_results_count", 0),
                    "status": result.get("status", "unknown")
                },
                "elapsed_time": elapsed
            })
            
        except Exception as e:
            state["web_results"] = []
            state["web_context"] = ""
            state["error"] = f"Web search error: {str(e)}"
        
        return state
    
    async def _generate_node(self, state: AgentState) -> AgentState:
        """
        Nodo per la generazione della risposta
        """
        try:
            start = time.time()
            user_ctx = build_user_context(state)
            
            # Arricchisci il contesto con i risultati web
            context = state.get("context") or {}
            web_context = state.get("web_context", "")
            if web_context:
                context["additional_info"] = web_context
            
            generation = await self.generator.generate(
                query=state["query"],
                category=state["category"],
                context=context,
                user_context=user_ctx,
                conversation_history=state.get("conversation_history")
            )
            elapsed = time.time() - start
            
            state["generated_response"] = generation["response"]
            state["generation_status"] = generation.get("status", "success")
            state["current_step"] = "generation"
            
            # Aggiungi al workflow tracking
            state["workflow_steps"].append({
                "step": "generation",
                "agent": "GeneratorAgent",
                "result": generation,
                "elapsed_time": elapsed
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
            start = time.time()
            user_ctx = build_user_context(state)
            revision = await self.reviser.revise(
                original_query=state["query"],
                generated_response=state["generated_response"],
                category=state["category"],
                user_context=user_ctx,
                conversation_history=state.get("conversation_history")
            )
            elapsed = time.time() - start
            
            state["final_response"] = revision["revised_response"]
            state["has_revisions"] = revision.get("has_changes", False)
            state["current_step"] = "revision"
            state["status"] = "success"
            
            # Aggiungi al workflow tracking
            state["workflow_steps"].append({
                "step": "revision",
                "agent": "RevisionAgent",
                "result": revision,
                "elapsed_time": elapsed
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
        context: Optional[Dict] = None,
        user_info: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Processa una query attraverso il workflow LangGraph
        """
        try:
            # Estrai informazioni utente
            ui = user_info or {}

            # Inizializza lo stato
            initial_state: AgentState = {
                "query": query,
                "context": context,
                "conversation_history": conversation_history,
                # User info
                "user_status": ui.get("status", "ospite"),
                "user_name": ui.get("name"),
                "user_surname": ui.get("surname"),
                "user_department": ui.get("department"),
                "user_course": ui.get("course"),
                "user_tipology": ui.get("tipology"),
                "user_year": ui.get("year"),
                "user_matricola": ui.get("matricola"),
                # Classification
                "category": None,
                "category_description": None,
                "confidence": None,
                "search_query": None,
                "web_results": None,
                "web_context": None,
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
            pipeline_start = time.time()
            final_state = await self.workflow.ainvoke(initial_state)
            total_time = time.time() - pipeline_start
            
            # Scrivi il log della pipeline
            try:
                self.logger.write_log(final_state, final_state.get("workflow_steps", []), total_time=total_time)
            except Exception:
                pass  # Il logging non deve mai bloccare la pipeline
            
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
            {"name": "query_agent", "description": "Genera query di ricerca web ottimizzate"},
            {"name": "web_agent", "description": "Cerca informazioni sul sito UniBG tramite Tavily"},
            {"name": "generator", "description": "Genera risposte basate sulla categoria"},
            {"name": "reviser", "description": "Rivede e migliora le risposte"},
        ]
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        La cronologia è ora gestita lato client.
        """
        return []
    
    def clear_conversation_history(self):
        """
        La cronologia è ora gestita lato client.
        """
        pass
    
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
