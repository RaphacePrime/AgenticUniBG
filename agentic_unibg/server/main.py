from fastapi import FastAPI, HTTPException, Depends, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from db import students_collection
from models.user import (
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
    QueryRequest,
    QueryResponse,
)
from auth.jwt_manager import JWTManager
from auth.profile_repository import ProfileRepository
from auth.service import AuthService
from auth.controller import AuthController
from agents.orchestrator_agent import OrchestratorAgent

# ─── Bootstrap ────────────────────────────────────────────────────
load_dotenv()

jwt_manager     = JWTManager()
profile_repo    = ProfileRepository(students_collection)
auth_service    = AuthService(profile_repo, jwt_manager)
auth_controller = AuthController(auth_service, cookie_max_age=jwt_manager.expire_minutes * 60)


def verify_token(request: Request) -> dict:
    """Dipendenza FastAPI: estrae e valida il JWT dall'httpOnly cookie."""
    return jwt_manager.validateFromRequest(request)

app = FastAPI(
    title="Agentic UniBG API",
    description="Backend con sistema ad agenti usando LangChain",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_origin_regex=r"http://192\.168\.\d+\.\d+:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
agent_manager = OrchestratorAgent()


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
async def login(body: LoginRequest, response: Response):
    """Login con matricola e password. Imposta httpOnly cookie con JWT token."""
    return await auth_controller.login(body.matricola, body.password, response)


@app.post("/api/auth/register")
async def register(body: RegisterRequest, response: Response):
    """Registrazione nuovo studente. Imposta httpOnly cookie con JWT token."""
    return await auth_controller.register(
        name=body.name,
        surname=body.surname,
        matricola=body.matricola,
        password=body.password,
        department=body.department,
        course=body.course,
        tipology=body.tipology,
        year=body.year,
        response=response,
    )


@app.get("/api/auth/verify")
async def verify_auth(request: Request, payload: dict = Depends(verify_token)):
    """Verifica il token JWT dal cookie e restituisce le informazioni dell'utente."""
    matricola = payload.get("matricola")
    if not matricola:
        raise HTTPException(status_code=401, detail="Token invalido")

    student = await profile_repo.findById(matricola)
    if not student:
        raise HTTPException(status_code=404, detail="Utente non trovato")

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


@app.put("/api/auth/profile")
async def update_profile(
    body: UpdateProfileRequest,
    payload: dict = Depends(verify_token),
):
    """Aggiorna i dati del profilo utente autenticato."""
    matricola = payload.get("matricola")
    if not matricola:
        raise HTTPException(status_code=401, detail="Token invalido")
    update_fields = body.dict(exclude_none=True)
    return await auth_controller.update_profile(matricola, update_fields)


@app.put("/api/auth/password")
async def change_password(
    body: ChangePasswordRequest,
    payload: dict = Depends(verify_token),
):
    """Cambia la password dell'utente autenticato."""
    matricola = payload.get("matricola")
    if not matricola:
        raise HTTPException(status_code=401, detail="Token invalido")
    return await auth_controller.change_password(
        matricola, body.current_password, body.new_password
    )


@app.post("/api/auth/logout")
async def logout(response: Response):
    """
    Logout - cancella il cookie httpOnly.
    """
    response.delete_cookie(key="access_token")
    return {"status": "success", "message": "Logout effettuato"}


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
            user_info=request.user_info,
            conversation_history=request.conversation_history
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
