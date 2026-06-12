import asyncio
import json
from typing import Any

from agents.mcp import MCPServerStreamableHttp

from app.infra.config.providers import infra_config
from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log

@step_log("get_written_query_and_validate")
def get_written_query_and_validate(state):
    # 1、获取数据
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        logger.info(f"rewritten_query: {rewritten_query} 没有内容，请重新弄输入")
        raise ValueError(f"rewritten_query: {rewritten_query} 没有内容，请重新弄输入")
    return rewritten_query

async def web_search_doc(rewritten_query):
    # 初始化mcp_server
    mcp_server = MCPServerStreamableHttp(
        name  ="web_search_mcp",
        params= {
            "url" :infra_config.mcp.mcp_base_url,
            "headers" :{"Authorization":f"Bearer {infra_config.mcp.api_key}"},

            "timeout":300
        },
        cache_tools_list=True,
        max_retry_attempts=3,
    )
    try:
        # 创建连接
        
        await mcp_server.connect()
        # 调用网络工具
        tool_list = await mcp_server.list_tools()
        logger.info(f"本次连接服务对应的tool_list: {tool_list}")
        mcp_result = await mcp_server.call_tool(tool_name="bailian_web_search",arguments={"query":rewritten_query,"count":5})
        return mcp_result
    except Exception as e:
        logger.exception(f"调用工具出现问题{rewritten_query},错误原因{str(e)}")
        # 断开连接
    finally:
        await mcp_server.cleanup()

@step_log("search_by_web")
def search_by_web(state: QueryGraphState) -> list[Any] | Any:
    """
    网络搜索服务：
    1. 通过 MCP 协议异步调用百炼联网搜索接口
    2. 将用户的查询转化为实时的、结构化的网络搜索结果
    3. 包含标题、链接和摘要
    4. 回写 web_search_docs
    """
    # 1、获取和校验参数
    rewritten_query = get_written_query_and_validate(state)

    # 调用业务的网络工具
    mcp_result = asyncio.run(web_search_doc(rewritten_query))
    logger.info(f"mcp_result: {mcp_result}")
    # 获取结果
    if mcp_result and mcp_result.content:
        search_text = mcp_result.content[0].text
    else:
        search_text = ""
    logger.info(f"search_text: {search_text}")
    # 转成dict pages对应列表即可
    if search_text:
        web_search_doc_list = json.loads(search_text).get("pages", [])
    else:
        web_search_doc_list = []
    logger.info(f"{rewritten_query}这个问题对应联网的结果web_search_doc_list: {web_search_doc_list}")
    return web_search_doc_list

