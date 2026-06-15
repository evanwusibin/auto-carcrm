import json
import os
from typing import Any

import requests

from app.process.query.agent.state import QueryGraphState
from app.shared.runtime.logger import logger, step_log

MCP_TIMEOUT = 30


@step_log("get_written_query_and_validate")
def get_written_query_and_validate(state):
    rewritten_query = state.get("rewritten_query")
    if not rewritten_query:
        raise ValueError(f"rewritten_query 为空")
    return rewritten_query


def _is_mcp_configured() -> bool:
    from app.infra.config.providers import infra_config
    url = infra_config.mcp.mcp_base_url
    key = infra_config.mcp.api_key
    return bool(url and key)


def _mcp_search_sync(rewritten_query: str) -> list[dict]:
    from app.infra.config.providers import infra_config

    base_url = infra_config.mcp.mcp_base_url
    api_key = infra_config.mcp.api_key

    session = requests.Session()
    session.trust_env = False
    session.proxies = {"http": None, "https": None}
    session.headers.update({
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    })

    try:
        init_body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "auto-carcrm", "version": "1.0"}
            }
        }
        resp = session.post(base_url, json=init_body, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"[web_search] MCP 初始化失败: HTTP {resp.status_code}")
            return []

        session_id = resp.headers.get("mcp-session-id")

        headers = {}
        if session_id:
            headers["mcp-session-id"] = session_id

        call_body = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "bailian_web_search",
                "arguments": {"query": rewritten_query, "count": 5}
            }
        }
        resp = session.post(base_url, json=call_body, headers=headers, timeout=MCP_TIMEOUT)
        if resp.status_code != 200:
            logger.warning(f"[web_search] MCP 调用失败: HTTP {resp.status_code}")
            return []

        result = resp.json()
        if "error" in result:
            logger.warning(f"[web_search] MCP 业务错误: {result['error']}")
            return []

        content = result.get("result", {}).get("content", [])
        if content:
            search_text = content[0].get("text", "")
            if search_text:
                return json.loads(search_text).get("pages", [])
        return []

    except requests.Timeout:
        logger.warning(f"[web_search] MCP 调用超时（{MCP_TIMEOUT}s），跳过联网搜索")
        return []
    except Exception as e:
        logger.warning(f"[web_search] MCP 调用失败，跳过联网搜索: {e}")
        return []
    finally:
        session.close()


@step_log("search_by_web")
def search_by_web(state: QueryGraphState) -> list[Any] | Any:
    logger.info("[web_search] ===== search_by_web 开始 =====")
    rewritten_query = get_written_query_and_validate(state)

    if not _is_mcp_configured():
        logger.info("[web_search] MCP 未配置完整，跳过联网搜索")
        state["web_search_docs"] = []
        return state

    logger.info("[web_search] MCP 已配置，开始调用（trust_env=False）...")
    web_search_doc_list = _mcp_search_sync(rewritten_query)
    logger.info(f"{rewritten_query} 联网结果: {len(web_search_doc_list)} 条")
    state["web_search_docs"] = web_search_doc_list
    return state
