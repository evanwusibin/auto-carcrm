"""
小米 mimo endpoint 联通性自检脚本（项目内常驻诊断工具）。

覆盖：
  1) 文本模型 mimo-v2.5-pro  —— 简单中文问答
  2) 文本模型 JSON 模式       —— 结构化输出
  3) 视觉功能总开关           —— VL_ENABLED=false 时 vision_chat() 返回 None
  4) 视觉模型 mimo-v2-omni    —— 真实图片理解（PIL 现生成 PNG）

每次调用都打印：模型名 → 状态 → 返回内容/异常，方便您快速判断是哪一段没通。
"""
from __future__ import annotations

import base64
import io
import sys
import traceback
from pathlib import Path

# 让脚本能 import app.* 包
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.shared.config.lm_config import is_vl_enabled, lm_config  # noqa: E402
from app.shared.model.lm_utils import get_llm_client  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402


# 1x1 红色 PNG (base64) —— 视觉测试的最小可用图像
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def make_test_png_b64() -> str:
    """用 PIL 生成一张 64x64 上红下蓝的 PNG，转 base64 供视觉测试用。

    注意：mimo-v2-omni / mimo-v2.5 都会在 response 之前先做一次思维链（reasoning），
    故 max_tokens 需 ≥ 200，否则 content 会返空。
    """
    from PIL import Image, ImageDraw  # 延后导入，未启用视觉的环境也能跑文本用例

    img = Image.new("RGB", (64, 64), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, 60, 30], fill=(220, 30, 30))      # 上半红
    d.rectangle([4, 34, 60, 60], fill=(30, 100, 220))    # 下半蓝
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def banner(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_text() -> None:
    banner("① 文本模型 · 普通对话")
    client = get_llm_client()  # 走默认 lm_config.llm_model
    print(f"  模型: {client.model_name}")
    print(f"  base_url: {client.openai_api_base}")
    resp = client.invoke([HumanMessage(content="用一句话介绍你自己，不超过30字。")])
    print(f"  ✅ 返回: {resp.content}")


def run_json() -> None:
    banner("② 文本模型 · JSON 模式")
    client = get_llm_client(json_mode=True)
    print(f"  模型: {client.model_name}  (json_mode=True)")
    prompt = '请严格按 JSON 输出：{"answer": <一句话回答>}\n问题：北京是哪个国家的首都？'
    resp = client.invoke([HumanMessage(content=prompt)])
    print(f"  ✅ 返回: {resp.content}")


def run_vl_switch() -> None:
    banner("③ 视觉功能总开关 · VL_ENABLED")
    print(f"  VL_ENABLED = {lm_config.vl_enabled}  (is_vl_enabled() = {is_vl_enabled()})")
    # 延迟导入：infra.llm.providers 会拉起 mongo 等重资源，仅在本用例内 import
    from app.infra.llm.providers import llm_provider  # noqa: PLC0415
    client = llm_provider.vision_chat()
    if lm_config.vl_enabled:
        assert client is not None, "VL_ENABLED=true 时 vision_chat() 不应返回 None"
        print(f"  ✅ 视觉客户端已就绪: {client.model_name}")
    else:
        assert client is None, "VL_ENABLED=false 时 vision_chat() 必须返回 None"
        print("  ✅ vision_chat() 正确返回 None（业务侧应走纯文本降级）")


def run_vl_image() -> None:
    banner("④ 视觉模型 mimo-v2-omni · 图像理解")
    if not is_vl_enabled():
        print("  ⏭️  跳过（VL_ENABLED=false）")
        return
    client = get_llm_client(model=lm_config.lv_model)
    print(f"  模型: {client.model_name}")
    b64 = make_test_png_b64()
    msg = HumanMessage(
        content=[
            {"type": "text", "text": "请用中文一句话告诉我这张图片的颜色组合。"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            },
        ]
    )
    # mimo-v2-omni 会先做 reasoning，所以 max_tokens 要够大
    resp = client.invoke([msg], max_tokens=300)
    print(f"  ✅ 返回: {resp.content}")


def main() -> int:
    print("\n🔎 小米 mimo endpoint 联通性自检")
    print(f"   base_url    = {lm_config.base_url}")
    print(f"   key 头/尾   = {lm_config.api_key[:6]}…{lm_config.api_key[-4:]}")
    print(f"   文本模型    = {lm_config.llm_model}")
    print(f"   视觉模型    = {lm_config.lv_model}  (VL_ENABLED={lm_config.vl_enabled})")

    cases = [
        ("文本对话", run_text),
        ("JSON 模式", run_json),
        ("VL 开关", run_vl_switch),
        ("VL 图像理解", run_vl_image),
    ]

    failed = 0
    for name, fn in cases:
        try:
            fn()
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name} 断言失败: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ❌ {name} 失败: {type(e).__name__}: {e}")
            traceback.print_exc()

    banner("汇总")
    total = len(cases)
    print(f"  通过 {total - failed}/{total}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
