"""
Pydantic schemas per l'utente e le richieste HTTP
"""

from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    """
    Rappresentazione del dominio utente (studente universitario).
    Rispecchia il documento salvato su MongoDB.
    """
    name: str
    surname: str
    matricola: str
    department: str
    course: str
    tipology: str
    year: int
    passwordHash: str


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


class QueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None
    user_info: Optional[dict] = None
    conversation_history: Optional[list] = None


class QueryResponse(BaseModel):
    response: str
    agent_used: Optional[str] = None
    metadata: Optional[dict] = None
