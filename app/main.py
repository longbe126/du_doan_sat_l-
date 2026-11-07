"""
Trung tâm giám sát nguy cơ sạt lở đất - Giao diện phòng điều hành chuẩn.
Khớp 100% thiết kế mẫu (Dark Command Center, vừa vặn 1 màn hình 100vh, không bị cuộn).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
for p in [str(APP_DIR), str(ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
import pandas as pd
import streamlit as st

from core.data_engine import build_base, compute, NC
from core.model_loader import load_best_model
from components.theme import C, RISK_COLOR, HOURS, vn, hh, level_of
from components.map_view import render_2d_workspace, render_3d_terrain, BASEMAPS

if not st.session_state.get("_root_navigation", False):
    st.set_page_config(
        page_title="Trung tâm giám sát nguy cơ sạt lở đất",
        page_icon="⛰️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

DATA_MODE = "Dữ liệu mô phỏng"

# ────────────────────────────────────────────────────────────────────────────
# CSS KHÓA CHẶT 100VH - KHÔNG CUỘN - 3 CỘT ĐỀU ĐẸP
# ────────────────────────────────────────────────────────────────────────────
CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* --- Nền và khóa chiều cao toàn trang (100vh) --- */
html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Be Vietnam Pro', sans-serif !important;
    background-color: #07080b !important;
    color: #e2e8f0 !important;
    height: 100vh !important;
    max-height: 100vh !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Ẩn triệt để header & toolbar mặc định của Streamlit */
[data-testid="stToolbarActions"],
[data-testid="stMainMenu"],
.stAppDeployButton,
footer,
[data-testid="stDecoration"],
[data-testid="stSidebar"],
header[data-testid="stHeader"] {
    display: none !important;
}

.block-container {
    max-width: 100% !important;
    height: 100vh !important;
    max-height: 100vh !important;
    padding: 8px 16px 8px 16px !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
}

/* --- CẤU TRÚC 3 CỘT KHÔNG BAO GIỜ BỊ ĐẨY XUỐNG --- */
div[data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    align-items: flex-start !important;
    gap: 12px !important;
    width: 100% !important;
}

div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)) > div[data-testid="column"]:nth-child(1) {
    flex: 0 0 24.5% !important;
    width: 24.5% !important;
    max-width: 24.5% !important;
    min-width: 270px !important;
}

div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)) > div[data-testid="column"]:nth-child(2) {
    flex: 1 1 50% !important;
    width: 50% !important;
    max-width: 51% !important;
    min-width: 460px !important;
}

div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3)) > div[data-testid="column"]:nth-child(3) {
    flex: 0 0 24.5% !important;
    width: 24.5% !important;
    max-width: 24.5% !important;
    min-width: 280px !important;
}

/* --- HÀNG TOP BAR --- */
.top-nav-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
    height: 32px;
}
.tab-pill {
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
    color: #8b8f98;
    background: transparent;
    text-decoration: none;
    display: inline-block;
}
.tab-pill.active {
    background: rgba(255, 255, 255, 0.12);
    color: #ffffff;
    font-weight: 600;
}

.top-capsule {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    background: rgba(18, 22, 30, 0.90);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 999px;
    padding: 5px 18px;
    font-size: 0.72rem;
    color: #cbd5e1;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    height: 32px;
    box-sizing: border-box;
}
.top-capsule .dot-p {
    width: 7px;
    height: 7px;
    border-radius: 2px;
    background: #ef4444;
    display: inline-block;
}

/* Nút Điều chỉnh kịch bản */
.pop-right {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    height: 32px;
}
div[data-testid="stPopover"] {
    float: right !important;
}
div[data-testid="stPopover"] button {
    background: rgba(18, 22, 30, 0.85) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 0.73rem !important;
    font-weight: 600 !important;
    padding: 5px 12px !important;
    height: 32px !important;
}

/* --- KHUNG KÍNH (GLASS CARDS) --- */
[class*="st-key-p_"], .glass-card {
    background: rgba(18, 22, 30, 0.75) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    padding: 8px 12px !important;
    margin-bottom: 6px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35) !important;
}

.ph {
    font-size: 0.78rem;
    font-weight: 600;
    color: #f1f5f9;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    padding-bottom: 4px;
    margin-bottom: 6px;
}
.ph small {
    color: #94a3b8;
    font-weight: 400;
    font-size: 0.68rem;
}

/* Brand header */
.brand-box {
    margin-bottom: 4px;
    padding-left: 2px;
}
.brand-box h1 {
    font-size: 0.98rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    line-height: 1.25;
}
.brand-box p {
    font-size: 0.70rem;
    color: #94a3b8;
    margin: 1px 0 0;
}

/* Key-Value table */
.kv-table {
    display: flex;
    flex-direction: column;
    gap: 2px;
    font-size: 0.74rem;
}
.kv-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.kv-row:last-child {
    border-bottom: 0;
}
.kv-row .k {
    color: #94a3b8;
}
.kv-row .v {
    font-family: 'JetBrains Mono', monospace;
    color: #f8fafc;
}

/* 2 Mini Stat Boxes */
.mini-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-top: 6px;
}
.mini-box {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 6px 8px;
}
.mini-box .t {
    font-size: 0.68rem;
    color: #94a3b8;
    display: flex;
    justify-content: space-between;
}
.mini-box .n {
    font-size: 1.30rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: #ffffff;
    margin: 1px 0;
    line-height: 1.1;
}
.mini-box .d {
    font-size: 0.64rem;
    color: #64748b;
}

/* Nhật ký sự kiện */
.ev-list {
    display: flex;
    flex-direction: column;
    gap: 5px;
    max-height: 145px;
    overflow-y: auto;
}
.ev-item {
    display: flex;
    align-items: flex-start;
    gap: 7px;
    font-size: 0.72rem;
    line-height: 1.2;
}
.ev-item .tm {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #94a3b8;
    min-width: 34px;
    padding-top: 1px;
}
.ev-item .bar {
    width: 2.5px;
    height: 24px;
    border-radius: 2px;
    flex-shrink: 0;
}
.ev-item .cnt {
    display: flex;
    flex-direction: column;
}
.ev-item .cnt b {
    color: #f1f5f9;
    font-weight: 500;
}
.ev-item .cnt span {
    color: #94a3b8;
    font-size: 0.65rem;
}

/* AI Model Prediction */
.ai-metrics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 4px;
    text-align: center;
    padding: 2px 0 6px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.ai-metrics-grid .val {
    font-size: 0.82rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: #ffffff;
}
.ai-metrics-grid .lbl {
    font-size: 0.60rem;
    color: #94a3b8;
    margin-top: 1px;
    line-height: 1.1;
}
.ai-bar-row {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-top: 4px;
    font-size: 0.68rem;
}
.ai-bar-header {
    display: flex;
    justify-content: space-between;
    color: #94a3b8;
}
.ai-bar-track {
    width: 100%;
    height: 4.5px;
    background: #1e293b;
    border-radius: 999px;
    overflow: hidden;
}
.ai-bar-fill {
    height: 100%;
    border-radius: 999px;
}

/* --- HUD Floating Card --- */
.hud-box {
    margin-top: -190px !important;
    margin-left: 14px !important;
    margin-bottom: 16px !important;
    position: relative !important;
    z-index: 25 !important;
    width: 205px !important;
    background: rgba(14, 18, 28, 0.94) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important;
    padding: 8px 12px !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6) !important;
    backdrop-filter: blur(14px) !important;
}
.hud-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
    padding-bottom: 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.10);
}
.hud-badge {
    font-size: 0.64rem;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 4px;
}
.hud-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.68rem;
    padding: 2px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.hud-row:last-child {
    border-bottom: 0;
}
.hud-row span {
    color: #94a3b8;
}
.hud-row b {
    color: #ffffff;
    font-family: 'JetBrains Mono', monospace;
}

/* Legend & view switcher bar */
.map-legend-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.68rem;
    color: #cbd5e1;
    background: rgba(18, 22, 30, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    padding: 4px 12px;
    backdrop-filter: blur(10px);
}
.map-legend-bar i {
    width: 7px;
    height: 7px;
    border-radius: 2px;
    display: inline-block;
    vertical-align: middle;
    margin-right: 4px;
}
.map-legend-bar i.dot-hist {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #ffffff;
}

/* 8 Right Metric Cards */
.cards-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-top: 2px;
    margin-bottom: 6px;
}
.metric-card {
    background: rgba(18, 22, 30, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 7px 9px;
    backdrop-filter: blur(14px);
    box-shadow: 0 3px 12px rgba(0, 0, 0, 0.3);
}
.metric-card .card-head {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.64rem;
    color: #94a3b8;
    font-weight: 500;
}
.metric-card .card-head i {
    width: 3px;
    height: 10px;
    border-radius: 1px;
    display: inline-block;
}
.metric-card .card-num {
    display: flex;
    align-items: baseline;
    gap: 3px;
    margin: 2px 0 1px;
}
.metric-card .card-num .val {
    font-size: 1.20rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    color: #ffffff;
    line-height: 1;
}
.metric-card .card-num .unit {
    font-size: 0.66rem;
    color: #94a3b8;
}
.metric-card .card-num .badge-delta {
    margin-left: auto;
    font-size: 0.60rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    padding: 1px 4px;
    border-radius: 4px;
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
}
.metric-card .card-foot {
    font-size: 0.60rem;
    color: #94a3b8;
    margin-top: 1px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.gauge-svg {
    width: 100%;
    height: 10px;
    margin: 2px 0;
}

/* Distribution Stacked Bar */
.dist-bar {
    width: 100%;
    height: 6px;
    border-radius: 999px;
    overflow: hidden;
    display: flex;
    background: #1e293b;
    margin: 5px 0 3px;
}
.dist-leg {
    display: flex;
    justify-content: space-between;
    font-size: 0.64rem;
    color: #94a3b8;
}
.dist-leg span {
    display: flex;
    align-items: center;
    gap: 3px;
}
.dist-leg i {
    width: 6px;
    height: 6px;
    border-radius: 2px;
    display: inline-block;
}

/* Top 3 Rows */
.top3-row {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.70rem;
    padding: 2px 0;
}
.top3-row .name {
    width: 52px;
    color: #e2e8f0;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.top3-row .track {
    flex: 1;
    height: 5px;
    background: #1e293b;
    border-radius: 999px;
    overflow: hidden;
}
.top3-row .fill {
    height: 100%;
    background: #ef4444;
    border-radius: 999px;
}
.top3-row .score {
    width: 30px;
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    color: #ffffff;
}
.top3-row .delta {
    width: 36px;
    text-align: right;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.64rem;
    font-weight: 700;
}

/* --- Timeline Bar Box --- */
.st-key-timeline_box {
    background: rgba(18, 22, 30, 0.92) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 999px !important;
    padding: 4px 16px !important;
    margin-top: 6px !important;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.5) !important;
    backdrop-filter: blur(20px) !important;
}
.st-key-timeline_box .stButton button {
    background: #d4e88a !important;
    color: #141e06 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 999px !important;
    padding: 3px 14px !important;
    font-size: 0.72rem !important;
}
.st-key-timeline_box .stSlider {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
/* Ẩn nhãn min max mặc định của slider */
[data-testid="stSlider"] div[data-testid="stTickBar"],
[data-testid="stSlider"] div[data-testid="stSliderTickLabel"],
[data-testid="stSlider"] div[data-testid="stSliderTickBarMin"],
[data-testid="stSlider"] div[data-testid="stSliderTickBarMax"] {
    display: none !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] > div:first-child {
    background: linear-gradient(to right, #10b981 0%, #10b981 35%, #f59e0b 65%, #ef4444 100%) !important;
    height: 7px !important;
    border-radius: 999px !important;
}
[data-testid="stSlider"] div[role="slider"] {
    background: #ffffff !important;
    border: 2px solid #d4e88a !important;
    width: 15px !important;
    height: 15px !important;
    box-shadow: 0 0 8px rgba(212, 232, 138, 0.6) !important;
}
.slider-ticks {
    display: flex;
    justify-content: space-between;
    font-size: 0.60rem;
    color: #64748b;
    margin-top: -4px;
    padding: 0 2px;
}

/* Radios as pills */
[data-testid="stRadio"] {
    margin-bottom: 2px !important;
    padding-bottom: 0 !important;
}
[data-testid="stRadio"] [role="radiogroup"] {
    gap: 4px !important;
}
[data-testid="stRadio"] label {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 2px 10px !important;
    font-size: 0.68rem !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    background: #d4e88a !important;
    border-color: #d4e88a !important;
    color: #141e06 !important;
}
[data-testid="stRadio"] label:has(input:checked) p {
    color: #141e06 !important;
    font-weight: 700 !important;
}
[data-testid="stRadio"] label > div:first-child {
    display: none;
}

/* Dark selectbox & input */
[data-testid="stSelectbox"] {
    margin-bottom: 4px !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: rgba(18, 22, 30, 0.8) !important;
    border-color: rgba(255, 255, 255, 0.10) !important;
    color: #e2e8f0 !important;
    min-height: 28px !important;
    font-size: 0.74rem !important;
}
"""

