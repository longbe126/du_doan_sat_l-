# Script ki?m tra tr?ng th?i ho?t ??ng c?a Streamlit Server
# L?u ?: Streamlit l? ?ng d?ng Single Page App (SPA) render ??ng b?ng React/WebSocket,
# n?n HTML ban ??u ch? l? th? <div id="root"></div>; ki?m tra HTTP 200 l? ?? ch?ng minh server online.
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

url = "http://localhost:8501"
try:
    with urllib.request.urlopen(url, timeout=5) as resp:
        code = resp.status
        html = resp.read().decode("utf-8", errors="replace")
    print(f"Streamlit Server: Online (HTTP {code})")
    print(f"?? d?i HTML c? s?: {len(html)} bytes")
    print("Ghi ch?: Streamlit t?i n?i dung ??ng qua WebSocket v?o client.")
except Exception as e:
    print("L?i k?t n?i t?i Streamlit:", e)
