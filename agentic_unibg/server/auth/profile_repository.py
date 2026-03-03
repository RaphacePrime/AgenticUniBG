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

    async def updateProfile(self, matricola: str, update_fields: dict) -> Optional[dict]:
        """Aggiorna i campi del profilo utente (esclude passwordHash e matricola)."""
        safe_fields = {k: v for k, v in update_fields.items() if k not in ("passwordHash", "matricola", "_id")}
        if not safe_fields:
            return await self.findById(matricola)
        await self._collection.update_one(
            {"matricola": matricola},
            {"$set": safe_fields},
        )
        return await self.findById(matricola)

    async def updatePassword(self, matricola: str, hashed_password: str) -> bool:
        """Aggiorna la password (hash) dell'utente."""
        result = await self._collection.update_one(
            {"matricola": matricola},
            {"$set": {"passwordHash": hashed_password}},
        )
        return result.modified_count > 0
