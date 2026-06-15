# -*- coding: utf-8 -*-
"""
doc_meta_service.py - 元数据抽取服务

目的：从文档标题和MD内容中自动抽取元数据（车型/版本/有效期/文档类型）
作用：为后续的元数据过滤检索提供基础数据

与老师项目的差异：
  - 老师项目：只有file_title，无元数据抽取
  - 本项目：增加vehicle_model/doc_version/effective_date/expiry_date/doc_type
  - 原因：商用车场景需要按车型、版本、有效期过滤文档

核心函数：
  extract_doc_meta(state) - 主入口，抽取元数据并写入state
"""

import re
from datetime import datetime
from app.process.import_.agent.state import ImportGraphState
from app.shared.runtime.logger import logger, step_log


# 文档类型关键词映射
DOC_TYPE_KEYWORDS = {
    "维修手册": ["维修手册", "维修指南", "维修说明", "修理手册"],
    "质保政策": ["质保", "保修", "质保政策", "保修政策", "三包"],
    "保养手册": ["保养手册", "保养指南", "保养周期", "保养规范"],
    "技术通报": ["技术通报", "TSB", "技术服务通报", "技术公告"],
    "故障案例": ["故障案例", "典型案例", "故障分析", "案例分析"],
    "使用说明": ["使用说明", "操作手册", "用户手册", "使用指南"],
}


@step_log("extract_doc_meta")
def extract_doc_meta(state: ImportGraphState) -> ImportGraphState:
    """
    元数据抽取主入口

    输入：state -> file_title, md_content
    输出：state -> vehicle_model, doc_version, effective_date, expiry_date, doc_type

    步骤：
    1. 获取参数并校验
    2. 从标题和内容中抽取车型
    3. 从内容中抽取版本号
    4. 从内容中抽取生效/失效日期
    5. 从标题中判断文档类型
    6. 写入state
    """
    # 1. 获取参数
    file_title = state.get("file_title", "")
    md_content = state.get("md_content", "")

    if not file_title:
        logger.warning("file_title为空，跳过元数据抽取")
        return state

    # 2. 抽取车型
    vehicle_model = extract_vehicle_model(file_title, md_content)
    logger.info(f"抽取到车型: {vehicle_model}")

    # 3. 抽取版本号
    doc_version = extract_version(file_title, md_content)
    logger.info(f"抽取到版本: {doc_version}")

    # 4. 抽取日期
    effective_date, expiry_date = extract_dates(md_content)
    logger.info(f"抽取到日期: {effective_date} ~ {expiry_date}")

    # 5. 判断文档类型
    doc_type = extract_doc_type(file_title, md_content)
    logger.info(f"抽取到文档类型: {doc_type}")

    # 6. 写入state
    state["vehicle_model"] = vehicle_model or ""
    state["version"] = doc_version or ""  # 使用version字段名，与ImportGraphState一致
    state["effective_date"] = effective_date or ""
    state["expire_date"] = expiry_date or ""
    state["doc_type"] = doc_type or "其他"

    logger.info(f"元数据抽取完成: vehicle={state['vehicle_model']}, type={state['doc_type']}")
    return state


def extract_vehicle_model(title: str, content: str) -> str:
    """
    从标题或内容中抽取车型

    常见格式：
    - HAK 180
    - HK-180
    - 华为Mate60 Pro
    - 长城炮 2024款
    """
    # 优先从标题中匹配
    # 匹配 "品牌+数字+字母" 的组合，如 HAK180, HK-180
    pattern = r'[A-Za-z]{2,}[\s-]?\d{2,}[A-Za-z]?'
    match = re.search(pattern, title)
    if match:
        return match.group().strip()

    # 匹配中文+数字组合，如 "长城炮2024"
    pattern_cn = r'[\u4e00-\u9fff]{2,}\s*\d{2,}款?'
    match_cn = re.search(pattern_cn, title)
    if match_cn:
        return match_cn.group().strip()

    # 从内容前200字中匹配
    short_content = content[:200] if content else ""
    match_content = re.search(pattern, short_content)
    if match_content:
        return match_content.group().strip()

    return ""


def extract_version(title: str, content: str) -> str:
    """
    从标题或内容中抽取版本号

    常见格式：
    - V1.0, v2.1
    - 版本：1.0
    - 第一版
    """
    # 匹配 V1.0 / v2.1 格式
    pattern = r'[Vv]\d+\.\d+'
    match = re.search(pattern, title)
    if match:
        return match.group().strip()

    # 从内容中匹配
    pattern_content = r'[版本版]\s*[:：]?\s*[Vv]?\d+[\.\d]*'
    match_content = re.search(pattern_content, content[:500] if content else "")
    if match_content:
        return match_content.group().strip()

    return ""


def extract_dates(content: str) -> tuple:
    """
    从内容中抽取生效日期和失效日期

    常见格式：
    - 2024年1月1日生效
    - 有效期至2025-12-31
    - 生效日期：2024-01-01
    """
    effective_date = ""
    expiry_date = ""

    if not content:
        return effective_date, expiry_date

    # 匹配生效日期
    pattern_effective = r'(?:生效|发布|实施).*?(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})'
    match = re.search(pattern_effective, content[:1000])
    if match:
        effective_date = match.group(1)

    # 匹配失效日期
    pattern_expiry = r'(?:失效|到期|有效期至|截止).*?(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})'
    match = re.search(pattern_expiry, content[:1000])
    if match:
        expiry_date = match.group(1)

    return effective_date, expiry_date


def extract_doc_type(title: str, content: str) -> str:
    """
    从标题或内容中判断文档类型

    返回：维修手册/质保政策/保养手册/技术通报/故障案例/使用说明/其他
    """
    text = (title + " " + (content[:500] if content else "")).lower()

    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return doc_type

    return "其他"
