# FastAPI 接口文档

> 文档编号：DOC-05-01 | 版本：v1.0 | 更新时间：2026-06-12

---

## 一、接口规范

### 1.1 基础信息

| 项目 | 说明 |
|---|---|
| 基础路径 | `https://api.auto-carcrm.com/api/v1` |
| 认证方式 | JWT Bearer Token |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 时间格式 | ISO 8601：`2026-06-12T10:00:00` |

### 1.2 通用响应结构

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "timestamp": "2026-06-12T10:00:00"
}
```

**错误码规范：**

| code | 含义 |
|---|---|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 未授权 |
| 1003 | 权限不足 |
| 1004 | 资源不存在 |
| 2001 | 文档解析失败 |
| 2002 | 向量化失败 |
| 3001 | 检索无结果 |
| 3002 | 模型调用失败 |
| 5000 | 服务器内部错误 |

---

## 二、认证接口

### 2.1 用户登录

```
POST /auth/login
```

**请求体：**
```json
{
  "phone": "13800000000",
  "password": "your_password"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user_info": {
      "user_id": "U10001",
      "name": "张三",
      "user_type": "customer",
      "roles": ["customer"]
    }
  }
}
```

### 2.2 用户注册

```
POST /auth/register
```

**请求体：**
```json
{
  "name": "张三",
  "phone": "13800000000",
  "password": "your_password",
  "user_type": "customer",
  "company_name": "某物流有限公司"
}
```

---

## 三、知识库管理接口

### 3.1 上传知识文档

```
POST /knowledge/documents/upload
Content-Type: multipart/form-data
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | file | ✅ | 上传文件（PDF/Word/Excel/TXT） |
| `doc_name` | string | ✅ | 文档名称 |
| `doc_type` | string | ✅ | 文档类型枚举 |
| `vehicle_model` | string | ✅ | 适用车型，多个用逗号分隔 |
| `vehicle_type` | string | 可选 | 车辆类型（轻卡/重卡/客车等） |
| `version` | string | ✅ | 版本号，如 v1.0 |
| `effective_date` | string | ✅ | 生效日期 |
| `expire_date` | string | 可选 | 失效日期 |
| `visible_roles` | string | 可选 | 可见角色，逗号分隔 |

**响应：**
```json
{
  "code": 0,
  "message": "上传成功",
  "data": {
    "doc_id": "DOC10001",
    "doc_name": "T5轻卡质保手册",
    "state": "uploaded",
    "file_url": "/files/docs/T5_warranty_v1.0.pdf"
  }
}
```

---

### 3.2 触发文档解析

```
POST /knowledge/documents/{doc_id}/parse
```

**响应：**
```json
{
  "code": 0,
  "message": "解析任务已创建",
  "data": {
    "task_id": "TASK10001",
    "doc_id": "DOC10001",
    "task_state": "pending",
    "created_at": "2026-06-12T10:00:00"
  }
}
```

---

### 3.3 查询导入任务状态

```
GET /knowledge/import-tasks/{task_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "TASK10001",
    "doc_id": "DOC10001",
    "task_state": "running",
    "total_pages": 45,
    "total_chunks": 120,
    "success_chunks": 80,
    "failed_chunks": 0,
    "progress_percent": 67,
    "started_at": "2026-06-12T10:00:00",
    "estimated_finish": "2026-06-12T10:05:00"
  }
}
```

---

### 3.4 审核发布文档

```
POST /knowledge/documents/{doc_id}/publish
```

**请求体：**
```json
{
  "review_result": "approved",
  "review_comment": "内容完整，格式正常，允许发布"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "发布成功",
  "data": {
    "doc_id": "DOC10001",
    "state": "published",
    "published_at": "2026-06-12T10:30:00"
  }
}
```

---

### 3.5 下线文档

```
POST /knowledge/documents/{doc_id}/offline
```

**请求体：**
```json
{
  "reason": "该版本已过期，请使用新版本"
}
```

