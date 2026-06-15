# -*- coding: utf-8 -*-
from datetime import date
from app.infra.persistence.vehicle_repository import vehicle_repository
from app.shared.clients.mongo_business_utils import get_business_db
from app.shared.utils.time_utils import parse_date, get_next_maintenance_date
from app.shared.runtime.logger import logger


class MaintenanceService:
    @property
    def records_col(self):
        return get_business_db()["maintenance_records"]

    def get_records(self, vehicle_id: str, limit: int = 10) -> list:
        return list(self.records_col.find({"vehicle_id": vehicle_id}).sort("maintenance_date", -1).limit(limit))

    def check(self, payload: dict, *, user_id: str) -> dict:
        vehicle_id = payload.get("vehicle_id")
        vehicle = vehicle_repository.find_by_id(vehicle_id) if vehicle_id else None
        if not vehicle:
            return {"result": "insufficient_info", "message": "未找到车辆信息"}

        current_mileage = vehicle.get("current_mileage", 0)
        records = self.get_records(vehicle_id, limit=1)

        if not records:
            return {
                "result": "no_records",
                "message": "未找到保养记录，建议尽快到服务站进行首次保养",
                "current_mileage": current_mileage,
            }

        last_record = records[0]
        last_mileage = last_record.get("mileage_at_maintenance", 0)
        last_date_str = last_record.get("maintenance_date", "")
        last_date = parse_date(last_date_str)
        next_mileage = last_record.get("next_maintenance_mileage")
        next_date_str = last_record.get("next_maintenance_date", "")
        next_date = parse_date(next_date_str)

        issues = []
        need_maintenance = False

        if next_mileage and current_mileage >= next_mileage:
            need_maintenance = True
            issues.append(f"当前里程 {current_mileage}km 已超过下次保养里程 {next_mileage}km")

        if next_date and date.today() >= next_date:
            need_maintenance = True
            issues.append(f"当前日期已超过下次保养日期 {next_date}")

        mileage_since_last = current_mileage - last_mileage
        if mileage_since_last >= 9000 and not need_maintenance:
            issues.append(f"距上次保养已行驶 {mileage_since_last}km，接近保养周期")

        result = "maintenance_due" if need_maintenance else "normal"

        return {
            "result": result,
            "vehicle_id": vehicle_id,
            "current_mileage": current_mileage,
            "last_maintenance_date": last_date_str,
            "last_maintenance_mileage": last_mileage,
            "next_maintenance_date": next_date_str,
            "next_maintenance_mileage": next_mileage,
            "mileage_since_last": mileage_since_last,
            "issues": issues,
            "message": "需要保养，请尽快到服务站" if need_maintenance else "保养状态正常",
        }

    def add_record(self, record: dict) -> str:
        from datetime import datetime
        record.setdefault("created_at", datetime.now().isoformat())
        record.setdefault("state", "completed")
        self.records_col.insert_one(record)
        logger.info(f"[MaintenanceService] 保养记录已保存: {record.get('_id')}")
        return record.get("_id")


maintenance_service = MaintenanceService()
