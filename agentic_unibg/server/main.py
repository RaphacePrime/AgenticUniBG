from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import bcrypt
from dotenv import load_dotenv

from agents.orchestrator_agent import OrchestratorAgent
from db import students_collection

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
    user_info: Optional[dict] = None


class QueryResponse(BaseModel):
    response: str
    agent_used: Optional[str] = None
    metadata: Optional[dict] = None


class LoginRequest(BaseModel):
    matricola: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    surname: str
    matricola: str
    password: str
    department: str
    course: str
    tipology: str
    year: int


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


# ─── Auth Endpoints ───────────────────────────────────────────────

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """
    Login con matricola e password.
    Restituisce tutte le informazioni dello studente.
    """
    student = await students_collection.find_one({"matricola": request.matricola})
    if not student:
        raise HTTPException(status_code=401, detail="Matricola non trovata")

    # Verifica password con bcrypt
    if not bcrypt.checkpw(
        request.password.encode("utf-8"),
        student["passwordHash"].encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Password errata")

    return {
        "status": "loggato",
        "name": student.get("name"),
        "surname": student.get("surname"),
        "department": student.get("department"),
        "course": student.get("course"),
        "tipology": student.get("tipology"),
        "year": student.get("year"),
        "matricola": student.get("matricola"),
    }


@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """
    Registrazione nuovo studente.
    """
    existing = await students_collection.find_one({"matricola": request.matricola})
    if existing:
        raise HTTPException(status_code=409, detail="Matricola già registrata")

    hashed = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt())

    student_doc = {
        "name": request.name,
        "surname": request.surname,
        "passwordHash": hashed.decode("utf-8"),
        "department": request.department,
        "course": request.course,
        "tipology": request.tipology,
        "year": request.year,
        "matricola": request.matricola,
    }
    await students_collection.insert_one(student_doc)

    return {
        "status": "loggato",
        "name": request.name,
        "surname": request.surname,
        "department": request.department,
        "course": request.course,
        "tipology": request.tipology,
        "year": request.year,
        "matricola": request.matricola,
    }


# ─── Agent Endpoints ──────────────────────────────────────────────


@app.post("/api/agent/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Processa una query usando il sistema ad agenti
    """
    try:
        result = await agent_manager.process_query(
            query=request.query,
            context=request.context,
            user_info=request.user_info
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
