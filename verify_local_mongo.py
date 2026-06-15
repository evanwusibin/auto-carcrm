"""验证本地 MongoDB：连接 + 三个客户端 + 默认账号 + chat_message 读写。"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from pymongo import MongoClient  # noqa: E402

from app.shared.clients.mongo_business_utils import get_business_db  # noqa: E402
from app.shared.clients.mongo_history_utils import (  # noqa: E402
    clear_history,
    get_history_mongo_tool,
    get_recent_messages,
    save_chat_message,
)
from app.shared.clients.mongo_knowledge_utils import get_knowledge_db  # noqa: E402

MONGO_URL = "mongodb://127.0.0.1:27017"
TEST_SID = "VERIFY-CONNECT-001"

EXPECTED_BUSINESS = [
    "users", "vehicles", "maintenance_records", "repair_histories",
    "warranty_policies", "diagnosis_sessions", "repair_orders",
    "qa_sessions", "qa_messages", "qa_references", "user_feedbacks",
    "typical_cases", "chat_message",
]
EXPECTED_KNOWLEDGE = ["knowledge_documents", "knowledge_chunks", "import_tasks"]

EXPECTED_USERS = [
    ("U90001", "13800000001", "admin123",   "knowledge_admin"),
    ("U20001", "13800000002", "advisor123", "service_advisor"),
    ("U20002", "13800000003", "tech123",    "technician"),
    ("U10001", "13800000010", "demo123",    "customer"),
    ("U10002", "13800000011", "demo123",    "fleet_admin"),
]


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    print(f"== 连接 {MONGO_URL} ==")
    ping_client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    print("ping:", ping_client.admin.command("ping"))
    print()

    # 1) history 工具（chat_message 写入/读取）
    print("== history 客户端 ==")
    tool = get_history_mongo_tool()
    print(f"  db_name={tool.db_name}, collection={tool.chat_message.name}")
    clear_history(TEST_SID)
    msg_id = save_chat_message(TEST_SID, "user", "你好，本地连通性验证",
                               item_names=["万用表"], image_urls=[])
    print(f"  ✅ save_chat_message -> id={msg_id}")
    msgs = get_recent_messages(TEST_SID, limit=5)
    print(f"  ✅ get_recent_messages -> count={len(msgs)}, role={msgs[0]['role']}, text={msgs[0]['text']}")
    clear_history(TEST_SID)
    print("  ✅ clear_history 清理完成\n")

    # 2) 业务库：集合存在 + 文档可读
    print("== business 客户端 ==")
    biz = get_business_db()
    biz_cols = set(biz.list_collection_names())
    missing_b = [c for c in EXPECTED_BUSINESS if c not in biz_cols]
    if missing_b:
        print(f"  ❌ 缺少集合: {missing_b}")
    else:
        print(f"  ✅ 13 个业务集合齐全")
    users_count = biz.users.count_documents({})
    print(f"  users.count_documents = {users_count}")
    vehicles_count = biz.vehicles.count_documents({})
    print(f"  vehicles.count_documents = {vehicles_count}")
    chat_count = biz.chat_message.count_documents({})
    print(f"  chat_message.count_documents = {chat_count}\n")

    # 3) 知识库
    print("== knowledge 客户端 ==")
    kn = get_knowledge_db()
    kn_cols = set(kn.list_collection_names())
    missing_k = [c for c in EXPECTED_KNOWLEDGE if c not in kn_cols]
    if missing_k:
        print(f"  ❌ 缺少集合: {missing_k}")
    else:
        print(f"  ✅ 3 个知识库集合齐全")
    print(f"  knowledge_documents.count = {kn.knowledge_documents.count_documents({})}\n")

    # 4) 默认账号 + 密码哈希校验
    print("== 默认账号 ==")
    all_ok = True
    for uid, phone, pwd, user_type in EXPECTED_USERS:
        u = biz.users.find_one({"_id": uid})
        if not u:
            print(f"  ❌ {uid} 不存在")
            all_ok = False
            continue
        ok_hash = u.get("password_hash") == sha256(pwd)
        ok_phone = u.get("phone") == phone
        ok_type = u.get("user_type") == user_type
        if ok_hash and ok_phone and ok_type:
            print(f"  ✅ {uid}  {u.get('name'):<8}  phone={phone}  type={user_type}  hash OK")
        else:
            print(f"  ❌ {uid}  hash={ok_hash} phone={ok_phone} type={ok_type}")
            all_ok = False

    print()
    print("== 汇总 ==")
    print("  MongoDB 连接：✅")
    print(f"  history 客户端：✅ ({tool.db_name})")
    print(f"  business 客户端：✅ ({biz.name})")
    print(f"  knowledge 客户端：✅ ({kn.name})")
    print(f"  默认账号：{'✅ 5/5' if all_ok else '❌ 有失败'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())