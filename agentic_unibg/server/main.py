from fastapi import FastAPI, HTTPException, Depends, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import os
import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta

from agents.orchestrator_agent import OrchestratorAgent
from db import students_collection

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalido o scaduto")

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


class QueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None
    user_info: Optional[dict] = None
    conversation_history: Optional[list] = None


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
async def login(request: LoginRequest, response: Response):
    """
    Login con matricola e password.
    Imposta httpOnly cookie con JWT token.
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

    # Crea JWT token
    token_data = {
        "matricola": student.get("matricola"),
        "status": "loggato"
    }
    access_token = create_access_token(token_data)

    # Imposta cookie httpOnly
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # True in production con HTTPS
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

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
async def register(request: RegisterRequest, response: Response):
    """
    Registrazione nuovo studente.
    Imposta httpOnly cookie con JWT token.
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

    # Crea JWT token
    token_data = {
        "matricola": request.matricola,
        "status": "loggato"
    }
    access_token = create_access_token(token_data)

    # Imposta cookie httpOnly
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # True in production con HTTPS
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

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


@app.get("/api/auth/verify")
async def verify_auth(request: Request, payload: dict = Depends(verify_token)):
    """
    Verifica il token JWT dal cookie e restituisce le informazioni dell'utente.
    """
    matricola = payload.get("matricola")
    if not matricola:
        raise HTTPException(status_code=401, detail="Token invalido")
    
    student = await students_collection.find_one({"matricola": matricola})
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
