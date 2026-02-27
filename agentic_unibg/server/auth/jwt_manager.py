"""
JWTManager - responsabile della generazione e validazione dei token JWT
"""

import os
from datetime import datetime, timedelta

from fastapi import HTTPException, Request
from jose import JWTError, jwt


class JWTManager:
    """
    Gestisce la creazione e la verifica dei token JWT.
    """

    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = "HS256",
        expire_minutes: int = 60 * 24 * 7,  # 7 giorni
    ):
        self.secret_key = secret_key or os.getenv(
            "JWT_SECRET_KEY", "your-secret-key-change-in-production"
        )
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def generateToken(self, data: dict) -> str:
        """
        Genera un JWT firmato con scadenza configurabile.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def validateToken(self, token: str) -> dict:
        """
        Valida un JWT e restituisce il payload.
        Solleva HTTPException 401 se il token non è valido o è scaduto.
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            raise HTTPException(status_code=401, detail="Token invalido o scaduto")

    def validateFromRequest(self, request: Request) -> dict:
        """
        Estrae il JWT dall'httpOnly cookie della request e lo valida.
        Solleva HTTPException 401 se il cookie è assente o il token è invalido.
        """
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Non autenticato")
        return self.validateToken(token)
