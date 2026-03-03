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


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    department: Optional[str] = None
    course: Optional[str] = None
    tipology: Optional[str] = None
    year: Optional[int] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class QueryRequest(BaseModel):
    query: str
    context: Optional[dict] = None
    user_info: Optional[dict] = None
    conversation_history: Optional[list] = None


class QueryResponse(BaseModel):
    response: str
    agent_used: Optional[str] = None
    metadata: Optional[dict] = None