---

### 3.6 查询文档列表

```
GET /knowledge/documents
```

**Query 参数：**

| 参数 | 类型 | 说明 |
|---|---|---|
| `doc_type` | string | 按类型过滤 |
| `vehicle_model` | string | 按车型过滤 |
| `state` | string | 按状态过滤 |
| `page` | int | 页码，默认1 |
| `page_size` | int | 每页数量，默认20 |

---

## 四、智能问答接口

### 4.1 发起问答

```
POST /qa/ask
```

**请求体：**
```json
{
  "session_id": "QAS10001",
  "question": "T5轻卡行驶6万公里需要做哪些保养？",
  "vehicle_id": "V10001",
  "vehicle_model": "T5",
  "context": {
    "mileage": 60000,
    "role": "customer"
  },
  "top_k": 5,
  "stream": false
}
```

**请求参数说明：**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `session_id` | string | 可选 | 会话ID，传入则保留多轮上下文 |
| `question` | string | ✅ | 用户问题 |
| `vehicle_id` | string | 可选 | 车辆ID，用于结构化查询 |
| `vehicle_model` | string | 可选 | 车型，用于检索过滤 |
| `context` | object | 可选 | 附加上下文信息 |
| `top_k` | int | 可选 | 召回数量，默认5 |
| `stream` | bool | 可选 | 是否流式输出，默认false |

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "message_id": "QA10001",
    "session_id": "QAS10001",
    "question": "T5轻卡行驶6万公里需要做哪些保养？",
    "rewritten_question": "T5轻卡60000公里保养项目和注意事项",
    "intent_type": "maintenance_query",
    "answer": "根据《T5轻卡保养手册》，行驶至60000公里时，需要重点完成以下保养项目：\n\n1. **必做项目**：\n   - 更换减速器/传动系统润滑油\n   - 检查制动系统（刹车片厚度、制动液）\n   - 检查/更换空调滤芯和空气滤芯\n   - 检查动力电池冷却系统\n\n2. **检查项目**：\n   - 检查轮胎磨损和气压\n   - 检查底盘螺栓紧固状态\n   - 检查灯光系统\n\n建议携带购车资料和前次保养记录前往授权服务站完成保养，以确保质保有效性。",
    "answer_state": "success",
    "need_more_info": false,
    "references": [
      {
        "doc_id": "DOC10002",
        "chunk_id": "CHK20045",
        "doc_name": "T5轻卡保养手册",
        "doc_type": "maintenance_manual",
        "section_title": "60000公里保养项目",
        "page_no": 28,
        "quote_text": "车辆行驶至60000公里时，应完成以下保养项目……",
        "score": 0.92
      }
    ],
    "latency_ms": 2340,
    "created_at": "2026-06-12T10:30:00"
  }
}
```

---

### 4.2 创建问答会话

```
POST /qa/sessions
```

**请求体：**
```json
{
  "vehicle_id": "V10001",
  "session_title": "关于T5保养问题"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "QAS10001",
    "created_at": "2026-06-12T10:00:00"
  }
}
```

---

### 4.3 提交答案反馈

```
POST /qa/messages/{message_id}/feedback
```

**请求体：**
```json
{
  "feedback_type": "negative",
  "reason_type": "answer_incomplete",
  "comment": "没有说清楚超过里程但没超时间的情况怎么处理"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "反馈成功",
  "data": {
    "feedback_id": "FB10001"
  }
}
```

---

### 4.4 查询会话历史

```
GET /qa/sessions/{session_id}/messages
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "QAS10001",
    "messages": [
      {
        "message_id": "QA10001",
        "question": "T5轻卡行驶6万公里需要做哪些保养？",
        "answer": "根据保养手册……",
        "created_at": "2026-06-12T10:30:00"
      }
    ],
    "total": 1
  }
}
```

---

## 五、智能诊断接口

### 5.1 发起智能诊断

```
POST /diagnosis/sessions
```

**请求体：**
```json
{
  "vehicle_id": "V10001",
  "fault_description": "车辆启动不了，仪表有电，但是挂不上挡",
  "fault_codes": ["P0A0F"],
  "current_mileage": 68000,
  "fault_images": []
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "DS10001",
    "intent_type": "startup_failure",
    "risk_level": "high",
    "risk_label": "高风险",
    "need_more_info": false,
    "missing_fields": [],
    "diagnosis_result": {
      "possible_causes": [
        "低压电瓶电量不足，导致高压系统无法上电",
        "高压互锁回路异常",
        "挡位传感器信号异常"
      ],
      "suggestion": "建议停止使用，不要强行启动，立即联系服务站或拨打救援电话",
      "action_recommendation": "repair"
    },
    "references": [
      {
        "doc_name": "T5轻卡维修手册",
        "section_title": "动力系统故障排查",
        "page_no": 56,
        "score": 0.89
      }
    ],
    "created_at": "2026-06-12T10:52:42"
  }
}
```

**risk_level 说明：**

| 值 | 中文 | 建议动作 |
|---|---|---|
| `low` | 低风险 | 可继续观察或自查 |
| `medium` | 中风险 | 建议预约服务站 |
| `high` | 高风险 | 建议停止使用并立即报修 |
| `emergency` | 紧急 | 建议救援/拖车 |

---

## 六、车辆管理接口

### 6.1 绑定车辆

```
POST /vehicles/bind
```

**请求体：**
```json
{
  "vin": "LXXXXXXXXXXXXXXXX",
  "plate_number": "粤A12345",
  "current_mileage": 68000
}
```

**响应：**
```json
{
  "code": 0,
  "message": "车辆绑定成功",
  "data": {
    "vehicle_id": "V10001",
    "vin": "LXXXXXXXXXXXXXXXX",
    "vehicle_model": "T5",
    "vehicle_type": "轻卡",
    "purchase_date": "2024-03-01"
  }
}
```

---

### 6.2 查询车辆保养状态

```
GET /vehicles/{vehicle_id}/maintenance-status
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "vehicle_id": "V10001",
    "vehicle_model": "T5",
    "current_mileage": 68000,
    "last_maintenance": {
      "date": "2026-03-01",
      "mileage": 60000,
      "items": ["更换齿轮油", "检查制动系统"]
    },
    "next_maintenance": {
      "recommended_mileage": 70000,
      "recommended_date": "2027-03-01",
      "status": "normal",
      "status_label": "保养状态正常",
      "overdue": false,
      "km_until_next": 2000
    }
  }
}
```

---

### 6.3 质保预判查询

```
POST /vehicles/{vehicle_id}/warranty-precheck
```

**请求体：**
```json
{
  "component": "动力电池",
  "fault_description": "电池充不上电，续航明显下降"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "vehicle_id": "V10001",
    "component": "动力电池",
    "precheck_result": "likely_in_warranty",
    "precheck_label": "初步判断可能在保",
    "details": {
      "is_within_time": true,
      "warranty_expire_date": "2029-03-01",
      "days_remaining": 991,
      "is_within_mileage": true,
      "warranty_mileage_limit": 200000,
      "km_remaining": 132000,
      "maintenance_status": "normal",
      "last_maintenance_date": "2026-03-01"
    },
    "warranty_rules_applied": [
      "动力电池质保期5年或20万公里（以先到者为准）",
      "需按规定周期保养，本车保养记录正常"
    ],
    "disclaimer": "本结果仅为初步预判，最终质保结论以授权服务站检测结果为准",
    "reference_doc": "T5轻卡质保手册 v1.0 第3.2节"
  }
}
```

---

## 七、报修单接口

### 7.1 创建报修单

```
POST /repair-orders
```

**请求体：**
```json
{
  "vehicle_id": "V10001",
  "diagnosis_session_id": "DS10001",
  "fault_description": "车辆启动不了，仪表有电，但是挂不上挡",
  "fault_codes": ["P0A0F"],
  "fault_images": [],
  "current_mileage": 68000,
  "location": "广东省深圳市南山区某路口",
  "can_drive": false,
  "preferred_time": "2026-06-12 14:00",
  "service_station_id": "S10001",
  "contact_name": "张三",
  "contact_phone": "13800000000"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "报修单提交成功",
  "data": {
    "repair_order_id": "RO10001",
    "order_no": "RO20260612001",
    "state": "submitted",
    "service_station_name": "深圳南山服务站",
    "warranty_precheck": {
      "result": "manual_review_required",
      "reason": "时间和里程均在质保范围内，但故障原因需服务站检测后确认"
    },
    "created_at": "2026-06-12T10:55:00"
  }
}
```

---

### 7.2 查询报修单状态

```
GET /repair-orders/{repair_order_id}
```

**响应：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "repair_order_id": "RO10001",
    "order_no": "RO20260612001",
    "state": "inspecting",
    "state_label": "检测中",
    "service_station_name": "深圳南山服务站",
    "assigned_technician": "李技师",
    "state_history": [
      {"state": "submitted", "time": "2026-06-12T10:55:00", "label": "已提交"},
      {"state": "accepted", "time": "2026-06-12T11:02:00", "label": "已受理"},
      {"state": "inspecting", "time": "2026-06-12T14:15:00", "label": "检测中"}
    ],
    "estimated_complete": "2026-06-12T17:00:00"
  }
}
```

