"""
初始化本地 MongoDB 业务库 + 知识库 + 集合 + 索引 + 默认账号

执行前提：本地 27017 已有 mongod 在跑（docker run -d -p 27017:27017 --name local-mongo mongo:7）
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pymongo import ASCENDING, MongoClient

DEFAULT_URL = "mongodb://127.0.0.1:27017"
BUSINESS_DB = "auto_carcrm"          # 业务库（chat_message / users / vehicles / 报修 等）
KNOWLEDGE_DB = "auto_carcrm_kb"     # 知识库（knowledge_documents / knowledge_chunks）


def sha256_password(raw: str) -> str:
    """项目当前用 sha256 存密码（与现有 chat_message._legacy_pwd 字段约定一致）；
    生产化建议改用 bcrypt。"""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_collections(db, expected: list[str]) -> None:
    existing = set(db.list_collection_names())
    for name in expected:
        if name not in existing:
            db.create_collection(name)
            print(f"  ✅ create collection: {name}")
        else:
            print(f"  ·  collection exists: {name}")


def ensure_indexes(db, plans: dict[str, list]) -> None:
    for coll, idx_list in plans.items():
        for keys, opts in idx_list:
            try:
                db[coll].create_index(keys, **opts)
            except Exception as e:
                print(f"  ⚠️  {coll}.{keys} 索引失败: {e}")


# ---------- 业务库 ----------
BUSINESS_COLLECTIONS = [
    "users",                  # 账号
    "vehicles",               # 车辆档案
    "maintenance_records",    # 保养记录
    "repair_histories",       # 历史维修
    "warranty_policies",      # 质保规则
    "diagnosis_sessions",     # 诊断会话
    "repair_orders",          # 报修单
    "qa_sessions",            # QA 会话
    "qa_messages",            # QA 消息（与历史 chat_message 并存）
    "qa_references",          # 引用溯源
    "user_feedbacks",         # 反馈
    "typical_cases",          # 典型案例
    "chat_message",           # 现有历史消息
]

BUSINESS_INDEXES = {
    "users": [
        ([("phone", ASCENDING)], {"unique": True}),
        ([("user_type", ASCENDING)], {}),
    ],
    "vehicles": [
        ([("vin", ASCENDING)], {"unique": True}),
        ([("owner_user_id", ASCENDING)], {}),
        ([("company_id", ASCENDING)], {}),
    ],
    "maintenance_records": [
        ([("vehicle_id", ASCENDING), ("maintenance_date", -1)], {}),
    ],
    "warranty_policies": [
        ([("vehicle_model", ASCENDING), ("component_category", ASCENDING)], {}),
        ([("state", ASCENDING)], {}),
    ],
    "diagnosis_sessions": [
        ([("user_id", ASCENDING), ("created_at", -1)], {}),
    ],
    "repair_orders": [
        ([("user_id", ASCENDING)], {}),
        ([("vehicle_id", ASCENDING)], {}),
        ([("state", ASCENDING)], {}),
        ([("service_station_id", ASCENDING)], {}),
    ],
    "qa_sessions": [
        ([("user_id", ASCENDING), ("created_at", -1)], {}),
    ],
    "qa_messages": [
        ([("session_id", ASCENDING), ("created_at", -1)], {}),
        ([("user_id", ASCENDING)], {}),
    ],
    "qa_references": [
        ([("message_id", ASCENDING)], {}),
        ([("chunk_id", ASCENDING)], {}),
    ],
    "user_feedbacks": [
        ([("message_id", ASCENDING)], {}),
        ([("user_id", ASCENDING)], {}),
    ],
    "typical_cases": [
        ([("vehicle_model", ASCENDING)], {}),
        ([("state", ASCENDING)], {}),
    ],
    "chat_message": [
        # 不指定 name，与 app/shared/clients/mongo_history_utils.py 自动生成的同名索引保持一致
        ([("session_id", ASCENDING), ("ts", -1)], {}),
    ],
}

DEFAULT_USERS = [
    # _id, name, phone, password (明文)，user_type, roles, company
    ("U90001", "系统管理员",   "13800000001", "admin123",   "knowledge_admin",          ["knowledge_admin", "after_sales_engineer"], "比亚迪商用车总部"),
    ("U20001", "李服务顾问",   "13800000002", "advisor123", "service_advisor",          ["service_advisor"],                         "深圳南山服务站"),
    ("U20002", "王技师",       "13800000003", "tech123",   "technician",               ["technician"],                              "深圳南山服务站"),
    ("U10001", "张司机",       "13800000010", "demo123",   "customer",                 ["customer"],                                 "某物流有限公司"),
    ("U10002", "王车队",       "13800000011", "demo123",   "fleet_admin",              ["fleet_admin", "customer"],                 "某物流有限公司"),
]


def seed_users(db, reset: bool) -> int:
    coll = db["users"]
    if reset:
        coll.delete_many({})
    now = datetime.now(timezone.utc).isoformat()
    docs = []
    for uid, name, phone, pwd, user_type, roles, company in DEFAULT_USERS:
        if coll.find_one({"_id": uid}):
            continue
        docs.append({
            "_id": uid,
            "name": name,
            "phone": phone,
            "password_hash": sha256_password(pwd),
            "user_type": user_type,
            "roles": roles,
            "company_id": "C10001" if "C1" not in (uid,) else None,
            "company_name": company,
            "dealer_id": None,
            "state": "active",
            "last_login_at": None,
            "created_at": now,
            "updated_at": now,
        })
    if docs:
        coll.insert_many(docs)
    return len(docs)


# ---------- 知识库 ----------
KNOWLEDGE_COLLECTIONS = [
    "knowledge_documents",
    "knowledge_chunks",
    "import_tasks",
]

KNOWLEDGE_INDEXES = {
    "knowledge_documents": [
        ([("vehicle_model", ASCENDING)], {"name": "vehicle_model"}),
        ([("doc_type", ASCENDING)], {"name": "doc_type"}),
        ([("state", ASCENDING)], {"name": "state"}),
    ],
    "knowledge_chunks": [
        ([("doc_id", ASCENDING), ("chunk_index", ASCENDING)], {"name": "doc_chunk"}),
        ([("metadata.vehicle_model", ASCENDING)], {"name": "meta_vehicle_model"}),
        ([("metadata.doc_type", ASCENDING)], {"name": "meta_doc_type"}),
        ([("state", ASCENDING)], {"name": "state"}),
    ],
    "import_tasks": [
        ([("doc_id", ASCENDING)], {"name": "doc_id"}),
        ([("task_state", ASCENDING)], {"name": "task_state"}),
    ],
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.getenv("MONGO_URL", DEFAULT_URL))
    ap.add_argument("--reset-users", action="store_true", help="清空 users 集合并重灌默认账号")
    args = ap.parse_args()

    print(f"连接 {args.url} ...")
    client = MongoClient(args.url, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
    except Exception as e:
        print(f"❌ 连不上 MongoDB: {e}")
        print("  提示：docker run -d -p 27017:27017 --name local-mongo -v mongodb_data:/data/db mongo:7")
        return 1
    print("✅ MongoDB ping 成功\n")

    # --- 业务库 ---
    print(f"== 业务库 {BUSINESS_DB} ==")
    biz = client[BUSINESS_DB]
    print("[collections]")
    ensure_collections(biz, BUSINESS_COLLECTIONS)
    print("[indexes]")
    ensure_indexes(biz, BUSINESS_INDEXES)
    print("[users seed]")
    n = seed_users(biz, args.reset_users)
    print(f"  插入默认账号 {n} 条（已存在的跳过）\n")

    # --- 知识库 ---
    print(f"== 知识库 {KNOWLEDGE_DB} ==")
    kn = client[KNOWLEDGE_DB]
    print("[collections]")
    ensure_collections(kn, KNOWLEDGE_COLLECTIONS)
    print("[indexes]")
    ensure_indexes(kn, KNOWLEDGE_INDEXES)
    print()

    # --- 总结 ---
    print("== 汇总 ==")
    print(f"业务库集合数: {len(biz.list_collection_names())}")
    print(f"知识库集合数: {len(kn.list_collection_names())}")
    print("默认账号（密码明文，登录测试用）：")
    for uid, name, phone, pwd, *_ in DEFAULT_USERS:
        print(f"  {uid}  {name:<8}  {phone}  /  {pwd}")
    print("\n请把以下变量写入 .env：")
    print(f"  MONGO_URL={args.url}")
    print(f"  MONGO_DB_NAME={BUSINESS_DB}")
    print(f"  MONGO_KNOWLEDGE_DB={KNOWLEDGE_DB}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
