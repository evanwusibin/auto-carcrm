"""
mimo-v2-omni vs mimo-v2.5 视觉能力对照（max_tokens=300，留够 reasoning 空间）。
"""
import os
import io
import base64
import json
import requests
from PIL import Image, ImageDraw
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)
base = os.environ["OPENAI_BASE_URL"].rstrip("/")
key = os.environ["OPENAI_API_KEY"]


def png_b64() -> str:
    img = Image.new("RGB", (64, 64), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, 60, 30], fill=(220, 30, 30))      # 上半红
    d.rectangle([4, 34, 60, 60], fill=(30, 100, 220))    # 下半蓝
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


b64 = png_b64()
question = "请用中文一句话告诉我这张图片的颜色组合。"

for model in ["mimo-v2-omni", "mimo-v2.5"]:
    print(f"\n{'='*70}\n  MODEL: {model}   max_tokens=300\n{'='*70}")
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }],
        "max_tokens": 300,
        "temperature": 0,
    }
    r = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload, timeout=60,
    )
    j = r.json()
    msg = j["choices"][0]["message"]
    usage = j.get("usage", {})
    img_tok = usage.get("prompt_tokens_details", {}).get("image_tokens", 0)
    rea_tok = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
    print(f"HTTP {r.status_code}  finish_reason={j['choices'][0].get('finish_reason')}")
    print(f"  image_tokens       = {img_tok}   (证明图被处理)")
    print(f"  reasoning_tokens   = {rea_tok}   (思维链占用)")
    print(f"  completion_tokens  = {usage.get('completion_tokens')}")
    print(f"  content (回答)     = {msg.get('content')!r}")
    print(f"  reasoning_content  = {msg.get('reasoning_content', '')[:200]!r}…")
