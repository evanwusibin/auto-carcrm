# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from app.infra.persistence.repair_repository import repair_repository
from app.infra.persistence.vehicle_repository import vehicle_repository
from app.shared.runtime.logger import logger


class RepairService:
    def create(self, payload: dict, *, user_id: str) -> dict:
        order_id = f"RO{uuid.uuid4().hex[:8].upper()}"
        vehicle_id = payload.get("vehicle_id")
        vehicle = vehicle_repository.find_by_id(vehicle_id) if vehicle_id else None
        order = {
            "_id": order_id,
            "order_no": f"RO{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "user_id": user_id,
            "user_name": payload.get("user_name", ""),
            "user_phone": payload.get("user_phone", ""),
            "vehicle_id": vehicle_id,
            "vin": vehicle.get("vin", "") if vehicle else "",
            "vehicle_model": vehicle.get("vehicle_model", "") if vehicle else payload.get("vehicle_model", ""),
            "current_mileage": vehicle.get("current_mileage", 0) if vehicle else 0,
            "fault_description": payload.get("fault_description", ""),
            "fault_codes": payload.get("fault_codes", []),
            "fault_images": payload.get("fault_images", []),
            "location": payload.get("location", ""),
            "can_drive": payload.get("can_drive", True),
            "preferred_time": payload.get("preferred_time", ""),
            "state": "submitted",
        }
        repair_repository.save(order)
        logger.info(f"[RepairService] 报修单已创建: {order_id}")
        return order

    def get(self, order_id: str, *, user_id: str) -> dict | None:
        order = repair_repository.find_by_id(order_id)
        if not order:
            logger.warning(f"[RepairService] 报修单不存在: {order_id}")
        return order

    def list_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> list:
        return repair_repository.find_by_user(user_id, skip, limit)

    def update_state(self, order_id: str, new_state: str, operator: str) -> bool:
        valid_transitions = {
            "submitted": ["accepted", "cancelled"],
            "accepted": ["assigned", "cancelled"],
            "assigned": ["inspecting"],
            "inspecting": ["repairing", "cancelled"],
            "repairing": ["completed", "cancelled"],
            "completed": ["confirmed"],
            "confirmed": [],
            "cancelled": [],
        }
        current = repair_repository.find_by_id(order_id)
        if not current:
            return False
        current_state = current.get("state", "")
        if new_state not in valid_transitions.get(current_state, []):
            logger.warning(f"[RepairService] 状态流转非法: {current_state} → {new_state}")
            return False
        return repair_repository.update_state(order_id, new_state, operator)

    def submit_conclusion(self, order_id: str, conclusion: dict) -> bool:
        return repair_repository.update(order_id, {
            "repair_conclusion": conclusion.get("conclusion", ""),
            "inspection_result": conclusion.get("inspection_result", ""),
            "warranty_final_result": conclusion.get("warranty_result", ""),
            "total_cost": conclusion.get("total_cost"),
        })

    def customer_confirm(self, order_id: str, rating: int, review: str) -> bool:
        return repair_repository.update(order_id, {
            "customer_confirmed_at": datetime.now().isoformat(),
            "customer_rating": rating,
            "customer_review": review,
        })


repair_service = RepairService()
