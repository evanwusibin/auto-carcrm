from datetime import datetime
from bson import ObjectId
from app.shared.clients.mongo_knowledge_utils import get_knowledge_db
from app.shared.runtime.logger import logger


class KnowledgeRepository:
    @property
    def collection(self):
        return get_knowledge_db()["knowledge_documents"]

    def save(self, document: dict) -> str:
        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def update_status(self, doc_id: str, status: str) -> None:
        self.collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"status": status, "updated_at": datetime.now()}},
        )

    def find_by_id(self, doc_id: str) -> dict:
        return self.collection.find_one({"_id": ObjectId(doc_id)})

    def find_by_item_name(self, item_name: str) -> list:
        return list(self.collection.find({"item_name": item_name}))

    def find_all(self, status: str = None) -> list:
        query = {}
        if status:
            query["status"] = status
        return list(self.collection.find(query).sort("updated_at", -1))

    def find_all_serialized(self, status: str = None) -> list[dict]:
        documents = self.find_all(status=status)
        items = []
        for document in documents:
            items.append(
                {
                    "id": str(document.get("_id")),
                    "name": document.get("title", ""),
                    "title": document.get("title", ""),
                    "item_name": document.get("item_name", ""),
                    "type": document.get("doc_type", "kb"),
                    "model": document.get("vehicle_model", ""),
                    "version": document.get("version", ""),
                    "chunks": int(document.get("chunk_count", 0) or 0),
                    "status": document.get("status", "draft"),
                    "date": self._format_datetime(document.get("updated_at") or document.get("created_at")),
                    "created_at": self._format_datetime(document.get("created_at")),
                    "updated_at": self._format_datetime(document.get("updated_at")),
                }
            )
        return items

    def delete_by_id(self, doc_id: str) -> None:
        self.collection.delete_one({"_id": ObjectId(doc_id)})

    @staticmethod
    def _format_datetime(value):
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return ""


knowledge_repository = KnowledgeRepository()
