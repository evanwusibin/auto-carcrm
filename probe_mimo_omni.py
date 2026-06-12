"""
打印 mimo-v2-omni / mimo-v2.5 的原始返回结构。
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
    d.rectangle([4, 4, 60, 30], fill=(220, 30, 30))
    d.rectangle([4, 34, 60, 60], fill=(30, 100, 220))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


b64 = png_b64()

for model in ["mimo-v2-omni", "mimo-v2.5", "mimo-v2-pro"]:
    print(f"\n{'='*70}\n  MODEL: {model}\n{'='*70}")
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "请用中文一句话告诉我这张图片的颜色组合。"},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }],
        "max_tokens": 80,
        "temperature": 0,
    }
    r = requests.post(
        f"{base}/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload, timeout=60,
    )
    print(f"HTTP {r.status_code}")
    try:
        j = r.json()
        print(json.dumps(j, ensure_ascii=False, indent=2)[:1500])
    except Exception:
        print(r.text[:1500])