---

### 7.3 查询我的报修单列表

```
GET /repair-orders/my
```

**Query 参数：**

| 参数 | 说明 |
|---|---|
| `state` | 按状态过滤 |
| `vehicle_id` | 按车辆过滤 |
| `page` | 页码 |
| `page_size` | 每页数量 |

---

### 7.4 经销商接单

```
POST /repair-orders/{repair_order_id}/accept
```

**请求体：**
```json
{
  "comment": "已受理，安排下午14:00进行检测",
  "estimated_time": "2026-06-12T14:00:00"
}
```

---

### 7.5 填写维修结论

```
POST /repair-orders/{repair_order_id}/conclusion
```

**请求体：**
```json
{
  "fault_confirmed": "DC-DC转换器故障，导致整车无法READY",
  "fault_cause": "DC-DC转换器内部电容老化失效",
  "repair_actions": [
    "更换DC-DC转换器总成",
    "清除整车故障码",
    "验证车辆正常启动"
  ],
  "warranty_final_result": "in_warranty",
  "warranty_note": "属于三电系统质量问题，在质保范围内",
  "total_cost": 0,
  "parts_replaced": ["DC-DC转换器"],
  "submit_as_case": true
}
```

---

## 八、管理端接口

### 8.1 高频问题统计

```
GET /admin/analytics/top-questions
```

**Query 参数：**

| 参数 | 说明 |
|---|---|
| `days` | 统计天数，默认30 |
| `intent_type` | 按意图类型过滤 |
| `limit` | 返回条数，默认20 |

**响应：**
```json
{
  "code": 0,
  "data": {
    "period": "2026-05-13 ~ 2026-06-12",
    "total_questions": 1240,
    "top_questions": [
      {
        "question_pattern": "车辆质保相关咨询",
        "count": 320,
        "percentage": 25.8,
        "intent_type": "warranty_query"
      }
    ]
  }
}
```

---

### 8.2 无答案问题列表

```
GET /admin/analytics/no-answer-questions
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "total": 45,
    "items": [
      {
        "question": "充电桩故障和车辆故障怎么区分",
        "count": 12,
        "last_asked": "2026-06-12T09:30:00",
        "suggested_action": "补充充电系统故障排查知识"
      }
    ]
  }
}
```

---

*文档版本：v1.0 | 更新时间：2026-06-12*
