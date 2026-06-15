# -*- coding: utf-8 -*-
from datetime import datetime
from app.shared.clients.mongo_business_utils import get_business_db
from app.shared.runtime.logger import logger


class VehicleRepository:
    @property
    def col(self):
        return get_business_db()["vehicles"]

    def find_by_id(self, vehicle_id: str) -> dict | None:
        return self.col.find_one({"_id": vehicle_id})

    def find_by_vin(self, vin: str) -> dict | None:
        return self.col.find_one({"vin": vin})

    def find_by_owner(self, user_id: str) -> list:
        return list(self.col.find({"owner_user_id": user_id, "state": "active"}))

    def find_all(self, skip: int = 0, limit: int = 20) -> list:
        return list(self.col.find().skip(skip).limit(limit))

    def save(self, vehicle: dict) -> str:
        vehicle.setdefault("created_at", datetime.now().isoformat())
        vehicle.setdefault("updated_at", datetime.now().isoformat())
        vehicle.setdefault("state", "active")
        self.col.insert_one(vehicle)
        logger.info(f"[VehicleRepository] 车辆已保存: {vehicle.get('_id')}")
        return vehicle["_id"]

    def update(self, vehicle_id: str, update_data: dict) -> bool:
        update_data["updated_at"] = datetime.now().isoformat()
        result = self.col.update_one({"_id": vehicle_id}, {"$set": update_data})
        return result.modified_count > 0

    def update_mileage(self, vehicle_id: str, mileage: int) -> bool:
        return self.update(vehicle_id, {"current_mileage": mileage})


vehicle_repository = VehicleRepository()
