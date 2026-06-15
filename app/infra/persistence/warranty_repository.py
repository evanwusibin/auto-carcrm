# -*- coding: utf-8 -*-
from datetime import datetime
from app.shared.clients.mongo_business_utils import get_business_db
from app.shared.runtime.logger import logger


class WarrantyRepository:
    @property
    def col(self):
        return get_business_db()["warranty_policies"]

    def find_by_id(self, policy_id: str) -> dict | None:
        return self.col.find_one({"_id": policy_id})

    def find_by_model_and_component(self, vehicle_model: str, component: str) -> dict | None:
        return self.col.find_one({
            "vehicle_model": vehicle_model,
            "component_name": component,
            "state": "active",
        })

    def find_by_model(self, vehicle_model: str) -> list:
        return list(self.col.find({"vehicle_model": vehicle_model, "state": "active"}))

    def find_all_active(self) -> list:
        return list(self.col.find({"state": "active"}))

    def save(self, policy: dict) -> str:
        policy.setdefault("created_at", datetime.now().isoformat())
        policy.setdefault("state", "active")
        self.col.insert_one(policy)
        logger.info(f"[WarrantyRepository] 质保规则已保存: {policy.get('_id')}")
        return policy["_id"]

    def update(self, policy_id: str, update_data: dict) -> bool:
        result = self.col.update_one({"_id": policy_id}, {"$set": update_data})
        return result.modified_count > 0


warranty_repository = WarrantyRepository()
