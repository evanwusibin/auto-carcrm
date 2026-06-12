"""
探测小米 mimo endpoint 实际支持的模型清单。
"""
import os
import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)
base = os.environ.get("OPENAI_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1").rstrip("/")
key = os.environ.get("OPENAI_API_KEY", "")

print(f"GET {base}/models")
print(f"   key 头几位: {key[:6]}…{key[-4:]}")

r = requests.get(
    f"{base}/models",
    headers={"Authorization": f"Bearer {key}"},
    timeout=30,
)
print("HTTP", r.status_code)
try:
    data = r.json()
    ids = [m.get("id") for m in data.get("data", [])]
    print(f"共 {len(ids)} 个模型:")
    for i in ids:
        print("  -", i)
except Exception:
    print("原始返回(前 500 字):")
    print(r.text[:500])
