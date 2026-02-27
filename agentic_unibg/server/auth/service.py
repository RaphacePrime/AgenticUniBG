"""
AuthService - logica di business per autenticazione e registrazione
"""

import bcrypt

from fastapi import HTTPException

from auth.jwt_manager import JWTManager
from auth.profile_repository import ProfileRepository


class AuthService:
    """
    Contiene la logica applicativa per autenticare uno studente esistente
    e per crearne uno nuovo. Delega la persistenza a ProfileRepository
    e la tokenizzazione a JWTManager.
    """

    def __init__(self, profile_repo: ProfileRepository, jwt_manager: JWTManager):
        self._repo = profile_repo
        self._jwt = jwt_manager

    async def authenticate(self, matricola: str, password: str) -> dict:
        """
        Verifica le credenziali e, se corrette, restituisce
        {'student': <doc>, 'token': <jwt>}.
        Solleva HTTPException 401 in caso di credenziali errate.
        """
        student = await self._repo.findById(matricola)
        if not student:
            raise HTTPException(status_code=401, detail="Matricola non trovata")

        if not bcrypt.checkpw(
            password.encode("utf-8"),
            student["passwordHash"].encode("utf-8"),
        ):
            raise HTTPException(status_code=401, detail="Password errata")

        token = self._jwt.generateToken(
            {"matricola": student.get("matricola"), "status": "loggato"}
        )
        return {"student": student, "token": token}

    async def createUser(
        self,
        name: str,
        surname: str,
        matricola: str,
        password: str,
        department: str,
        course: str,
        tipology: str,
        year: int,
    ) -> dict:
        """
        Registra un nuovo studente e restituisce
        {'student': <doc>, 'token': <jwt>}.
        Solleva HTTPException 409 se la matricola è già registrata.
        """
        if await self._repo.exists(matricola):
            raise HTTPException(status_code=409, detail="Matricola già registrata")

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        student_doc = {
            "name": name,
            "surname": surname,
            "passwordHash": hashed.decode("utf-8"),
            "department": department,
            "course": course,
            "tipology": tipology,
            "year": year,
            "matricola": matricola,
        }

        saved = await self._repo.save(student_doc)
        token = self._jwt.generateToken({"matricola": matricola, "status": "loggato"})
        return {"student": saved, "token": token}
