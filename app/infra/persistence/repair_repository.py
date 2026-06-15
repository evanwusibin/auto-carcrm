# -*- coding: utf-8 -*-
from datetime import datetime
from app.shared.clients.mongo_business_utils import get_business_db
from app.shared.runtime.logger import logger


class RepairRepository:
    @property
    def col(self):
        return get_business_db()["repair_orders"]

    def find_by_id(self, order_id: str) -> dict | None:
        return self.col.find_one({"_id": order_id})

    def find_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> list:
        return list(self.col.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit))

    def find_by_vehicle(self, vehicle_id: str) -> list:
        return list(self.col.find({"vehicle_id": vehicle_id}).sort("created_at", -1))

    def find_by_state(self, state: str, skip: int = 0, limit: int = 50) -> list:
        return list(self.col.find({"state": state}).sort("created_at", -1).skip(skip).limit(limit))

    def save(self, order: dict) -> str:
        order.setdefault("created_at", datetime.now().isoformat())
        order.setdefault("updated_at", datetime.now().isoformat())
        order.setdefault("state", "submitted")
        order.setdefault("state_history", [])
        self.col.insert_one(order)
        logger.info(f"[RepairRepository] 报修单已保存: {order.get('_id')}")
        return order["_id"]

    def update_state(self, order_id: str, new_state: str, operator: str) -> bool:
        now = datetime.now().isoformat()
        result = self.col.update_one(
            {"_id": order_id},
            {
                "$set": {"state": new_state, "updated_at": now},
                "$push": {"state_history": {"state": new_state, "time": now, "operator": operator}},
            },
        )
        return result.modified_count > 0

    def update(self, order_id: str, update_data: dict) -> bool:
        update_data["updated_at"] = datetime.now().isoformat()
        result = self.col.update_one({"_id": order_id}, {"$set": update_data})
        return result.modified_count > 0


repair_repository = RepairRepository()
