# -*- coding: utf-8 -*-
from datetime import datetime
from app.shared.clients.mongo_business_utils import get_business_db
from app.shared.runtime.logger import logger


class QARepository:
    @property
    def sessions_col(self):
        return get_business_db()["qa_sessions"]

    @property
    def messages_col(self):
        return get_business_db()["qa_messages"]

    @property
    def references_col(self):
        return get_business_db()["qa_references"]

    def find_session(self, session_id: str) -> dict | None:
        return self.sessions_col.find_one({"_id": session_id})

    def save_session(self, session: dict) -> str:
        session.setdefault("created_at", datetime.now().isoformat())
        session["updated_at"] = datetime.now().isoformat()
        self.sessions_col.update_one(
            {"_id": session["_id"]},
            {"$set": session},
            upsert=True,
        )
        return session["_id"]

    def find_messages(self, session_id: str, limit: int = 50) -> list:
        return list(self.messages_col.find({"session_id": session_id}).sort("created_at", -1).limit(limit))

    def save_message(self, message: dict) -> str:
        message.setdefault("created_at", datetime.now().isoformat())
        self.messages_col.insert_one(message)
        return message["_id"]

    def save_references(self, references: list[dict]) -> list:
        if not references:
            return []
        for ref in references:
            ref.setdefault("created_at", datetime.now().isoformat())
        self.references_col.insert_many(references)
        return [r.get("_id") for r in references]

    def find_references(self, message_id: str) -> list:
        return list(self.references_col.find({"message_id": message_id}))

    def save_feedback(self, feedback: dict) -> str:
        feedback.setdefault("created_at", datetime.now().isoformat())
        get_business_db()["user_feedbacks"].insert_one(feedback)
        return feedback.get("_id")


qa_repository = QARepository()
