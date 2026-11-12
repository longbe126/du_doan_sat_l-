"""
FastAPI Server phục vụ Hệ thống Giám sát Nguy cơ Sạt lở Đất.
Cung cấp API cho Frontend React + Three.js:
- Địa hình DEM & tọa độ lưới
- Đánh giá nguy cơ học máy (Logistic Regression, Random Forest, XGBoost)
- Kịch bản mô phỏng mưa 24 giờ
- Dữ liệu lịch sử sạt lở từ SQLite
- Báo cáo đánh giá mô hình AI
"""
from __future__ import annotations

import json
import os
import math
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Thêm đường dẫn project vào sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "app") not in sys.path:
    sys.path.insert(0, str(ROOT / "app"))

from app.core.data_engine import build_base, compute, NC, N, AREAS
from app.core.model_loader import load_best_model

app = FastAPI(
    title="Landslide Risk Intelligence API",
    version="2.0.0",
    description="API cung cấp dữ liệu địa hình, mô hình AI và kịch bản sạt lở",
)

# Cấu hình CORS để frontend React kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = ROOT / "data" / "landslide.db"
REPORT_PATH = ROOT / "reports" / "evaluation.json"

# Nạp dữ liệu cơ sở tĩnh và mô hình một lần khi khởi động
_BASE_DATA = build_base()
_MODEL_OBJ, _MODEL_NAME, _TRAIN_REPORT = load_best_model()

HOURS = 24


def ramp(h: int) -> float:
    """Hàm tăng trưởng mưa theo giờ kịch bản (giờ 0: 30%, giờ 24: 100%)."""
    return 0.30 + 0.70 * (h / HOURS) ** 1.3


@app.get("/api/health")
def health():
    return {
        "status": "online",
        "model": _MODEL_NAME,
        "grid_size": f"{N}x{N}",
        "areas_count": len(AREAS),
        "database": DB_PATH.exists(),
    }


@app.get("/api/base")
def get_base():
    """Thông tin cơ sở tĩnh: danh sách 12 khu vực, metadata, sự kiện mô phỏng."""
    events_df = _BASE_DATA["events"].copy()
    events_list = events_df.to_dict(orient="records")

    areas_list = []
    for code, name, lat, lon, cover in AREAS:
        i = np.abs(np.asarray(_BASE_DATA["lat"]) - lat).argmin()
        j = np.abs(np.asarray(_BASE_DATA["lon"]) - lon).argmin()
        elev_val = float(_BASE_DATA["elev"][i, j])
        slope_val = float(_BASE_DATA["slope"][i, j])
        areas_list.append({
            "code": code,
            "name": name,
            "lat": lat,
            "lon": lon,
            "cover": cover,
            "elev": round(elev_val, 1),
            "slope": round(slope_val, 1),
        })

    return {
        "areas": areas_list,
        "events": events_list,
        "metadata": _BASE_DATA.get("metadata", {}),
        "model_name": _MODEL_NAME,
        "trained_at": _TRAIN_REPORT.get("trained_at", ""),
        "bounds": {
            "lat_min": float(_BASE_DATA["lat"].min()),
            "lat_max": float(_BASE_DATA["lat"].max()),
            "lon_min": float(_BASE_DATA["lon"].min()),
            "lon_max": float(_BASE_DATA["lon"].max()),
        },
    }


@app.get("/api/terrain")
def get_terrain():
    """Dữ liệu độ cao DEM 72x72 và tọa độ lưới để Three.js tạo mô hình 3D."""
    elev = _BASE_DATA["elev"]
    slope = _BASE_DATA["slope"]
    lat = _BASE_DATA["lat"]
    lon = _BASE_DATA["lon"]

    elev_flat = [round(float(v), 1) for v in elev.ravel()]
    slope_flat = [round(float(v), 1) for v in slope.ravel()]

    return {
        "rows": N,
        "cols": N,
        "elev_min": float(elev.min()),
        "elev_max": float(elev.max()),
        "elevation": elev_flat,
        "slope": slope_flat,
        "lat": [round(float(v), 5) for v in lat],
        "lon": [round(float(v), 5) for v in lon],
    }


def _num(val: Any, default: float) -> float:
    if hasattr(val, "default"):
        return float(val.default)
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


