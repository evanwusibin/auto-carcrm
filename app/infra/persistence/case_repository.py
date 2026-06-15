# -*- coding: utf-8 -*-
from datetime import datetime
from app.shared.clients.mongo_business_utils import get_business_db
from app.shared.runtime.logger import logger


class CaseRepository:
    @property
    def col(self):
        return get_business_db()["typical_cases"]

    def find_by_id(self, case_id: str) -> dict | None:
        return self.col.find_one({"_id": case_id})

    def find_published(self, skip: int = 0, limit: int = 20, vehicle_model: str | None = None) -> list:
        query = {"state": "published"}
        if vehicle_model:
            query["vehicle_model"] = vehicle_model
        return list(self.col.find(query).sort("created_at", -1).skip(skip).limit(limit))

    def find_by_model_and_symptom(self, vehicle_model: str, symptom_keyword: str) -> list:
        return list(self.col.find({
            "vehicle_model": vehicle_model,
            "fault_symptom": {"$regex": symptom_keyword, "$options": "i"},
            "state": "published",
        }).limit(10))

    def find_pending_review(self) -> list:
        return list(self.col.find({"state": "pending_review"}))

    def save(self, case: dict) -> str:
        case.setdefault("created_at", datetime.now().isoformat())
        case.setdefault("state", "pending_review")
        self.col.insert_one(case)
        logger.info(f"[CaseRepository] 案例已保存: {case.get('_id')}")
        return case["_id"]

    def publish(self, case_id: str, reviewer: str) -> bool:
        result = self.col.update_one(
            {"_id": case_id},
            {"$set": {
                "state": "published",
                "reviewed_by": reviewer,
                "published_at": datetime.now().isoformat(),
            }},
        )
        return result.modified_count > 0

    def reject(self, case_id: str, reviewer: str, reason: str) -> bool:
        result = self.col.update_one(
            {"_id": case_id},
            {"$set": {
                "state": "rejected",
                "reviewed_by": reviewer,
                "reject_reason": reason,
            }},
        )
        return result.modified_count > 0

    def update(self, case_id: str, update_data: dict) -> bool:
        result = self.col.update_one({"_id": case_id}, {"$set": update_data})
        return result.modified_count > 0


case_repository = CaseRepository()
