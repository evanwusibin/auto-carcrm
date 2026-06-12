# -*- coding: utf-8 -*-
"""
结构化查询服务
作用：查询车辆档案、保养记录、质保规则等结构化数据
参考老师 answer_service.py 的代码风格
"""
from app.shared.runtime.logger import logger, step_log
from app.process.query.agent.state import QueryGraphState


@step_log("validate_structured_state")
def validate_structured_state(state: QueryGraphState):
    """校验结构化查询所需参数"""
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        logger.error("rewritten_query 为空，无法进行结构化查询")
        raise ValueError("rewritten_query 为空，无法进行结构化查询")
    return rewritten_query


def query_vehicle_info(entities: dict) -> list[dict]:
    """
    查询车辆档案
    
    输入：entities（实体字典，包含 vehicle_model、vin 等）
    输出：vehicle_info（车辆信息列表）
    """
    # TODO: 查询 MongoDB vehicles 集合
    # 暂时返回空列表，后续实现 MongoDB 查询
    return []


def query_maintenance_records(entities: dict) -> list[dict]:
    """
    查询保养记录
    
    输入：entities（实体字典）
    输出：maintenance_records（保养记录列表）
    """
    # TODO: 查询 MongoDB maintenance_records 集合
    # 暂时返回空列表，后续实现 MongoDB 查询
    return []


def query_warranty_policies(entities: dict) -> list[dict]:
    """
    查询质保规则
    
    输入：entities（实体字典）
    输出：warranty_policies（质保规则列表）
    """
    # TODO: 查询 MongoDB warranty_policies 集合
    # 暂时返回空列表，后续实现 MongoDB 查询
    return []


def query_structured_data(state: QueryGraphState) -> QueryGraphState:
    """
    结构化查询主函数（参考老师 answer_service.py 风格）
    
    输入：state（包含 rewritten_query, extracted_entities）
    输出：state（新增 structured_chunks 字段）
    """
    # 1. 校验参数
    rewritten_query = validate_structured_state(state)
    
    # 2. 提取实体
    entities = state.get("extracted_entities", {})
    
    # 3. 查询各类结构化数据
    vehicle_info = query_vehicle_info(entities)
    maintenance_records = query_maintenance_records(entities)
    warranty_policies = query_warranty_policies(entities)
    
    # 4. 合并结果
    structured_chunks = []
    
    # 车辆档案
    for info in vehicle_info:
        structured_chunks.append({
            "chunk_id": f"vehicle_{info.get('vin', 'unknown')}",
            "content": f"车辆信息：{info}",
            "type": "vehicle_info",
            "score": 1.0,
        })
    
    # 保养记录
    for record in maintenance_records:
        structured_chunks.append({
            "chunk_id": f"maintenance_{record.get('id', 'unknown')}",
            "content": f"保养记录：{record}",
            "type": "maintenance_record",
            "score": 0.9,
        })
    
    # 质保规则
    for policy in warranty_policies:
        structured_chunks.append({
            "chunk_id": f"warranty_{policy.get('id', 'unknown')}",
            "content": f"质保规则：{policy}",
            "type": "warranty_policy",
            "score": 0.8,
        })
    
    # 5. 写入 state
    state["structured_chunks"] = structured_chunks
    
    logger.info(f"结构化查询完成：{rewritten_query} → {len(structured_chunks)} 条结果")
    
    return state