@app.get("/api/simulation")
def get_simulation(
    hour: int = Query(24, ge=0, le=24),
    scale: float = Query(1.0, ge=0.5, le=2.0),
    lo: float = Query(0.25, ge=0.05, le=0.95),
    hi: float = Query(0.45, ge=0.05, le=0.95),
    rain_alert: float = Query(100.0, ge=30.0, le=400.0),
):
    """Tính toán đánh giá nguy cơ sạt lở cho giờ được chỉ định theo kịch bản mưa (dữ liệu thật từ mô hình AI)."""
    h_int = int(_num(hour, 24))
    scale_flt = _num(scale, 1.0)
    lo_flt = _num(lo, 0.25)
    hi_flt = _num(hi, 0.45)
    alert_flt = _num(rain_alert, 100.0)

    current_scale = scale_flt * ramp(h_int)
    prev_hour = max(0, h_int - 1)
    prev_scale = scale_flt * ramp(prev_hour)

    risk_curr, cells_curr, df_curr = compute(_BASE_DATA, current_scale, (lo_flt, hi_flt), _MODEL_OBJ)
    _, _, df_prev = compute(_BASE_DATA, prev_scale, (lo_flt, hi_flt), _MODEL_OBJ)

    df = df_curr.copy()
    prev_scores = {r["name"]: float(r["score"]) for _, r in df_prev.iterrows()}

    scores_list = []
    prev_scores_list = []
    deltas_list = []
    levels_list = []

    for idx, row in df.iterrows():
        name = row["name"]
        s_curr = round(float(row["score"]), 3)
        s_prev = round(prev_scores.get(name, s_curr), 3)
        d_val = round(s_curr - s_prev, 3)
        lv = "Cao" if s_curr >= hi_flt else ("Trung bình" if s_curr >= lo_flt else "Thấp")
        scores_list.append(s_curr)
        prev_scores_list.append(s_prev)
        deltas_list.append(d_val)
        levels_list.append(lv)

    df["score"] = scores_list
    df["prev_score"] = prev_scores_list
    df["delta_score"] = deltas_list
    df["level"] = levels_list
    df["rain"] = [round(float(r), 1) for r in df["rain"]]

    areas_records = df.to_dict(orient="records")

    # Phân bố ô lưới tính trực tiếp từ mảng cells_curr
    cells_arr = np.asarray(cells_curr)
    low_cells = int((cells_arr < lo_flt).sum())
    mid_cells = int(((cells_arr >= lo_flt) & (cells_arr < hi_flt)).sum())
    high_cells = int((cells_arr >= hi_flt).sum())

    high_areas = int(sum(1 for s in scores_list if s >= hi_flt))
    mid_areas = int(sum(1 for s in scores_list if lo_flt <= s < hi_flt))
    low_areas = len(df) - high_areas - mid_areas

    # Khu vực điểm nguy cơ cao nhất
    max_idx = int(df["score"].idxmax())
    max_row = df.iloc[max_idx]
    max_area = {
        "name": max_row["name"],
        "code": max_row["code"],
        "score": float(max_row["score"]),
        "delta": float(max_row["delta_score"]),
        "level": max_row["level"],
    }

    # Khu vực lượng mưa cao nhất
    max_rain_idx = int(df["rain"].idxmax())
    max_rain_row = df.iloc[max_rain_idx]
    prev_rain = float(df_prev.loc[df_prev["name"] == max_rain_row["name"], "rain"].values[0])
    max_rain = {
        "name": max_rain_row["name"],
        "code": max_rain_row["code"],
        "rain": float(max_rain_row["rain"]),
        "delta": round(float(max_rain_row["rain"]) - prev_rain, 1),
    }

    # Top 3 nguy cơ
    top3_df = df.sort_values("score", ascending=False).head(3)
    top3 = [
        {
            "name": r["name"],
            "code": r["code"],
            "score": float(r["score"]),
            "delta": float(r["delta_score"]),
            "level": r["level"],
        }
        for _, r in top3_df.iterrows()
    ]

    # Sự kiện sinh động học theo diễn biến qua các giờ
    active_events = []
    prev_d = None
    for h in range(1, h_int + 1):
        if prev_d is None:
            _, _, prev_d = compute(_BASE_DATA, scale_flt * ramp(h - 1), (lo_flt, hi_flt), _MODEL_OBJ)
        if h == h_int:
            d_h = df_curr
        else:
            _, _, d_h = compute(_BASE_DATA, scale_flt * ramp(h), (lo_flt, hi_flt), _MODEL_OBJ)
        for (_, r_now), (_, r_old) in zip(d_h.iterrows(), prev_d.iterrows()):
            if r_now["level"] != r_old["level"]:
                color = "#ef4444" if r_now["level"] == "Cao" else ("#f59e0b" if r_now["level"] == "Trung bình" else "#10b981")
                tx = f"{'lên' if r_now['score'] > r_old['score'] else 'xuống'} mức {r_now['level']}"
                active_events.append({
                    "hour": h,
                    "time": f"{h:02d}:00",
                    "area": r_now["name"],
                    "type": "risk_change",
                    "text": f"{r_now['name']} {tx}",
                    "sub": f"Điểm nguy cơ {r_now['score']:.2f}".replace(".", ","),
                    "color": color,
                })
            if r_now["rain"] >= alert_flt and r_old["rain"] < alert_flt:
                active_events.append({
                    "hour": h,
                    "time": f"{h:02d}:00",
                    "area": r_now["name"],
                    "type": "rain_alert",
                    "text": f"{r_now['name']} vượt ngưỡng mưa chú ý",
                    "sub": f"Mưa 24 giờ {r_now['rain']:.0f} mm, ngưỡng {alert_flt:.0f} mm",
                    "color": "#0ea5e9",
                })
        prev_d = d_h
    active_events.sort(key=lambda e: (-e["hour"], e["area"]))

    rain_exceeded = int((df["rain"] >= alert_flt).sum())

    risk_flat = [round(float(v), 3) for v in risk_curr.ravel()]
    cells_flat = [round(float(v), 3) for v in cells_curr]

    return {
        "hour": h_int,
        "time_str": f"{h_int:02d}:00",
        "scale": scale_flt,
        "thresholds": {"low": lo_flt, "high": hi_flt},
        "areas": areas_records,
        "grid_risk": risk_flat,
        "grid_cells": cells_flat,
        "grid_distribution": {
            "low": low_cells,
            "mid": mid_cells,
            "high": high_cells,
            "total": len(cells_flat),
        },
        "area_counts": {
            "high": high_areas,
            "mid": mid_areas,
            "low": low_areas,
            "total": len(df),
        },
        "max_risk_area": max_area,
        "max_rain_area": max_rain,
        "top3_risk": top3,
        "rain_exceeded_count": rain_exceeded,
        "events_log": active_events[:6],
        "total_events": len(active_events),
    }


