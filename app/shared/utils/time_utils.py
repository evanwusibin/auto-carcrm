# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta
from app.shared.runtime.logger import logger


def parse_date(date_str: str) -> date | None:
    """将日期字符串解析为 date 对象，支持多种格式。"""
    if not date_str:
        return None
    for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日', '%Y.%m.%d'):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    logger.warning(f"[time_utils] 无法解析日期: {date_str}")
    return None


def days_between(date1: date, date2: date) -> int:
    """计算两个日期之间的天数（date2 - date1）。"""
    return (date2 - date1).days


def is_within_period(
    start_date: date,
    years: int | None = None,
    months: int | None = None,
    check_date: date | None = None,
) -> bool:
    """判断 check_date 是否在 start_date + years/months 的期限内。"""
    check = check_date or date.today()
    end = start_date
    if years:
        end = end.replace(year=end.year + years) if months is None else end
    if months:
        total_months = end.month - 1 + months
        new_year = end.year + total_months // 12
        new_month = total_months % 12 + 1
        try:
            end = end.replace(year=new_year, month=new_month)
        except ValueError:
            import calendar
            last_day = calendar.monthrange(new_year, new_month)[1]
            end = date(new_year, new_month, last_day)
    return check <= end


def calculate_warranty_expire(
    purchase_date: date,
    warranty_years: int,
) -> date:
    """计算质保到期日期。"""
    try:
        return purchase_date.replace(year=purchase_date.year + warranty_years)
    except ValueError:
        import calendar
        last_day = calendar.monthrange(
            purchase_date.year + warranty_years, purchase_date.month
        )[1]
        return date(
            purchase_date.year + warranty_years,
            purchase_date.month,
            min(purchase_date.day, last_day),
        )


def is_within_mileage(
    current_mileage: int,
    warranty_mileage_limit: int,
) -> bool:
    """判断当前里程是否在质保里程范围内。"""
    return current_mileage <= warranty_mileage_limit


def get_next_maintenance_date(
    last_maintenance_date: date,
    interval_months: int = 12,
) -> date:
    """根据上次保养日期和保养周期计算下次保养日期。"""
    total_months = last_maintenance_date.month - 1 + interval_months
    new_year = last_maintenance_date.year + total_months // 12
    new_month = total_months % 12 + 1
    try:
        return last_maintenance_date.replace(year=new_year, month=new_month)
    except ValueError:
        import calendar
        last_day = calendar.monthrange(new_year, new_month)[1]
        return date(new_year, new_month, min(last_maintenance_date.day, last_day))


def format_datetime(dt: datetime) -> str:
    """格式化 datetime 为 ISO 格式字符串。"""
    return dt.isoformat() if dt else ''