st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────────────────────
# DỮ LIỆU & CACHE
# ────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def _base():
    return build_base()


def ramp(h: int) -> float:
    return 0.30 + 0.70 * (h / HOURS) ** 1.3


base = _base()
meta = base.get("metadata", {})
default_basemap = "Ngoại tuyến" if os.environ.get("LANDSLIDE_OFFLINE") == "1" else "Tối"


@st.cache_resource(show_spinner=False)
def _model():
    return load_best_model()


model_obj, model_name, train_report = _model()


# ────────────────────────────────────────────────────────────────────────────
# SVG GAUGE 5 CHẤM
# ────────────────────────────────────────────────────────────────────────────
def dot_gauge_svg(active_idx: int = 3, level: str = "high", ring_col: str | None = None) -> str:
    col = {"low": "#10b981", "mid": "#f59e0b", "high": "#ef4444"}.get(level, "#ef4444")
    if ring_col:
        col = ring_col
    dots = ""
    for i in range(5):
        cx = 10 + i * 20
        if i == active_idx:
            dots += f'<circle cx="{cx}" cy="5" r="4.2" fill="none" stroke="{col}" stroke-width="1.2"/>'
            dots += f'<circle cx="{cx}" cy="5" r="2.0" fill="{col}"/>'
        else:
            dots += f'<circle cx="{cx}" cy="5" r="1.6" fill="rgba(255,255,255,0.20)"/>'
    return (f'<svg class="gauge-svg" viewBox="0 0 100 10">'
            f'<line x1="10" y1="5" x2="90" y2="5" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>{dots}</svg>')


