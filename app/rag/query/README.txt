[rag/query] 查询服务层执行顺序说明

一、主体确认阶段（入口，有分流逻辑）
  01. item_name_confirm_service.py
      - 主体确认服务
      - 作用：识别当前问题涉及哪个知识主体，并完成问题改写
      - 三种分支：
        A. 确认主体（score >= 0.55）
           → state['item_names'] = 确认列表
           → 继续进入意图识别
        B. 候选主体（0.45 < score < 0.55）
           → state['candidate_item_names'] = 候选列表
           → state['answer'] = 候选确认提示
           → 提前进入答案输出，等待用户点选候选
        C. 未识别主体（score <= 0.45 或无结果）
           → state['answer'] = 无匹配提示
           → 提前进入答案输出
      - 候选确认流程：
        1. 后端返回 candidate_item_names 字段
        2. 前端渲染可点击候选按钮
        3. 用户点击后，将候选名 + 原始问题重新提交
        4. 重新进入主体确认，此时 LLM 会直接识别出确认主体

二、意图与实体识别（仅确认主体后进入）
  02. intent_recognition_service.py
      - 意图识别服务
      - 作用：判断用户问题属于质保、保养、故障、案例、普通问答等哪一类

  03. entity_extraction_service.py
      - 实体抽取服务
      - 作用：抽取车型、文档类型、故障码、部件等结构化实体

三、多路并行召回（RRF 前）
  04. embedding_search_service.py
      - 向量检索
      - 作用：基于混合向量从 Milvus 中召回语义最相关 chunks

  05. keyword_search_service.py
      - BM25 关键词检索
      - 作用：按关键词命中次数召回精确结果

  06. structured_query_service.py
      - 结构化查询
      - 作用：从 MongoDB 知识文档元数据中检索结构化记录

  07. case_search_service.py
      - 案例检索
      - 作用：优先检索包含案例/故障/维修等关键词的案例型内容

  08. hyde_search_sevice.py
      - HyDE 检索
      - 作用：先让 LLM 生成假设答案，再用假设答案反查向量库

  09. web_search_service.py
      - 网络搜索
      - 作用：补充外部实时信息来源（可选）

四、融合与后处理
  10. rrf_service.py
      - RRF 融合服务
      - 作用：融合六路召回结果，统一排序并去重

  11. metadata_filter_service.py
      - 元数据过滤服务
      - 作用：根据车型、文档类型等实体对融合结果做过滤/降权

  12. rerank_service.py
      - 重排序服务
      - 作用：对候选结果做精排，动态截断 TopK

  13. confidence_service.py
      - 置信度处理服务
      - 作用：判断当前结果是否足够可靠，是否需要追问

五、答案生成与持久化
  14. prompt_builder.py
      - 提示词构建服务
      - 作用：将上下文、历史对话、主体、问题整理成最终 Prompt

  15. answer_service.py
      - 答案生成服务
      - 作用：调用大模型生成最终答案，支持流式与非流式输出

  16. qa_persist_service.py
      - 问答持久化服务
      - 作用：保存问答记录、上下文与答案结果

六、说明
  1. 上述顺序对应 app/process/query/agent/main_graph.py 中的主执行链路。
  2. 01 为入口节点，有确认/候选/未识别三种分流。
  3. 04~09 为并行召回阶段，不是严格串行执行。
  4. 10~16 为召回后统一处理链路。
  5. 主体确认阈值：
     - 确认阈值 CONFIRM_THRESHOLD = 0.55
     - 候选阈值 CANDIDATE_THRESHOLD = 0.45
  6. 候选确认通过前端点击按钮实现，点击后重新提交检索。

七、会话管理与历史记录
  1. 会话列表接口：GET /api/v1/chat/sessions
     - 从 MongoDB chat_message 集合中聚合出所有 session_id
     - 每个会话返回：session_id、最新消息摘要、消息数量、最后活跃时间
     - 按最后活跃时间倒序排列
  2. 历史消息接口：GET /api/v1/chat/history/{session_id}
     - 返回指定会话的最近 N 条消息（默认10条，最多200条）
     - 按时间倒序返回，前端使用时需 reverse
  3. 前端会话管理：
     - 页面初始化时调用 loadSessions() 从后端拉取真实会话列表
     - 点击会话时调用 switchSession() → loadSessionHistory() 加载历史消息
     - 新建会话时生成 crypto.randomUUID() 作为 session_id
     - 发送消息后可选调用 loadSessions() 刷新列表
  4. 数据流向：
     用户提问 → POST /api/v1/chat/query → LangGraph 执行
     → qa_persist_service 保存到 MongoDB chat_message
     → 下次 loadSessions() 可见新会话
     → 切换会话时 loadSessionHistory() 可查看历史

八、反馈存储
  1. 反馈接口：POST /api/v1/feedback/submit
  2. 保存内容：session_id、query、answer、feedback_type、comment、created_at
  3. 存储位置：MongoDB auto_carcrm 库 user_feedbacks 集合
  4. 前端交互：每条回答下方有"有用/无用"按钮，点击后保存当前问题和回答