@app.get("/api/series")
def get_series(
    scale: float = Query(1.0, ge=0.5, le=2.0),
    lo: float = Query(0.25, ge=0.05, le=0.95),
    hi: float = Query(0.45, ge=0.05, le=0.95),
):
    """Tính sẵn chuỗi phân bố 24 giờ từ mô hình AI thật để thanh trượt thời gian render mượt mà."""
    scale_flt = _num(scale, 1.0)
    lo_flt = _num(lo, 0.25)
    hi_flt = _num(hi, 0.45)

    timeline = []
    scores_by_area: Dict[str, List[float]] = {name: [] for _, name, _, _, _ in AREAS}
    rain_by_area: Dict[str, List[float]] = {name: [] for _, name, _, _, _ in AREAS}
    max_scores: List[float] = []
    max_rain: List[float] = []
    n_high_areas: List[int] = []
    high_cells: List[int] = []

    for h in range(HOURS + 1):
        _, cells_h, df_h = compute(_BASE_DATA, scale_flt * ramp(h), (lo_flt, hi_flt), _MODEL_OBJ)
        c_arr = np.asarray(cells_h)
        low_c = int((c_arr < lo_flt).sum())
        mid_c = int(((c_arr >= lo_flt) & (c_arr < hi_flt)).sum())
        high_c = int((c_arr >= hi_flt).sum())
        high_cells.append(high_c)
        max_scores.append(round(float(df_h["score"].max()), 3))
        max_rain.append(round(float(df_h["rain"].max()), 1))
        n_high_areas.append(int((df_h["level"] == "Cao").sum()))

        for _, r in df_h.iterrows():
            area_name = str(r["name"])
            if area_name in scores_by_area:
                scores_by_area[area_name].append(round(float(r["score"]), 3))
                rain_by_area[area_name].append(round(float(r["rain"]), 1))

        timeline.append({
            "hour": h,
            "time": f"{h:02d}:00",
            "low": low_c,
            "mid": mid_c,
            "high": high_c,
            "total": len(c_arr),
            "max_score": round(float(df_h["score"].max()), 2),
        })
    return {
        "timeline": timeline,
        "scores_by_area": scores_by_area,
        "rain_by_area": rain_by_area,
        "max_scores": max_scores,
        "max_rain": max_rain,
        "n_high_areas": n_high_areas,
        "high_cells": high_cells,
    }


@app.get("/api/models")
def get_models_report():
    """Thông tin đánh giá mô hình học máy từ reports/evaluation.json."""
    if not REPORT_PATH.exists():
        return {"error": "Report not found"}
    with open(REPORT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    def sanitize(value):
        if isinstance(value, dict):
            return {key: sanitize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value

    return sanitize(data)


@app.get("/api/database/events")
def get_db_events():
    """Đọc dữ liệu sự kiện từ SQLite landslide.db nếu cần."""
    if not DB_PATH.exists():
        return {"events": []}
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM landslide_events ORDER BY event_date DESC LIMIT 50")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"events": rows}


# Phục vụ giao diện React Single Page Application (build từ frontend/dist)
DIST_DIR = ROOT / "frontend" / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = DIST_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(DIST_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
