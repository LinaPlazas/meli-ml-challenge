import os
from motor.motor_asyncio import AsyncIOMotorClient


class MongoDB:
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "")
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client.document_management
        self.document_analysis = self.db.document_analysis
        self.users = self.db.users

    async def upsert_documents_by_filename(self, documents: list[dict]):
        for doc in documents:
            filename = doc.get("filename")
            if filename:
                await self.document_analysis.update_one(
                    {"filename": filename},
                    {"$set": doc},
                    upsert=True
                )
