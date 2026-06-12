# MongoDB 集合设计

> 文档编号：DOC-04-01 | 版本：v1.0 | 更新时间：2026-06-12

---

## 一、集合总览

| 集合名称 | 中文名 | 主要用途 |
|---|---|---|
| `users` | 用户集合 | 存储所有用户账号信息 |
| `vehicles` | 车辆集合 | 存储车辆档案信息 |
| `maintenance_records` | 保养记录集合 | 存储车辆保养历史 |
| `repair_histories` | 维修记录集合 | 存储历史维修工单 |
| `warranty_policies` | 质保规则集合 | 存储结构化质保规则 |
| `knowledge_documents` | 知识文档集合 | 存储上传的知识资料元信息 |
| `knowledge_chunks` | 知识片段集合 | 存储 Chunk 文本 + 向量 + 元数据 |
| `import_tasks` | 导入任务集合 | 存储文档解析任务进度 |
| `diagnosis_sessions` | 诊断会话集合 | 存储自助诊断过程 |
| `repair_orders` | 报修单集合 | 存储智能报修工单 |
| `qa_sessions` | 问答会话集合 | 存储多轮对话上下文 |
| `qa_messages` | 问答消息集合 | 存储每条问答记录 |
| `qa_references` | 答案引用集合 | 存储答案引用的知识片段 |
| `user_feedbacks` | 用户反馈集合 | 存储点赞/点踩/错误反馈 |
| `typical_cases` | 典型案例集合 | 存储审核后的典型维修案例 |

---

## 二、各集合详细设计

### 2.1 users（用户集合）

