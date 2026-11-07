import urllib.request
import re

url = "http://localhost:8501"
try:
    with urllib.request.urlopen(url, timeout=5) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    print("HTML length:", len(html))
    # Look for top bar strings
    print("Has 'Tổng quan':", "Tổng quan" in html)
    print("Has 'Cảnh báo':", "Cảnh báo" in html)
    print("Has 'Điều chỉnh kịch bản':", "Điều chỉnh kịch bản" in html)
except Exception as e:
    print("Error:", e)
