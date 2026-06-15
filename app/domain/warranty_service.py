# -*- coding: utf-8 -*-
from datetime import date
from app.infra.persistence.warranty_repository import warranty_repository
from app.infra.persistence.vehicle_repository import vehicle_repository
from app.shared.utils.time_utils import parse_date, is_within_mileage, is_within_period, calculate_warranty_expire
from app.shared.runtime.logger import logger


class WarrantyService:
    def precheck(self, payload: dict, *, user_id: str) -> dict:
        vehicle_id = payload.get("vehicle_id")
        component = payload.get("component", "")

        vehicle = vehicle_repository.find_by_id(vehicle_id) if vehicle_id else None
        if not vehicle:
            return {"result": "insufficient_info", "issues": ["未找到车辆信息"], "disclaimer": self._disclaimer()}

        vehicle_model = vehicle.get("vehicle_model", "")
        purchase_date = parse_date(vehicle.get("purchase_date", ""))
        current_mileage = vehicle.get("current_mileage", 0)

        policy = warranty_repository.find_by_model_and_component(vehicle_model, component)
        if not policy:
            policies = warranty_repository.find_by_model(vehicle_model)
            if not policies:
                return {"result": "insufficient_info", "issues": ["未找到该车型的质保规则"], "disclaimer": self._disclaimer()}
            policy = policies[0]

        warranty_years = policy.get("warranty_years", 5)
        warranty_mileage = policy.get("warranty_mileage", 200000)

        issues = []
        is_time_ok = True
        is_mileage_ok = True
        warranty_expire_date = None

        if purchase_date:
            warranty_expire_date = calculate_warranty_expire(purchase_date, warranty_years)
            is_time_ok = date.today() <= warranty_expire_date
            if not is_time_ok:
                issues.append(f"已超过质保期限（{warranty_years}年），质保到期日：{warranty_expire_date}")
        else:
            issues.append("缺少购车日期，无法判断时间质保")

        is_mileage_ok = is_within_mileage(current_mileage, warranty_mileage)
        if not is_mileage_ok:
            issues.append(f"已超过质保里程（{warranty_mileage}公里），当前里程：{current_mileage}")

        if is_time_ok and is_mileage_ok and not issues:
            result = "likely_in_warranty"
        elif not is_time_ok or not is_mileage_ok:
            result = "likely_out_of_warranty"
        else:
            result = "manual_review_required"

        return {
            "result": result,
            "vehicle_model": vehicle_model,
            "component": component,
            "is_within_time": is_time_ok,
            "warranty_expire_date": str(warranty_expire_date) if warranty_expire_date else None,
            "is_within_mileage": is_mileage_ok,
            "warranty_mileage_limit": warranty_mileage,
            "warranty_years": warranty_years,
            "issues": issues,
            "policy_description": policy.get("warranty_description", ""),
            "conditions": policy.get("conditions", []),
            "exclusions": policy.get("exclusions", []),
            "disclaimer": self._disclaimer(),
        }

    def _disclaimer(self) -> str:
        return "本结果仅为初步预判，最终质保结论以授权服务站检测结果为准。"


warranty_service = WarrantyService()