```json
{
  "_id": "U10001",
  "name": "张三",
  "phone": "13800000000",
  "password_hash": "bcrypt_hash_string",
  "user_type": "customer",
  "roles": ["customer"],
  "company_id": "C10001",
  "company_name": "某物流有限公司",
  "region": "华南",
  "dealer_id": null,
  "state": "active",
  "last_login_at": "2026-06-12T10:00:00",
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-06-12T10:00:00"
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `_id` | string | ✅ | 用户唯一ID |
| `name` | string | ✅ | 用户姓名 |
| `phone` | string | ✅ | 手机号，唯一索引 |
| `password_hash` | string | ✅ | bcrypt加密密码 |
| `user_type` | enum | ✅ | customer/fleet_admin/service_advisor/technician/after_sales_engineer/knowledge_admin |
| `roles` | array | ✅ | 角色列表，支持多角色 |
| `company_id` | string | 可空 | 所属企业ID |
| `dealer_id` | string | 可空 | 所属经销商ID |
| `state` | enum | ✅ | active/disabled/deleted |

---

### 2.2 vehicles（车辆集合）

```json
{
  "_id": "V10001",
  "vin": "LXXXXXXXXXXXXXXXX",
  "plate_number": "粤A12345",
  "vehicle_model": "T5",
  "vehicle_type": "轻卡",
  "fuel_type": "纯电动",
  "color": "白色",
  "engine_no": "",
  "motor_no": "M2024XXXXXX",
  "battery_no": "B2024XXXXXX",
  "purchase_date": "2024-03-01",
  "delivery_date": "2024-03-10",
  "current_mileage": 68000,
  "owner_user_id": "U10001",
  "company_id": "C10001",
  "dealer_id": "D10001",
  "state": "active",
  "created_at": "2024-03-10T00:00:00",
  "updated_at": "2026-06-12T10:00:00"
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `vin` | string | ✅ | 车架号，唯一索引 |
| `vehicle_model` | string | ✅ | 车型，用于知识检索过滤 |
| `purchase_date` | date | ✅ | 购车日期，质保计算基准 |
| `delivery_date` | date | ✅ | 交付日期，质保计算备用 |
| `current_mileage` | int | ✅ | 当前里程，质保和保养判断 |
| `state` | enum | ✅ | active/repairing/scrapped/transferred/inactive |

---

### 2.3 maintenance_records（保养记录集合）

```json
{
  "_id": "MR10001",
  "vehicle_id": "V10001",
  "vin": "LXXXXXXXXXXXXXXXX",
  "maintenance_date": "2026-03-01",
  "mileage_at_maintenance": 60000,
  "maintenance_type": "regular",
  "service_station_id": "S10001",
  "service_station_name": "深圳某服务站",
  "technician_name": "李技师",
  "items": [
    "更换齿轮油",
    "检查制动系统",
    "检查动力电池",
    "更换空调滤芯"
  ],
  "cost": 1200.00,
  "next_maintenance_mileage": 70000,
  "next_maintenance_date": "2027-03-01",
  "notes": "车主反映空调偶有异响，已检查并处理",
  "state": "completed",
  "created_at": "2026-03-01T14:00:00"
}
```

---

### 2.4 warranty_policies（质保规则集合）

```json
{
  "_id": "WP10001",
  "vehicle_model": "T5",
  "component_category": "三电系统",
  "component_name": "动力电池",
  "warranty_years": 5,
  "warranty_mileage": 200000,
  "warranty_description": "动力电池在质保期内出现非人为损坏的容量衰减或故障，享受免费维修或更换服务",
  "conditions": [
    "车辆在规定质保期限和里程内",
    "按规定周期完成保养并保留记录",
    "故障非人为操作不当导致",
    "车辆未私自改装"
  ],
  "exclusions": [
    "事故导致的物理损坏",
    "泡水或进液导致的损坏",
    "私自改装后导致的故障",
    "过充或过放导致的损坏",
    "超过质保里程或年限"
  ],
  "claim_process": "联系授权服务站 → 服务站检测 → 提交质保申请 → 厂家审核 → 维修处理",
  "version": "v1.0",
  "effective_date": "2024-01-01",
  "expire_date": null,
  "state": "active",
  "created_at": "2024-01-01T00:00:00"
}
```

---

### 2.5 knowledge_documents（知识文档集合）

```json
{
  "_id": "DOC10001",
  "doc_name": "T5轻卡质保手册",
  "doc_type": "warranty_manual",
  "vehicle_model": "T5",
  "vehicle_type": "轻卡",
  "applicable_components": ["动力电池", "驱动电机", "电机控制器"],
  "business_category": "质保",
  "version": "v1.0",
  "file_url": "/files/docs/T5_warranty_v1.0.pdf",
  "file_type": "pdf",
  "file_size_kb": 2048,
  "total_pages": 45,
  "total_chunks": 120,
  "effective_date": "2026-01-01",
  "expire_date": "2027-01-01",
  "visible_roles": ["customer", "service_advisor", "technician", "after_sales_engineer", "knowledge_admin"],
  "state": "published",
  "upload_by": "U90001",
  "review_by": "U90002",
  "review_comment": "内容完整，格式正常，允许发布",
  "created_at": "2026-06-01T10:00:00",
  "published_at": "2026-06-02T09:00:00",
  "updated_at": "2026-06-02T09:00:00"
}
```

**doc_type 枚举：**

| 值 | 含义 |
|---|---|
| `maintenance_manual` | 保养手册 |
| `warranty_manual` | 质保手册 |
| `repair_manual` | 维修手册 |
| `typical_case` | 典型案例方案 |
| `faq` | 常见问题解答 |
| `technical_bulletin` | 技术通报 |
| `training_material` | 培训材料 |

---

### 2.6 knowledge_chunks（知识片段集合）⭐ 核心集合

```json
{
  "_id": "CHK10001",
  "doc_id": "DOC10001",
  "chunk_text": "动力电池质保期限为5年或20万公里（以先到者为准）。在质保期内，因产品质量问题导致的电池故障，提供免费维修或更换服务。质保期的计算从车辆交付日期开始。",
  "embedding": [0.012, -0.023, 0.087, 0.145, ...],
  "chunk_index": 12,
  "token_count": 95,
  "metadata": {
    "doc_type": "warranty_manual",
    "doc_name": "T5轻卡质保手册",
    "vehicle_model": "T5",
    "vehicle_type": "轻卡",
    "component": "动力电池",
    "component_category": "三电系统",
    "section_title": "三电系统质保说明",
    "page_no": 18,
    "version": "v1.0",
    "effective_date": "2026-01-01",
    "expire_date": "2027-01-01",
    "visible_roles": ["customer", "service_advisor", "technician", "after_sales_engineer", "knowledge_admin"],
    "keywords": ["质保", "动力电池", "5年", "20万公里", "免费维修"]
  },
  "state": "active",
  "created_at": "2026-06-01T10:30:00"
}
```

> ⚠️ **重要说明**：`embedding` 字段存储向量，需要在 MongoDB Atlas 上创建 `vectorSearch` 类型索引，索引字段为 `embedding`，维度与所用 Embedding 模型一致（bge-large-zh 为 1024 维）。

---

### 2.7 import_tasks（导入任务集合）

```json
{
  "_id": "TASK10001",
  "doc_id": "DOC10001",
  "task_type": "full_import",
  "task_state": "success",
  "total_pages": 45,
  "total_chunks": 120,
  "success_chunks": 120,
  "failed_chunks": 0,
  "error_details": [],
  "started_at": "2026-06-01T10:00:00",
  "finished_at": "2026-06-01T10:05:30",
  "duration_seconds": 330,
  "created_at": "2026-06-01T10:00:00"
}
```

---

### 2.8 diagnosis_sessions（诊断会话集合）

```json
{
  "_id": "DS10001",
  "user_id": "U10001",
  "vehicle_id": "V10001",
  "vin": "LXXXXXXXXXXXXXXXX",
  "vehicle_model": "T5",
  "current_mileage": 68000,
  "fault_description": "车辆启动不了，仪表有电，但是挂不上挡",
  "fault_images": ["/files/images/DS10001_1.jpg"],
  "fault_codes": ["P0A0F"],
  "intent_type": "startup_failure",
  "extracted_entities": {
    "fault_symptom": ["无法启动", "挂不上挡"],
    "dashboard_status": "仪表有电",
    "fault_codes": ["P0A0F"]
  },
  "risk_level": "high",
  "diagnosis_result": {
    "possible_causes": [
      "低压电瓶电量不足，导致高压系统无法上电",
      "高压互锁回路异常",
      "挡位传感器信号异常"
    ],
    "suggestion": "建议停止使用，不要强行启动，联系服务站或拨打救援电话",
    "references": ["CHK20045", "CHK20046", "CASE10012"]
  },
  "converted_to_repair": true,
  "repair_order_id": "RO10001",
  "state": "converted_to_order",
  "created_at": "2026-06-12T10:52:42",
  "updated_at": "2026-06-12T11:10:00"
}
```

---

### 2.9 repair_orders（报修单集合）⭐ 核心业务集合

```json
{
  "_id": "RO10001",
  "order_no": "RO20260612001",
  "user_id": "U10001",
  "user_name": "张三",
  "user_phone": "13800000000",
  "vehicle_id": "V10001",
  "vin": "LXXXXXXXXXXXXXXXX",
  "vehicle_model": "T5",
  "current_mileage": 68000,
  "diagnosis_session_id": "DS10001",
  "fault_description": "车辆启动不了，仪表有电，但是挂不上挡",
  "fault_codes": ["P0A0F"],
  "fault_images": ["/files/images/DS10001_1.jpg"],
  "risk_level": "high",
  "diagnosis_summary": "可能原因：低压电瓶电量不足 / 高压互锁异常",
  "warranty_precheck": {
    "result": "manual_review_required",
    "is_within_time": true,
    "warranty_expire_date": "2029-03-01",
    "is_within_mileage": true,
    "warranty_mileage_limit": 200000,
    "maintenance_status": "normal",
    "last_maintenance_date": "2026-03-01",
    "last_maintenance_mileage": 60000,
    "reason": "时间和里程均在质保范围内，但故障原因需服务站检测后确认是否属于质量问题"
  },
  "location": "广东省深圳市南山区某路口",
  "can_drive": false,
  "preferred_time": "2026-06-12 14:00",
  "service_station_id": "S10001",
  "service_station_name": "深圳南山服务站",
  "assigned_advisor_id": "U20001",
  "assigned_technician_id": "U20002",
  "inspection_result": null,
  "repair_conclusion": null,
  "warranty_final_result": null,
  "total_cost": null,
  "customer_confirmed_at": null,
  "customer_rating": null,
  "customer_review": null,
  "state": "accepted",
  "state_history": [
    {"state": "submitted", "time": "2026-06-12T10:55:00", "operator": "U10001"},
    {"state": "accepted", "time": "2026-06-12T11:02:00", "operator": "U20001"}
  ],
  "created_at": "2026-06-12T10:55:00",
  "updated_at": "2026-06-12T11:02:00"
}
```

---

### 2.10 qa_messages（问答消息集合）

```json
{
  "_id": "QA10001",
  "session_id": "QAS10001",
  "user_id": "U10001",
  "vehicle_id": "V10001",
  "question": "动力电池坏了还能保修吗？",
  "rewritten_question": "T5轻卡动力电池故障是否在质保范围内，质保期限和条件是什么？",
  "intent_type": "warranty_query",
  "extracted_entities": {
    "vehicle_model": "T5",
    "component": "动力电池"
  },
  "retrieval_results": [
    {"chunk_id": "CHK10001", "score": 0.92, "rerank_score": 0.95},
    {"chunk_id": "CHK10002", "score": 0.85, "rerank_score": 0.82}
  ],
  "answer": "根据《T5轻卡质保手册》，动力电池质保期限为5年或20万公里（以先到者为准）。在质保期内，因产品质量问题导致的电池故障，可享受免费维修或更换服务。需要注意：质保不包含事故损坏、泡水损坏、私自改装等情况。建议联系授权服务站进行检测，以确认是否属于质量问题。",
  "answer_state": "success",
  "has_references": true,
  "model_name": "qwen2.5-72b",
  "latency_ms": 2340,
  "created_at": "2026-06-12T10:30:00"
}
```

---

### 2.11 qa_references（答案引用集合）

```json
{
  "_id": "REF10001",
  "message_id": "QA10001",
  "doc_id": "DOC10001",
  "chunk_id": "CHK10001",
  "doc_name": "T5轻卡质保手册",
  "doc_type": "warranty_manual",
  "section_title": "三电系统质保说明",
  "page_no": 18,
  "quote_text": "动力电池质保期限为5年或20万公里（以先到者为准）……",
  "retrieval_score": 0.92,
  "rerank_score": 0.95,
  "created_at": "2026-06-12T10:30:00"
}
```

---

### 2.12 user_feedbacks（用户反馈集合）

```json
{
  "_id": "FB10001",
  "message_id": "QA10001",
  "user_id": "U10001",
  "feedback_type": "negative",
  "reason_type": "answer_incomplete",
  "reason_label": "回答不完整",
  "comment": "没有说清楚超过里程但没超时间的情况怎么处理",
  "created_at": "2026-06-12T10:35:00"
}
```

**feedback_type 枚举：**

| 值 | 含义 |
|---|---|
| `positive` | 点赞 |
| `negative` | 点踩 |

**reason_type 枚举：**

| 值 | 含义 |
|---|---|
| `no_answer` | 未找到答案 |
| `answer_inaccurate` | 答案不准确 |
| `answer_incomplete` | 回答不完整 |
| `source_wrong` | 引用来源错误 |
| `content_expired` | 内容已过期 |
| `answer_too_vague` | 回答太泛化 |
| `need_human` | 需要人工确认 |

---

### 2.13 typical_cases（典型案例集合）

```json
{
  "_id": "CASE10001",
  "case_no": "CASE20260612001",
  "vehicle_model": "T5",
  "fault_system": "动力系统",
  "fault_symptom": "车辆无法启动，低压电瓶正常，仪表上电但无法READY",
  "fault_codes": ["P0A0F", "P1D00"],
  "mileage_range": "50000-80000",
  "cause_analysis": "DC-DC转换器故障导致低压侧供电异常，整车控制器无法完成READY流程",
  "inspection_steps": [
    "检查低压电瓶电压（应≥12V）",
    "检查DC-DC输出电压（正常14V±0.5V）",
    "读取整车控制器故障码",
    "检查DC-DC控制器连接器"
  ],
  "solution": "更换DC-DC转换器，清除故障码，验证车辆正常启动",
  "result": "车辆恢复正常，行驶500km后复查无异常",
  "lesson_learned": "T5车型在5-8万公里区间，DC-DC故障率较高，建议保养时增加DC-DC输出电压检查项",
  "tags": ["无法启动", "DC-DC", "高压上电", "READY故障"],
  "source_repair_order_id": "RO10001",
  "submitted_by": "U20002",
  "reviewed_by": "U90001",
  "state": "published",
  "created_at": "2026-06-12T15:00:00",
  "published_at": "2026-06-13T09:00:00"
}
```

---

## 三、索引设计建议

```javascript
// users 集合
db.users.createIndex({ "phone": 1 }, { unique: true })
db.users.createIndex({ "user_type": 1 })

// vehicles 集合
db.vehicles.createIndex({ "vin": 1 }, { unique: true })
db.vehicles.createIndex({ "owner_user_id": 1 })
db.vehicles.createIndex({ "company_id": 1 })

// knowledge_chunks 集合（向量索引在 Atlas 控制台配置）
db.knowledge_chunks.createIndex({ "doc_id": 1 })
db.knowledge_chunks.createIndex({ "metadata.vehicle_model": 1 })
db.knowledge_chunks.createIndex({ "metadata.doc_type": 1 })
db.knowledge_chunks.createIndex({ "state": 1 })

// repair_orders 集合
db.repair_orders.createIndex({ "user_id": 1 })
db.repair_orders.createIndex({ "vehicle_id": 1 })
db.repair_orders.createIndex({ "state": 1 })
db.repair_orders.createIndex({ "service_station_id": 1 })

// qa_messages 集合
db.qa_messages.createIndex({ "session_id": 1 })
db.qa_messages.createIndex({ "user_id": 1 })
db.qa_messages.createIndex({ "created_at": -1 })
```

---

*文档版本：v1.0 | 更新时间：2026-06-12*
