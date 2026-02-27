"""
AuthController - coordina le operazioni di autenticazione e imposta i cookie HTTP
"""

from fastapi import Response

from auth.service import AuthService


class AuthController:
    """
    Fa da ponte tra i route handlers FastAPI e AuthService.
    Si occupa di impostare/eliminare il cookie httpOnly con il JWT.
    """

    def __init__(self, auth_service: AuthService, cookie_max_age: int):
        self._service = auth_service
        self._cookie_max_age = cookie_max_age  # in secondi

    async def login(self, matricola: str, password: str, response: Response) -> dict:
        """
        Autentica lo studente, imposta il cookie JWT e restituisce il profilo pubblico.
        """
        result = await self._service.authenticate(matricola, password)
        self._set_auth_cookie(response, result["token"])
        return self._public_profile(result["student"])

    async def register(
        self,
        name: str,
        surname: str,
        matricola: str,
        password: str,
        department: str,
        course: str,
        tipology: str,
        year: int,
        response: Response,
    ) -> dict:
        """
        Registra un nuovo studente, imposta il cookie JWT e restituisce il profilo pubblico.
        """
        result = await self._service.createUser(
            name=name,
            surname=surname,
            matricola=matricola,
            password=password,
            department=department,
            course=course,
            tipology=tipology,
            year=year,
        )
        self._set_auth_cookie(response, result["token"])
        return self._public_profile(result["student"])

    # ─── helpers ─────────────────────────────────────────────────

    def _set_auth_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,  # Impostare True in produzione con HTTPS
            samesite="lax",
            max_age=self._cookie_max_age,
        )

    @staticmethod
    def _public_profile(student: dict) -> dict:
        """Restituisce solo i campi pubblici del profilo (omette passwordHash)."""
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
