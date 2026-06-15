# -*- coding: utf-8 -*-
from datetime import datetime
from app.shared.clients.mongo_business_utils import get_business_db
from app.shared.runtime.logger import logger


class DiagnosisRepository:
    @property
    def col(self):
        return get_business_db()["diagnosis_sessions"]

    def find_by_id(self, session_id: str) -> dict | None:
        return self.col.find_one({"_id": session_id})

    def find_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> list:
        return list(self.col.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit))

    def find_by_vehicle(self, vehicle_id: str) -> list:
        return list(self.col.find({"vehicle_id": vehicle_id}).sort("created_at", -1))

    def save(self, session: dict) -> str:
        session.setdefault("created_at", datetime.now().isoformat())
        session.setdefault("updated_at", datetime.now().isoformat())
        session.setdefault("state", "diagnosing")
        self.col.insert_one(session)
        logger.info(f"[DiagnosisRepository] 诊断会话已保存: {session.get('_id')}")
        return session["_id"]

    def update_result(self, session_id: str, diagnosis_result: dict) -> bool:
        result = self.col.update_one(
            {"_id": session_id},
            {"$set": {"diagnosis_result": diagnosis_result, "updated_at": datetime.now().isoformat()}},
        )
        return result.modified_count > 0

    def update_state(self, session_id: str, new_state: str) -> bool:
        result = self.col.update_one(
            {"_id": session_id},
            {"$set": {"state": new_state, "updated_at": datetime.now().isoformat()}},
        )
        return result.modified_count > 0

    def mark_converted(self, session_id: str, repair_order_id: str) -> bool:
        result = self.col.update_one(
            {"_id": session_id},
            {"$set": {
                "converted_to_repair": True,
                "repair_order_id": repair_order_id,
                "state": "converted_to_order",
                "updated_at": datetime.now().isoformat(),
            }},
        )
        return result.modified_count > 0


diagnosis_repository = DiagnosisRepository()
