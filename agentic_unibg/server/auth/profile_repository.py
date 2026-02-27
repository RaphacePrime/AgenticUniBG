"""
ProfileRepository - gestisce la persistenza degli utenti su MongoDB
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorCollection


class ProfileRepository:
    """
    Incapsula tutte le operazioni sulla collection MongoDB degli utenti.
    """

    def __init__(self, collection: AsyncIOMotorCollection):
        self._collection = collection

    async def findById(self, matricola: str) -> Optional[dict]:
        """Cerca un utente tramite matricola (chiave primaria applicativa)."""
        return await self._collection.find_one({"matricola": matricola})

    async def findByEmail(self, email: str) -> Optional[dict]:
        """Cerca un utente tramite email."""
        return await self._collection.find_one({"email": email})

    async def save(self, user_doc: dict) -> dict:
        """
        Inserisce un nuovo documento utente e restituisce il documento
        senza il campo interno _id di MongoDB.
        """
        await self._collection.insert_one(user_doc)
        user_doc.pop("_id", None)
        return user_doc

    async def exists(self, matricola: str) -> bool:
        """Verifica se esiste già un documento con la matricola indicata."""
        doc = await self._collection.find_one({"matricola": matricola}, {"_id": 1})
        return doc is not None