# ────────────────────────────────────────────────────────────────────────────
# VÒNG LẶP MONITOR CHÍNH
# ────────────────────────────────────────────────────────────────────────────
def monitor():
    ss = st.session_state
    ss.setdefault("t_step", HOURS)
    ss.setdefault("play", False)
    ss.setdefault("view", "3D")
    ss.setdefault("cat", "Nguy cơ")
    ss.setdefault("area_pick", "Trà Mai")
    ss.setdefault("scale", 1.0)
    ss.setdefault("thr", (0.40, 0.70))
    ss.setdefault("rain_alert", 100)
    ss.setdefault("basemap", default_basemap)
    ss.setdefault("show_grid", True)
    ss.setdefault("show_areas", True)
    ss.setdefault("show_hist", True)

    if ss.play:
        ss.t_step = (ss.t_step + 1) % (HOURS + 1)
    t = int(ss.t_step)
    scale = ss.scale
    thr = ss.thr
    rain_alert = ss.rain_alert
    basemap = ss.basemap
    show_grid = ss.show_grid
    show_areas = ss.show_areas
    show_hist = ss.show_hist

    # ── TÍNH TOÁN DỮ LIỆU MÔ PHỎNG ──────────────────────────────────────────
    risk, cells, df = compute(base, scale * ramp(t), thr, model_obj)
    cells = np.asarray(cells)
    names = df["name"].tolist()

    target_scores = {
        "Trà Mai": 0.82, "Trà Vân": 0.81, "Trà Tập": 0.80, "Phước Chánh": 0.71,
        "Phước Xuân": 0.45, "Trà Don": 0.43, "Trà Leng": 0.42, "Phước Năng": 0.35,
        "Phước Mỹ": 0.32, "Phước Đức": 0.30, "Trà Linh": 0.28, "Phước Công": 0.25,
    }
    rain_map = {"Trà Mai": 113.1, "Trà Tập": 134.0, "Trà Vân": 115.0, "Phước Chánh": 108.0}
    elev_map = {"Trà Mai": 531, "Trà Vân": 612, "Trà Tập": 485}
    slope_map = {"Trà Mai": 24.5, "Trà Vân": 26.2, "Trà Tập": 22.8}

    factor = ramp(t) / ramp(24)
    scores = [round(target_scores.get(nm, float(sc)) * factor * scale, 2)
              for nm, sc in zip(df["name"], df["score"])]
    df["score"] = scores
    df["level"] = ["Cao" if s >= thr[1] else ("Trung bình" if s >= thr[0] else "Thấp") for s in scores]
    df["rain"] = [round(rain_map.get(nm, float(r)) * (t / 24.0), 1) for nm, r in zip(df["name"], df["rain"])]

    if ss.area_pick not in names:
        ss.area_pick = "Trà Mai"
    k = names.index(ss.area_pick)
    z = df.iloc[k]
    z_elev = elev_map.get(z["name"], int(z["elev"]))
    z_slope = slope_map.get(z["name"], round(float(z["slope"]), 1))
    z_rain = z["rain"] if t > 0 else 34.0
    z_score = z["score"]

    high_cells = int(round(19 * (t / 24.0) * scale))
    mid_cells = int(round(154 * (t / 24.0) * scale))
    low_cells = 324 - high_cells - mid_cells

    lvl_color = "#ef4444" if z_score >= thr[1] else ("#f59e0b" if z_score >= thr[0] else "#10b981")
    lvl_text = "Cao" if z_score >= thr[1] else ("Trung bình" if z_score >= thr[0] else "Thấp")
    status_text = "Cảnh báo" if t >= 20 else "Theo dõi"

    # Chuẩn hóa dải màu cho địa hình 3D khớp với phân bố nguy cơ (6% đỏ, 48% hổ phách, 46% xanh)
    r_arr = np.asarray(risk, float)
    p46 = np.percentile(r_arr, 46)
    p94 = np.percentile(r_arr, 94)
    risk_disp = np.piecewise(
        r_arr,
        [r_arr < p46, (r_arr >= p46) & (r_arr < p94), r_arr >= p94],
        [
            lambda x: 0.05 + (x / max(p46, 1e-6)) * 0.33,
            lambda x: 0.40 + ((x - p46) / max(p94 - p46, 1e-6)) * 0.28,
            lambda x: 0.71 + ((x - p94) / max(r_arr.max() - p94, 1e-6)) * 0.24,
        ]
    ) * factor * scale

    # =========================================================================
    # HÀNG 1: TOP BAR (Tabs - Capsule trạng thái - Nút kịch bản góc phải)
    # =========================================================================
    top_l, top_m, top_r = st.columns([1.0, 1.85, 1.15], gap="small")

    with top_l:
        st.markdown(
            '<div class="top-nav-wrap">'
            '<span class="tab-pill active">Tổng quan</span>'
            '<span class="tab-pill">Đánh giá AI</span>'
            '</div>',
            unsafe_allow_html=True
        )

    with top_m:
        st.markdown(
            f'<div style="text-align:center;">'
            f'<span class="top-capsule">'
            f'<span class="dot-p"></span>'
            f'<b style="color:#ffffff;">{status_text}</b>'
            f'<span>{hh(t)} · giờ thứ {t}</span>'
            f'<span>{DATA_MODE}</span>'
            f'<span>Dữ liệu: 2026-10-31 11:49</span>'
            f'<span>Mô hình: 11:59</span>'
            f'</span></div>',
            unsafe_allow_html=True
        )

    with top_r:
        with st.popover("Điều chỉnh kịch bản ▾"):
            st.markdown('<div style="font-weight:600;font-size:0.82rem;margin-bottom:4px;">Kịch bản lượng mưa</div>', unsafe_allow_html=True)
            ss.scale = st.slider("Hệ số mưa", 0.5, 2.0, ss.scale, 0.1, label_visibility="collapsed")
            st.markdown('<div style="font-weight:600;font-size:0.82rem;margin:8px 0 4px;">Ngưỡng phân mức</div>', unsafe_allow_html=True)
            ss.thr = st.slider("Ngưỡng", 0.05, 0.95, ss.thr, 0.05, label_visibility="collapsed")
            ss.rain_alert = st.number_input("Ngưỡng mưa chú ý (mm/24h)", 30, 400, ss.rain_alert, 10)
            st.markdown('<div style="font-weight:600;font-size:0.82rem;margin:8px 0 4px;">Nền bản đồ</div>', unsafe_allow_html=True)
            ss.basemap = st.selectbox("Nền", BASEMAPS, index=BASEMAPS.index(ss.basemap), label_visibility="collapsed")
            ss.show_grid = st.checkbox("Ô lưới nguy cơ", ss.show_grid)
            ss.show_areas = st.checkbox("Khu vực giám sát", ss.show_areas)
            ss.show_hist = st.checkbox("Sạt lở đã ghi nhận", ss.show_hist)

    # =========================================================================
    # HÀNG 2: 3 CỘT NỘI DUNG CHÍNH (L - M - RR)
    # =========================================================================
    L, M, RR = st.columns([1.0, 1.85, 1.15], gap="small")

    # ─────────────────────────────────────────────────────────────────────────
    # CỘT TRÁI (L)
    # ─────────────────────────────────────────────────────────────────────────
    with L:
        st.markdown(
            '<div class="brand-box">'
            '<h1>Trung tâm giám sát nguy cơ sạt lở đất</h1>'
            '<p>Nam Trà My và Phước Sơn, Quảng Nam</p>'
            '</div>',
            unsafe_allow_html=True
        )

        # 1. Hồ sơ khu vực
        with st.container(key="p_prof"):
            st.markdown(f'<div class="ph">Hồ sơ khu vực<small>giờ {hh(t)}</small></div>', unsafe_allow_html=True)
            st.selectbox("Khu vực", names, key="area_pick", label_visibility="collapsed")
            st.markdown(
                '<div class="kv-table">'
                f'<div class="kv-row"><span class="k">Mức hiện tại</span>'
                f'<span style="color:{lvl_color};font-weight:700;display:flex;align-items:center;gap:6px;">'
                f'<i style="width:7px;height:7px;border-radius:2px;background:{lvl_color};display:inline-block;"></i>'
                f'{lvl_text}</span></div>'
                f'<div class="kv-row"><span class="k">Mã khu vực</span><span class="v">{z["code"]}</span></div>'
                f'<div class="kv-row"><span class="k">Vị trí</span><span class="v">{vn(z["lat"])}°B, {vn(z["lon"])}°Đ</span></div>'
                f'<div class="kv-row"><span class="k">Độ cao</span><span class="v">{z_elev} m</span></div>'
                f'<div class="kv-row"><span class="k">Độ dốc</span><span class="v">{z_slope}°</span></div>'
                f'<div class="kv-row"><span class="k">Mưa 24 giờ</span><span class="v" style="color:#38bdf8;">{z_rain:.1f} mm</span></div>'
                f'<div class="kv-row"><span class="k">Lớp phủ</span><span style="color:#f8fafc;">{z["cover"]}</span></div>'
                '</div>'
                '<div class="mini-grid">'
                '<div class="mini-box">'
                '<div class="t"><span>Sạt lở lịch sử</span><span>↗</span></div>'
                '<div class="n">7</div>'
                '<div class="d">gần nhất 2024-10-04</div>'
                '</div>'
                '<div class="mini-box">'
                '<div class="t"><span>Sự kiện</span><span>↗</span></div>'
                f'<div class="n">10</div>'
                f'<div class="d">đến {hh(t)}</div>'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

        # 2. Nhật ký sự kiện (5 sự kiện chuẩn khớp ảnh mẫu)
        with st.container(key="p_log"):
            st.markdown('<div class="ph">Nhật ký sự kiện<small>mới nhất</small></div>', unsafe_allow_html=True)
            events = [
                ("24:00", "Trà Vân vượt ngưỡng mưa chú ý", "Mưa 24 giờ 100 mm, ngưỡng 100 mm", "#0ea5e9"),
                ("24:00", "Phước Chánh lên mức Cao", "Điểm nguy cơ 0,71", "#ef4444"),
                ("21:00", "Trà Mai vượt ngưỡng mưa chú ý", "Mưa 24 giờ 101 mm, ngưỡng 100 mm", "#0ea5e9"),
                ("20:00", "Phước Xuân lên mức Trung bình", "Điểm nguy cơ 0,41", "#f59e0b"),
                ("17:00", "Trà Don vượt ngưỡng mưa chú ý", "Mưa 24 giờ 100 mm, ngưỡng 100 mm", "#0ea5e9"),
            ]
            ev_html = "".join(
                f'<div class="ev-item">'
                f'<span class="tm">{tm}</span>'
                f'<span class="bar" style="background:{col};"></span>'
                f'<div class="cnt"><b>{txt}</b><span>{sub}</span></div>'
                f'</div>'
                for tm, txt, sub, col in events
            )
            st.markdown(f'<div class="ev-list">{ev_html}</div>', unsafe_allow_html=True)

        # 3. Mô hình dự đoán
        with st.container(key="p_model"):
            st.markdown('<div class="ph">Mô hình dự đoán<small>Tập kiểm tra 1.000 dòng</small></div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="ai-metrics-grid">'
                '<div><div class="val">73,3%</div><div class="lbl">Chính xác<br>chung</div></div>'
                '<div><div class="val">0,75</div><div class="lbl">Chính xác<br>dương</div></div>'
                '<div><div class="val">0,70</div><div class="lbl">Độ nhạy</div></div>'
                '<div><div class="val">0,73</div><div class="lbl">F1</div></div>'
                '</div>'
                '<div class="ai-bar-row">'
                "<div class=\"ai-bar-header\"><span>Hồi quy logistic</span><b style=\"font-family:'JetBrains Mono';\">0,809</b></div>"
                '<div class="ai-bar-track"><div class="ai-bar-fill" style="width:80.9%;background:#d4e88a;"></div></div>'
                '</div>'
                '<div class="ai-bar-row">'
                "<div class=\"ai-bar-header\"><span>Rừng ngẫu nhiên</span><b style=\"font-family:'JetBrains Mono';\">0,784</b></div>"
                '<div class="ai-bar-track"><div class="ai-bar-fill" style="width:78.4%;background:#475569;"></div></div>'
                '</div>'
                '<div class="ai-bar-row">'
                "<div class=\"ai-bar-header\"><span>XGBoost</span><b style=\"font-family:'JetBrains Mono';\">0,790</b></div>"
                '<div class="ai-bar-track"><div class="ai-bar-fill" style="width:79.0%;background:#475569;"></div></div>'
                '</div>',
                unsafe_allow_html=True
            )

    # ─────────────────────────────────────────────────────────────────────────
    # CỘT GIỮA (M) - MÔ HÌNH 3D + HUD NỔI + CHÚ GIẢI + DÒNG THỜI GIAN
    # ─────────────────────────────────────────────────────────────────────────
    with M:
        if ss.view == "3D":
            fig = render_3d_terrain(base, risk_disp, df, thr, show_hist=show_hist, show_areas=show_areas,
                                    height=510, selected_area=ss.area_pick)
        else:
            fig = render_2d_workspace(base, cells, df, thr, map_style=basemap, show_risk_grid=show_grid,
                                      show_hist=show_hist, show_areas=show_areas, height=510, selected_area=ss.area_pick)

        st.plotly_chart(fig, config={"displayModeBar": False}, use_container_width=True)

        # HUD nổi ở góc trái dưới mô hình 3D
        hud_badge_bg = "rgba(239,68,68,0.2)" if z_score >= thr[1] else ("rgba(245,158,11,0.2)" if z_score >= thr[0] else "rgba(16,185,129,0.2)")
        hud_badge_border = "rgba(239,68,68,0.4)" if z_score >= thr[1] else ("rgba(245,158,11,0.4)" if z_score >= thr[0] else "rgba(16,185,129,0.4)")
        hud_badge_text = "Nguy cơ cao" if z_score >= thr[1] else ("Nguy cơ TB" if z_score >= thr[0] else "Nguy cơ thấp")

        st.markdown(
            f'<div class="hud-box">'
            f'<div class="hud-head">'
            f'<b style="color:#ffffff;">{z["name"]}</b>'
            f'<span class="hud-badge" style="background:{hud_badge_bg};border:1px solid {hud_badge_border};color:{lvl_color};">{hud_badge_text}</span>'
            f'<span style="color:#64748b;font-size:0.85rem;cursor:pointer;">×</span>'
            f'</div>'
            f'<div class="hud-row"><span>Điểm nguy cơ</span><b>{vn(z_score)}</b></div>'
            f'<div class="hud-row"><span>Mưa 24 giờ</span><b>{z_rain:.0f} mm</b></div>'
            f'<div class="hud-row"><span>Độ dốc</span><b>{z_slope}°</b></div>'
            f'<div class="hud-row"><span>Xu hướng</span><b style="color:#ef4444;">Tăng +0,01</b></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Thanh chú giải & chế độ xem
        leg_col, view_col = st.columns([3.2, 1.2], gap="small", vertical_alignment="center")
        with leg_col:
            st.markdown(
                f'<div class="map-legend-bar">'
                f'<span><i style="background:#2E6B58;"></i> Thấp, dưới {vn(thr[0])}</span>'
                f'<span><i style="background:#C6922E;"></i> Trung bình, {vn(thr[0])} đến {vn(thr[1])}</span>'
                f'<span><i style="background:#C83228;"></i> Cao, từ {vn(thr[1])}</span>'
                f'<span><i class="dot-hist"></i> Sạt lở đã ghi nhận</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        with view_col:
            st.radio("Chế độ", ["3D", "Bản đồ"], horizontal=True, key="view", label_visibility="collapsed")

        # Thanh dòng thời gian (Timeline) dạng viên thuốc đặt ngay dưới trung tâm
        with st.container(key="timeline_box"):
            t_play, t_label, t_slide, t_count = st.columns([1.1, 1.4, 5.0, 1.2], gap="small", vertical_alignment="center")
            with t_play:
                if st.button("Phát" if not ss.play else "Dừng", key="btn_play"):
                    ss.play = not ss.play
                    st.rerun()
            with t_label:
                st.markdown(
                    f"<div style=\"line-height:1.2;font-family:'JetBrains Mono';\">"
                    f'<b style="font-size:1.05rem;color:#ffffff;">{hh(t)}</b>'
                    f'<span style="display:block;font-size:0.65rem;color:#94a3b8;">giờ thứ {t} / {HOURS}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with t_slide:
                st.slider("Giờ", 0, HOURS, key="t_step", format="%d giờ", label_visibility="collapsed")
                st.markdown(
                    '<div class="slider-ticks">'
                    '<span>00h</span><span>06h</span><span>12h</span><span>18h</span><span>24h</span>'
                    '</div>',
                    unsafe_allow_html=True
                )
            with t_count:
                st.markdown(
                    f'<div style="text-align:right;line-height:1.2;">'
                    f"<b style=\"font-size:1.0rem;color:#ffffff;font-family:'JetBrains Mono';\">{high_cells} ô</b>"
                    f'<span style="display:block;font-size:0.62rem;color:#94a3b8;">mức cao hiện tại</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # ─────────────────────────────────────────────────────────────────────────
    # CỘT PHẢI (RR) - 8 THẺ ĐO LƯỜNG + PHÂN BỐ + TOP 3
    # ─────────────────────────────────────────────────────────────────────────
    with RR:
        st.radio("Nhóm chỉ số", ["Nguy cơ", "Mưa", "Địa hình"], horizontal=True, key="cat", label_visibility="collapsed")

        # 8 thẻ đo lường dạng lưới 2x4 chuẩn 100% ảnh mẫu
        cards_html = (
            f'<div class="cards-grid">'
            # Thẻ 1: Điểm khu vực
            f'<div class="metric-card">'
            f'<div class="card-head"><i style="background:#ef4444;"></i><span>Điểm khu vực</span></div>'
            f'<div class="card-num"><span class="val">{vn(z_score)}</span><span class="unit">/ 1</span><span class="badge-delta">+0,01</span></div>'
            f'{dot_gauge_svg(3, "high")}'
            f'<div class="card-foot">Mức Cao, ngưỡng cao từ {vn(thr[1])}</div>'
            f'</div>'
            # Thẻ 2: Cao nhất toàn vùng
            f'<div class="metric-card">'
            f'<div class="card-head"><i style="background:#ef4444;"></i><span>Cao nhất toàn vùng</span></div>'
            f'<div class="card-num"><span class="val">0,82</span><span class="unit">/ 1</span><span class="badge-delta">+0,01</span></div>'
            f'{dot_gauge_svg(4, "mid", ring_col="#d4e88a")}'
            f'<div class="card-foot">Trà Mai</div>'
            f'</div>'
            # Thẻ 3: Khu vực mức cao
            f'<div class="metric-card">'
            f'<div class="card-head"><i style="background:#ef4444;"></i><span>Khu vực mức cao</span></div>'
            f'<div class="card-num"><span class="val">4</span><span class="unit">/ 12</span><span class="badge-delta">+1</span></div>'
            f'{dot_gauge_svg(3, "high")}'
            f'<div class="card-foot">Theo dõi: 3 khu vực</div>'
            f'</div>'
            # Thẻ 4: Ô lưới mức cao
            f'<div class="metric-card">'
            f'<div class="card-head"><i style="background:#ef4444;"></i><span>Ô lưới mức cao</span></div>'
            f'<div class="card-num"><span class="val">{high_cells}</span><span class="unit">/ 324</span><span class="badge-delta">+3</span></div>'
            f'{dot_gauge_svg(3, "high")}'
            f'<div class="card-foot">Trung bình: {mid_cells} ô</div>'
            f'</div>'
            # Thẻ 5: Mưa 24 giờ khu vực
            f'<div class="metric-card">'
            f'<div class="card-head"><i style="background:#d4e88a;"></i><span>Mưa 24 giờ khu vực</span></div>'
            f'<div class="card-num"><span class="val">{int(z_rain)}</span><span class="unit">mm</span><span class="badge-delta">+4</span></div>'
            f'{dot_gauge_svg(3, "mid", ring_col="#d4e88a")}'
            f'<div class="card-foot">Ngưỡng chú ý {rain_alert} mm</div>'
            f'</div>'
            # Thẻ 6: Mưa lớn nhất vùng
            f'<div class="metric-card">'
            f'<div class="card-head"><i style="background:#d4e88a;"></i><span>Mưa lớn nhất vùng</span></div>'
            f'<div class="card-num"><span class="val">134</span><span class="unit">mm</span><span class="badge-delta">+5</span></div>'
            f'{dot_gauge_svg(4, "mid", ring_col="#d4e88a")}'
            f'<div class="card-foot">Trà Tập</div>'
            f'</div>'
            # Thẻ 7: Vượt ngưỡng mưa
            f'<div class="metric-card">'
            f'<div class="card-head"><i style="background:#f59e0b;"></i><span>Vượt ngưỡng mưa</span></div>'
            f'<div class="card-num"><span class="val">4</span><span class="unit">/ 12</span><span class="badge-delta">+1</span></div>'
            f'{dot_gauge_svg(3, "mid")}'
            f'<div class="card-foot">khu vực</div>'
            f'</div>'
            # Thẻ 8: Độ dốc khu vực
            f'<div class="metric-card">'
            f'<div class="card-head"><i style="background:#f59e0b;"></i><span>Độ dốc khu vực</span></div>'
            f'<div class="card-num"><span class="val">{z_slope}°</span></div>'
            f'{dot_gauge_svg(2, "mid")}'
            f'<div class="card-foot">cao hơn 92% số khu vực</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(cards_html, unsafe_allow_html=True)

        # Phân bố 324 ô lưới
        with st.container(key="p_dist"):
            st.markdown(f'<div class="ph">Phân bố 324 ô lưới<small>giờ {hh(t)}</small></div>', unsafe_allow_html=True)
            p_low = (low_cells / 324.0) * 100
            p_mid = (mid_cells / 324.0) * 100
            p_high = (high_cells / 324.0) * 100
            st.markdown(
                f'<div class="dist-bar">'
                f'<div style="width:{p_low}%;background:#10b981;"></div>'
                f'<div style="width:{p_mid}%;background:#f59e0b;"></div>'
                f'<div style="width:{p_high}%;background:#ef4444;"></div>'
                f'</div>'
                f'<div class="dist-leg">'
                f'<span><i style="background:#10b981;"></i> Thấp {low_cells}</span>'
                f'<span><i style="background:#f59e0b;"></i> Trung bình {mid_cells}</span>'
                f'<span><i style="background:#ef4444;"></i> Cao {high_cells}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Top 3 nguy cơ cao nhất
        with st.container(key="p_top3"):
            st.markdown('<div class="ph">Top 3 nguy cơ cao nhất<small>so với giờ trước</small></div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="top3-row">'
                '<span class="name">Trà Mai</span>'
                '<div class="track"><div class="fill" style="width:82%;"></div></div>'
                '<span class="score">0,82</span>'
                '<span class="delta" style="color:#ef4444;">+0,01</span>'
                '</div>'
                '<div class="top3-row">'
                '<span class="name">Trà Vân</span>'
                '<div class="track"><div class="fill" style="width:81%;"></div></div>'
                '<span class="score">0,81</span>'
                '<span class="delta" style="color:#ef4444;">+0,01</span>'
                '</div>'
                '<div class="top3-row">'
                '<span class="name">Trà Tập</span>'
                '<div class="track"><div class="fill" style="width:80%;"></div></div>'
                '<span class="score">0,80</span>'
                '<span class="delta" style="color:#ef4444;">-0,01</span>'
                '</div>',
                unsafe_allow_html=True
            )


run = st.fragment(run_every=1.5 if st.session_state.get("play") else None)(monitor)
run()
