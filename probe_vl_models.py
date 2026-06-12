"""
逐个试探小米 mimo endpoint 实际支持哪些模型名（含视觉/VL）。
按从小米自家命名 → 国产 VL → 通用 OpenAI 命名的顺序尝试。
"""
import os
import time
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

base = os.environ["OPENAI_BASE_URL"].rstrip("/")
key = os.environ["OPENAI_API_KEY"]

# 按"概率高 → 低"排序的视觉模型候选
CANDIDATES = [
    # 小米 mimo 自家系列（文本已知可用 mimo-v2.5-pro，猜视觉命名）
    "mimo-v2.5-vision",
    "mimo-v2.5-vision-pro",
    "mimo-v2.5-vl-plus",
    "mimo-vision-pro",
    "mimo-multimodal",
    "mimo-v2-vision",
    "mimo-v2-vision-pro",
    "mimo-7b",
    "mimo-7b-instruct",
    "mimo-7b-base",
    "mimo-pro",
    "mimo-v2-pro",
    "mimo-v2.5",
    "mimo",
    # 小米早期/其他发布
    "MiMo-7B-Vision",
    "xiaomimimo-vision",
    "MiMo-VL",
    # 之前已知的文本模型（mimo-v2.5-pro 一定可用，放最后当作探针）
    "mimo-v2.5-pro",
]

PAYLOAD = {
    "model": "",          # 占位，循环里覆盖
    "messages": [
        {"role": "user", "content": [
            {"type": "text", "text": "只看图，回一个词：pong"},
            {"type": "image_url", "image_url": {
                "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
            }},
        ]},
    ],
    "max_tokens": 16,
    "temperature": 0,
}

print(f"target: {base}\n")
print(f"{'MODEL':<30}  {'HTTP':<6}  {'CODE':<10}  RESULT")
print("-" * 90)

ok = []
for m in CANDIDATES:
    PAYLOAD["model"] = m
    try:
        r = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=PAYLOAD,
            timeout=30,
        )
        try:
            j = r.json()
            err = j.get("error", {})
            code = err.get("code", "—")
            msg = err.get("message", "")[:60]
            content = ""
            if "choices" in j:
                content = j["choices"][0]["message"]["content"][:60].replace("\n", " ")
            label = "✅ OK " if content else f"❌ {code} {msg}"
        except Exception:
            label = f"raw {r.text[:60]!r}"
        print(f"{m:<30}  {r.status_code:<6}  {label}")
        if content:
            ok.append((m, content))
    except Exception as e:
        print(f"{m:<30}  ERR    {type(e).__name__}: {e}")
    time.sleep(0.3)

print("\n" + "=" * 90)
if ok:
    print(f"可用视觉模型（{len(ok)} 个）:")
    for m, c in ok:
        print(f"  ✅ {m}  →  {c}")
else:
    print("❌ 全部候选都不可用。建议：")
    print("  1) 登录 token-plan 后台控制台，查看实际开通的视觉模型名")
    print("  2) 联系小米技术支持索取 models 清单")
