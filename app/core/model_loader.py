"""Nạp mô hình đã huấn luyện cho bảng điều khiển; tự huấn luyện nếu chưa có tệp mô hình."""
from __future__ import annotations

import json
from pathlib import Path

import joblib

from core import train_models

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "models"
REPORT_PATH = ROOT / "reports" / "evaluation.json"


def _read_report() -> dict | None:
    if not REPORT_PATH.exists():
        return None
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_best_model():
    """Trả về (mô hình, tên mô hình, báo cáo). Mô hình tốt nhất do báo cáo huấn luyện chọn."""
    report = _read_report()
    best = (report or {}).get("best_model")
    if not best or not (MODEL_DIR / f"{best}.pkl").exists():
        # Tệp .pkl không được đưa lên git, nên lần chạy đầu trên máy mới sẽ huấn luyện lại.
        train_models.main()
        report = _read_report()
        best = report["best_model"]
    model = joblib.load(MODEL_DIR / f"{best}.pkl")
    return model, best, report
