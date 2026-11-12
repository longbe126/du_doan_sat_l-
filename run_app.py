"""
Hệ thống Giám sát Nguy cơ Sạt lở Đất (Phiên bản React + Three.js 3D + FastAPI).
Chạy: python run_app.py
Tự động mở trình duyệt tại: http://localhost:8000
"""
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Tự động chuyển sang Python trong venv nếu đang chạy bằng Python toàn cục
venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
if not venv_python.exists():
    venv_python = ROOT / "venv" / "Scripts" / "python.exe"
if venv_python.exists() and Path(sys.executable).resolve() != venv_python.resolve():
    print(f" -> Tự động kích hoạt môi trường ảo: {venv_python}")
    subprocess.run([str(venv_python), str(ROOT / "run_app.py")] + sys.argv[1:])
    sys.exit(0)

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "server"))

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 65)
    print(" ⛰️  TRUNG TÂM GIÁM SÁT NGUY CƠ SẠT LỞ ĐẤT (AI + 3D GEOSPATIAL)")
    print("=" * 65)
    print(" -> Khởi động FastAPI Backend & Giao diện React Three Fiber...")
    print(" -> Giao diện web sẵn sàng tại: http://localhost:8000\n")

    # Mở trình duyệt sau khi server khởi chạy
    try:
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass

    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=False)
