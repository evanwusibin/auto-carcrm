# HyDE 检索与 Web 搜索实现文档

> 文档编号：DOC-10-07 | 版本：v1.0 | 更新时间：2026-06-12

---

## 一、概述

HyDE 检索和 Web 搜索是查询流程中的两个**可选旁路**，通过配置开关控制是否启用。

### 1.1 配置说明

```env
# .env
RAG_ENABLE_HYDE=false      # 是否启用 HyDE 检索（默认关闭）
RAG_ENABLE_WEB=false       # 是否启用 Web 搜索（默认关闭）
```

### 1.2 启用方式

修改 `.env` 文件中的配置，重启服务即可生效。

---

## 二、HyDE 检索

### 2.1 什么是 HyDE？

**HyDE（Hypothetical Document Embeddings）** 是一种检索增强技术：

1. 先让 LLM 生成一个"假设性答案"
2. 用这个假设性答案去向量检索
3. 找到与假设性答案相似的真实文档

**好处**：假设性答案的语义更丰富，检索效果更好。

### 2.2 核心代码

```python
def search_by_embedding(state):
    # 1. 校验参数
    item_names, rewritten_query = validate_retrival_state(state)
    
    # 2. 生成假设性答案
    hyde_answer = call_llm_deal_hyde(rewritten_query)
    
    # 3. 用假设性答案向量化
    milvus_response = search_chunks_by_hyde(
        hyde_answer=hyde_answer,
        rewritten_query=rewritten_query,
        item_names=item_names
    )
    
    # 4. 格式化结果
    final_list_dict = normalize_retrieved_chunk(milvus_response) if milvus_response else []
    
    # 5. 写入 state
    state['hyde_embedding_chunks'] = final_list_dict if final_list_dict else []
    return state
```

### 2.3 关键点

| 步骤 | 说明 |
|------|------|
| 生成假设性答案 | 使用 `load_prompt("hyde_prompt")` 加载提示词 |
| 向量化 | 使用 `rewritten_query + ":" + hyde_answer` 拼接后向量化 |
| 混合搜索 | 使用 `milvus_gateway.hybrid_search()` 进行稠密+稀疏混合搜索 |

---

## 三、Web 搜索

### 3.1 什么是 Web 搜索？

**Web 搜索** 是通过 MCP 协议调用百炼联网搜索接口，获取实时的网络搜索结果。

**适用场景**：
- 最新政策、天气、新闻等时效性信息
- 知识库覆盖不足时的补充

### 3.2 核心代码

```python
async def web_search_doc(rewritten_query):
    # 1. 初始化 MCP 服务器
    mcp_server = MCPServerStreamableHttp(
        name="web_search_mcp",
        params={
            "url": infra_config.mcp.mcp_base_url,
            "headers": {"Authorization": f"Bearer {infra_config.mcp.api_key}"},
            "timeout": 300
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    )
    
    try:
        # 2. 创建连接
        await mcp_server.connect()
        
        # 3. 调用搜索工具
        mcp_result = await mcp_server.call_tool(
            tool_name="bailian_web_search",
            arguments={"query": rewritten_query, "count": 5}
        )
        return mcp_result
    except Exception as e:
        logger.exception(f"调用工具出现问题：{e}")
    finally:
        # 4. 断开连接
        await mcp_server.cleanup()
```

### 3.3 关键点

| 步骤 | 说明 |
|------|------|
| MCP 协议 | 使用 `MCPServerStreamableHttp` 连接 MCP 服务器 |
| 认证 | 使用 `infra_config.mcp.api_key` 进行认证 |
| 工具调用 | 使用 `call_tool(tool_name="bailian_web_search")` 调用搜索 |
| 结果解析 | 使用 `json.loads(search_text).get("pages", [])` 解析结果 |

---

## 四、MainGraph 中的配置

### 4.1 节点添加

```python
# 根据配置决定是否添加可选节点
if rag_config.enable_hyde:
    query_graph_builder.add_node("node_search_embedding_hyde", node_search_embedding_hyde)
    logger.info("✅ HyDE 检索已启用")

if rag_config.enable_web:
    query_graph_builder.add_node("node_web_search_mcp", node_web_search_mcp)
    logger.info("✅ Web 搜索已启用")
```

### 4.2 条件边

```python
def node_entity_extraction_after(state):
    """返回并行执行的节点列表"""
    parallel_nodes = [
        "node_search_embedding",
        "node_keyword_search",
        "node_structured_query",
        "node_case_search",
    ]
    
    if rag_config.enable_hyde:
        parallel_nodes.append("node_search_embedding_hyde")
    if rag_config.enable_web:
        parallel_nodes.append("node_web_search_mcp")
    
    return tuple(parallel_nodes)
```

### 4.3 静态边

```python
# 所有检索节点 → node_rrf
query_graph_builder.add_edge("node_search_embedding", "node_rrf")
query_graph_builder.add_edge("node_keyword_search", "node_rrf")
query_graph_builder.add_edge("node_structured_query", "node_rrf")
query_graph_builder.add_edge("node_case_search", "node_rrf")

if rag_config.enable_hyde:
    query_graph_builder.add_edge("node_search_embedding_hyde", "node_rrf")
if rag_config.enable_web:
    query_graph_builder.add_edge("node_web_search_mcp", "node_rrf")
```

---

## 五、完整流程图

```
用户问题
    │
    ▼
node_entity_extraction（实体抽取）
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    四路并行检索 + 可选旁路                                │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  向量检索   │  │  关键词检索 │  │  结构化查询 │  │  案例检索   │  │
│  │  (必选)     │  │  (必选)     │  │  (必选)     │  │  (必选)     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         │               │               │               │           │
│  ┌─────────────┐  ┌─────────────┐                                 │
│  │  [可选]     │  │  [可选]     │                                 │
│  │  HyDE检索   │  │  Web搜索    │                                 │
│  │  (默认关闭) │  │  (默认关闭) │                                 │
│  └──────┬──────┘  └──────┬──────┘                                 │
│         │               │                                         │
└─────────┼───────────────┼─────────────────────────────────────────┘
          │               │
          └───────┬───────┘
                  │
                  ▼
            node_rrf（RRF融合）
                  │
                  ▼
            node_rerank（重排序）
                  │
                  ▼
            node_confidence_check（置信度检查）
                  │
                  ▼
            node_answer_output → node_save_qa → END
```

---

## 六、测试结果

```
62 passed in 13.49s ✅
```

---

## 七、一句话总结

> **HyDE 检索：先生成假设性答案，再用答案去检索，补充语义召回。**
> **Web 搜索：通过 MCP 协议调用百炼联网搜索，补充外部知识。**
> **两者都是可选旁路，通过配置开关控制，默认关闭。**

---

*文档版本：v1.0 | 更新时间：2026-06-12*
