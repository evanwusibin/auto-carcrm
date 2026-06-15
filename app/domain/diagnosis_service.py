# -*- coding: utf-8 -*-
import uuid
from datetime import datetime
from app.infra.persistence.diagnosis_repository import diagnosis_repository
from app.infra.persistence.vehicle_repository import vehicle_repository
from app.shared.config.business_config import business_config
from app.shared.runtime.logger import logger


class DiagnosisService:
    def run(self, payload: dict, *, user_id: str) -> dict:
        session_id = f"DS{uuid.uuid4().hex[:8].upper()}"
        vehicle_id = payload.get("vehicle_id")
        fault_description = payload.get("fault_description", "")
        fault_codes = payload.get("fault_codes", [])
        fault_images = payload.get("fault_images", [])

        vehicle = vehicle_repository.find_by_id(vehicle_id) if vehicle_id else None

        session = {
            "_id": session_id,
            "user_id": user_id,
            "vehicle_id": vehicle_id,
            "vin": vehicle.get("vin", "") if vehicle else "",
            "vehicle_model": vehicle.get("vehicle_model", "") if vehicle else "",
            "current_mileage": vehicle.get("current_mileage", 0) if vehicle else 0,
            "fault_description": fault_description,
            "fault_images": fault_images,
            "fault_codes": fault_codes,
            "extracted_entities": {
                "fault_symptom": self._extract_symptoms(fault_description),
                "fault_codes": fault_codes,
            },
        }

        risk_level = self._assess_risk(fault_description, fault_codes)
        possible_causes = self._analyze_causes(fault_description, fault_codes, vehicle)
        suggestion = self._generate_suggestion(risk_level, fault_description)

        diagnosis_result = {
            "possible_causes": possible_causes,
            "suggestion": suggestion,
            "risk_level": risk_level,
            "references": [],
        }

        session["risk_level"] = risk_level
        session["diagnosis_result"] = diagnosis_result
        session["state"] = "completed"
        diagnosis_repository.save(session)

        logger.info(f"[DiagnosisService] 诊断完成: {session_id}, 风险等级={risk_level}")
        return {
            "session_id": session_id,
            "risk_level": risk_level,
            "possible_causes": possible_causes,
            "suggestion": suggestion,
            "vehicle_model": session["vehicle_model"],
            "disclaimer": "本诊断仅供参考，如遇高风险故障请立即联系服务站或拨打救援电话。",
        }

    def _assess_risk(self, fault_description: str, fault_codes: list) -> str:
        high_keywords = business_config.diagnosis_risk_high_keywords
        text = fault_description.lower()
        for kw in high_keywords:
            if kw in text:
                return "high"
        high_codes = ("P0A0F", "P1D00", "P0562", "P0A1A")
        for code in fault_codes:
            if code.upper() in high_codes:
                return "high"
        medium_keywords = ("异响", "抖动", "漏液", "警告", "报警", "动力不足")
        for kw in medium_keywords:
            if kw in text:
                return "medium"
        return "low"

    def _extract_symptoms(self, description: str) -> list:
        symptom_keywords = [
            "无法启动", "启动不了", "挂不上挡", "动力不足", "异响", "抖动",
            "漏液", "冒烟", "刹车失灵", "转向困难", "空调不制冷", "无法充电",
        ]
        return [kw for kw in symptom_keywords if kw in description]

    def _analyze_causes(self, fault_description: str, fault_codes: list, vehicle: dict | None) -> list:
        causes = []
        if "无法启动" in fault_description or "启动不了" in fault_description:
            causes.extend([
                "低压电瓶电量不足，导致高压系统无法上电",
                "高压互锁回路异常",
                "挡位传感器信号异常",
            ])
        if "P0A0F" in fault_codes:
            causes.append("DC-DC转换器故障导致低压侧供电异常")
        if "动力不足" in fault_description:
            causes.extend([
                "动力电池SOC过低",
                "电机控制器故障",
            ])
        if not causes:
            causes.append("需服务站专业设备进一步检测")
        return causes

    def _generate_suggestion(self, risk_level: str, fault_description: str) -> str:
        if risk_level == "high":
            return "建议停止使用车辆，不要强行启动，立即联系服务站或拨打救援电话。如在高速或危险路段，请先确保人身安全。"
        if risk_level == "medium":
            return "建议尽快到最近的授权服务站进行检测，行驶中如出现异常请立即靠边停车。"
        return "建议预约服务站进行常规检查，如症状加重请及时联系服务站。"

    def get_session(self, session_id: str) -> dict | None:
        return diagnosis_repository.find_by_id(session_id)

    def list_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> list:
        return diagnosis_repository.find_by_user(user_id, skip, limit)


diagnosis_service = DiagnosisService()
