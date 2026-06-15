# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from app.infra.persistence.case_repository import case_repository
from app.infra.persistence.repair_repository import repair_repository
from app.shared.runtime.logger import logger


class CaseService:
    def submit(self, payload: dict, *, user_id: str) -> dict:
        case_id = f"CASE{uuid.uuid4().hex[:8].upper()}"
        source_order_id = payload.get("source_repair_order_id")

        order = None
        if source_order_id:
            order = repair_repository.find_by_id(source_order_id)

        case = {
            "_id": case_id,
            "case_no": f"CASE{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "vehicle_model": payload.get("vehicle_model", order.get("vehicle_model", "") if order else ""),
            "fault_system": payload.get("fault_system", ""),
            "fault_symptom": payload.get("fault_symptom", order.get("fault_description", "") if order else ""),
            "fault_codes": payload.get("fault_codes", order.get("fault_codes", []) if order else []),
            "mileage_range": payload.get("mileage_range", ""),
            "cause_analysis": payload.get("cause_analysis", ""),
            "inspection_steps": payload.get("inspection_steps", []),
            "solution": payload.get("solution", ""),
            "result": payload.get("result", ""),
            "lesson_learned": payload.get("lesson_learned", ""),
            "tags": payload.get("tags", []),
            "source_repair_order_id": source_order_id,
            "submitted_by": user_id,
            "state": "pending_review",
        }

        case_repository.save(case)
        logger.info(f"[CaseService] 案例已提交: {case_id}")
        return case

    def get(self, case_id: str) -> dict | None:
        return case_repository.find_by_id(case_id)

    def list_published(self, skip: int = 0, limit: int = 20, vehicle_model: str | None = None) -> list:
        return case_repository.find_published(skip, limit, vehicle_model)

    def publish(self, case_id: str, reviewer: str) -> bool:
        return case_repository.publish(case_id, reviewer)

    def reject(self, case_id: str, reviewer: str, reason: str) -> bool:
        return case_repository.reject(case_id, reviewer, reason)

    def list_pending_review(self) -> list:
        return case_repository.find_pending_review()

    def search_by_symptom(self, vehicle_model: str, symptom: str) -> list:
        return case_repository.find_by_model_and_symptom(vehicle_model, symptom)


case_service = CaseService()
