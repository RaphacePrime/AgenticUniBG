from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

from agents.orchestrator_agent import OrchestratorAgent

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Agentic UniBG API",
    description="Backend con sistema ad agenti usando LangChain",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
agent_manager = OrchestratorAgent()


class QueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None


class QueryResponse(BaseModel):
    response: str
    agent_used: Optional[str] = None
    metadata: Optional[dict] = None


@app.get("/")
async def root():
    return {
        "message": "Agentic UniBG API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "agentic-unibg-backend"
    }


@app.post("/api/agent/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Processa una query usando il sistema ad agenti
    """
    try:
        result = await agent_manager.process_query(
            query=request.query,
            context=request.context
        )
        
        return QueryResponse(
            response=result.get("response", ""),
            agent_used=result.get("agent_used"),
            metadata=result.get("metadata")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents")
async def list_agents():
    """
    Restituisce la lista degli agenti disponibili
    """
    return {
        "agents": agent_manager.get_available_agents()
    }


@app.get("/api/conversation/history")
async def get_conversation_history(limit: int = 10):
    """
    Restituisce la cronologia delle conversazioni
    """
    return {
        "history": agent_manager.get_conversation_history(limit)
    }


@app.delete("/api/conversation/history")
async def clear_conversation_history():
    """
    Pulisce la cronologia delle conversazioni
    """
    agent_manager.clear_conversation_history()
    return {
        "status": "success",
        "message": "Cronologia cancellata"
    }


@app.post("/api/agent/analyze")
async def analyze_query(request: QueryRequest):
    """
    Analizza una query senza eseguirla (per debug)
    """
    try:
        result = await agent_manager.analyze_query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
