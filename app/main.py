"""Trung tâm giám sát nguy cơ sạt lở đất.
Giao diện: Dark Frosted Glass HUD đồng bộ theo thiết kế tham chiếu.
Mô hình 3D toàn màn hình ở giữa, thẻ kính mờ hai bên, thanh thời gian dạng viên ở đáy."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in [str(ROOT / "app"), str(ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
import streamlit as st

from core.data_engine import build_base, compute, NC, assign_commune_info
from core.model_loader import load_model
from components.theme import HOURS, vn, hh
from components.map_view import render_2d_workspace, render_3d_terrain, BASEMAPS
from components.charts import fig_gauge, fig_timeline, fig_trend, fig_rain, fig_hist

if not st.session_state.get("_root_navigation", False):
    st.set_page_config(
        page_title="Trung tâm giám sát nguy cơ sạt lở đất",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

# Xử lý chuyển trang an toàn ở cấp ngoài cùng
_nav_target = st.session_state.pop("_nav_target", None)
if _nav_target:
    try:
        st.switch_page(_nav_target)
    except Exception:
        alt_target = _nav_target.replace("app/", "", 1) if _nav_target.startswith("app/") else f"app/{_nav_target}"
        st.switch_page(alt_target)

DATA_MODE = "Dữ liệu mô phỏng"
HI, MI, LO, AC = "#e85d56", "#e5a93c", "#4cc38a", "#c8dc70"
MODEL_VI = {
    "logistic_regression": "Hồi quy Logistic",
    "random_forest": "Rừng ngẫu nhiên",
    "xgboost": "XGBoost",
}
MODEL_OPTIONS = {
    "auto": "Tự động (Tốt nhất theo CV)",
    "logistic_regression": "Hồi quy Logistic (Logistic Regression)",
    "random_forest": "Rừng ngẫu nhiên (Random Forest)",
    "xgboost": "XGBoost (Gradient Boosted Trees)",
}

CSS = r'''
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@200;300;400;500;600&display=swap');
html,body,.stApp,[data-testid="stMain"],[data-testid="stAppViewContainer"]{overflow:hidden!important}
.stApp{background:#08090c;color:#eceef2;line-height:1.3}
.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stMarkdownContainer"] div{line-height:1.3}
.stApp [data-testid="stMarkdownContainer"] p{margin:0}
.stApp,.stApp p,.stApp label,.stApp button,.stApp input,.stApp li,.stApp [data-baseweb]{font-family:'Be Vietnam Pro',system-ui,-apple-system,sans-serif}
[data-testid="stHeader"],[data-testid="stToolbarActions"],[data-testid="stMainMenu"],.stAppDeployButton,[data-testid="stDecoration"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],footer{display:none!important}
.block-container{max-width:100%!important;padding:0!important;pointer-events:none}
[data-testid="stElementContainer"]{margin:0!important}
iframe[height="0"]{display:none}

/* Sân khấu 3D / Bản đồ nền */
.st-key-stage{position:fixed!important;inset:0;z-index:0;pointer-events:auto;padding:0!important;gap:0!important;overflow:hidden}
.st-key-stage [data-testid="stPlotlyChart"],.st-key-stage .js-plotly-plot,.st-key-stage .plot-container,.st-key-stage .mapboxgl-map,.st-key-stage .mapboxgl-canvas-container,.st-key-stage canvas{width:100%!important;height:calc(100vh + 6px)!important}

/* Hai cột nổi hai bên với khoảng thở rộng rãi */
.st-key-colL,.st-key-colR{position:fixed!important;top:60px;height:calc(100vh - 76px);display:flex;flex-direction:column;gap:12px!important;z-index:5;pointer-events:none;overflow-y:auto!important;overflow-x:hidden!important;padding-bottom:18px;scrollbar-width:none}
.st-key-colL{left:20px;width:376px}
.st-key-colR{right:20px;width:416px}
.st-key-colL::-webkit-scrollbar,.st-key-colR::-webkit-scrollbar{display:none}
.st-key-colL>*,.st-key-colR>*{flex:none}

/* Chất liệu kính mờ Dark Frosted Glass chuẩn ảnh mẫu */
.g,.mc,.mini,.prof-card{
    pointer-events:auto;
    background:linear-gradient(155deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.015) 100%), rgba(20, 22, 27, 0.62)!important;
    backdrop-filter:blur(26px) saturate(140%)!important;
    -webkit-backdrop-filter:blur(26px) saturate(140%)!important;
    border:1px solid rgba(255,255,255,0.08)!important;
    box-shadow:inset 0 1px 0 rgba(255,255,255,0.09), 0 14px 34px rgba(0,0,0,0.42)!important;
    border-radius:22px!important;
    overflow:hidden;
}

/* Hộp chọn khu vực dạng viên thuốc (Record: Family History pill trong ảnh mẫu) */
.st-key-g_sel{pointer-events:auto;background:none!important;border:0!important;padding:0!important;margin:0!important}
.st-key-g_sel [data-testid="stSelectbox"]{padding:0!important}
.st-key-g_sel [data-baseweb="select"]>div{
    background:linear-gradient(155deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%), rgba(22, 24, 29, 0.72)!important;
    backdrop-filter:blur(24px)!important;
    border:1px solid rgba(255,255,255,0.09)!important;
    border-radius:16px!important;
    min-height:42px!important;
    padding:0 14px!important;
    font-size:0.84rem!important;
    color:#eceef2!important;
    box-shadow:inset 0 1px 0 rgba(255,255,255,0.08), 0 8px 20px rgba(0,0,0,0.3)!important;
}

/* Thẻ Hồ sơ khu vực lấy cảm hứng trực tiếp từ Patient Profile (a04eae92) */
.prof-card{padding:18px 20px 16px 20px;position:relative}
.prof-card.critical{
    background:radial-gradient(120% 95% at 50% 105%, rgba(210, 52, 48, 0.34) 0%, rgba(110, 28, 28, 0.16) 52%, rgba(24, 24, 29, 0.72) 100%)!important;
    border-color:rgba(232, 93, 86, 0.22)!important;
}
.prof-card.watch{
    background:radial-gradient(120% 95% at 50% 105%, rgba(229, 169, 60, 0.24) 0%, rgba(24, 25, 30, 0.72) 100%)!important;
    border-color:rgba(229, 169, 60, 0.18)!important;
}
.prof-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.prof-top span{font-size:0.95rem;font-weight:400;color:#eceef2;letter-spacing:-0.01em}
.prof-top small{font-size:0.74rem;color:rgba(236,238,242,0.52);font-weight:300}
.prof-grid3{display:grid;grid-template-columns:1.1fr 0.9fr 1.1fr;gap:10px;margin-bottom:18px}
.prof-grid3 .lbl{font-size:0.74rem;color:rgba(236,238,242,0.48);margin-bottom:3px;font-weight:300}
.prof-grid3 .val{font-size:0.86rem;color:#eceef2;font-weight:400;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.prof-trend-hdr{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:8px;font-size:0.8rem}
.prof-trend-hdr span:first-child{color:rgba(236,238,242,0.78);font-weight:300}
.prof-trend-hdr span:last-child{color:#eceef2;font-weight:400;font-variant-numeric:tabular-nums}
.morse-bar{display:flex;align-items:center;gap:4px;height:10px;padding-bottom:14px;margin-bottom:14px;border-bottom:1px solid rgba(255,255,255,0.07)}
.morse-bar i{display:inline-block;height:2.5px;border-radius:2px;background:rgba(255,255,255,0.22)}
.morse-bar i.on{background:#eceef2;height:3px}
.morse-bar i.hi{background:#e85d56;height:3px}
.prof-bot{display:flex;justify-content:space-between;align-items:center;padding-top:2px}
.prof-bot-left .t1{font-size:0.82rem;color:#eceef2;font-weight:400}
.prof-bot-left .t2{font-size:0.68rem;color:rgba(236,238,242,0.48);margin-top:2px}
.prof-bot-mid{display:flex;align-items:center;gap:8px;font-size:0.84rem;color:#eceef2}
.prof-dot{width:8px;height:8px;border-radius:50%;display:inline-block;position:relative}
.prof-dot::after{content:"";position:absolute;inset:-4px;border-radius:50%;background:inherit;opacity:0.28}
.prof-bot-right{display:flex;flex-direction:column;gap:4px;align-items:flex-end;font-size:0.74rem;font-variant-numeric:tabular-nums}
.prof-lvl-row{display:flex;align-items:center;gap:6px;color:rgba(236,238,242,0.78)}
.prof-lvl-row b{font-weight:400;color:#eceef2}
.prof-lvl-row i{width:5px;height:5px;border-radius:50%;display:inline-block}
.prof-lvl-row s{display:inline-block;width:36px;height:1.5px;background:rgba(255,255,255,0.18);text-decoration:none}

/* Hai thẻ vuông .two (Tomography / Radiography style) */
.two{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:10px!important;margin:0!important}
.mini{padding:14px 16px!important;display:flex;flex-direction:column;justify-content:space-between;min-height:102px!important;border-radius:20px!important}
.mini .t{display:flex;justify-content:space-between;align-items:center;font-size:0.84rem;color:#eceef2;font-weight:400}
.mini .t span{color:rgba(236,238,242,0.55);font-size:0.88rem;font-weight:300}
.mini .d{font-size:0.7rem;color:rgba(236,238,242,0.45);margin-top:2px}
.mini .n{font-size:1.95rem;font-weight:200;color:#ffffff;line-height:1.05;margin-top:10px;font-variant-numeric:tabular-nums}
.mini .n small{font-size:0.76rem;color:rgba(236,238,242,0.45);font-weight:300;margin-left:4px}

/* Khung thông tin tiêu chuẩn bên cột trái */
.ph{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.06);font-size:0.88rem;color:#eceef2}
.ph small{color:rgba(236,238,242,0.45);font-size:0.72rem;font-weight:300}
.st4{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:8px!important;padding:12px!important}
.st4 .st4cell{padding:10px 12px;border:1px solid rgba(255,255,255,0.055)!important;border-radius:14px!important;background:rgba(255,255,255,0.02)!important;font-size:0.7rem;color:rgba(236,238,242,0.52)}
.st4 .st4cell b{display:block;font-size:1.28rem;font-weight:200;color:#eceef2;margin-bottom:2px;font-variant-numeric:tabular-nums}
.ev{display:grid;grid-template-columns:42px 2.5px 1fr;gap:10px;padding:8px 16px;font-size:0.78rem;border-bottom:1px solid rgba(255,255,255,0.045);align-items:center}
.ev:last-child{border:0}
.ev i{height:22px;border-radius:2px;display:block}
.ev b{font-weight:400;color:#eceef2}
.tm{color:rgba(236,238,242,0.45);font-size:0.72rem;font-variant-numeric:tabular-nums}
.sub{color:rgba(236,238,242,0.45);font-size:0.7rem;margin-top:2px}

/* Cột phải: Thẻ KPI theo đúng mẫu HbA1c / Testosterone / Insulin ({40DBE37A} & {F83CBF57}) */
.st-key-g_cat{pointer-events:auto;background:none!important;border:0!important;box-shadow:none!important;padding:0!important}
.st-key-g_cat [role="radiogroup"]{gap:8px!important;padding:2px 0 4px 0}
.st-key-g_cat label{padding:5px 16px;border-radius:999px;background:rgba(24,26,31,0.65);border:1px solid rgba(255,255,255,0.08);margin:0;transition:all .18s ease}
.st-key-g_cat label>div:first-child{display:none}
.st-key-g_cat label p{font-size:0.78rem;color:rgba(236,238,242,0.72)}
.st-key-g_cat label:has(input:checked){background:rgba(200,220,112,0.16);border-color:rgba(200,220,112,0.45)}
.st-key-g_cat label:has(input:checked) p{color:#d8ea86;font-weight:500}

.mg{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;pointer-events:none}
.mc{padding:14px 15px 12px 15px;border-radius:20px!important;display:flex;flex-direction:column;justify-content:space-between}
.mt{font-size:0.78rem;display:flex;align-items:center;gap:8px;color:rgba(236,238,242,0.82);white-space:nowrap;font-weight:400}
.mt i{width:2.5px;height:12px;border-radius:2px;flex-shrink:0}
.mv{margin:8px 0 6px;display:flex;align-items:baseline;justify-content:space-between}
.mv-left{display:flex;align-items:baseline;gap:2px}
.n{font-size:2.05rem;font-weight:200;line-height:1;color:#f5f6f8;letter-spacing:-0.02em;font-variant-numeric:tabular-nums}
.n .dec{color:rgba(236,238,242,0.42);font-weight:200}
.n.t{font-size:1.12rem;font-weight:300;letter-spacing:0}
.u{font-size:0.76rem;color:rgba(236,238,242,0.42);margin-left:4px;font-weight:300}
.arr{font-size:0.86rem;color:rgba(236,238,242,0.55);font-weight:300;margin-left:6px}
.dp-row{display:flex;align-items:center;gap:8px;min-height:22px;margin:2px 0 4px}
.dp{display:inline-block;border-radius:999px;padding:2px 10px;font-size:0.68rem;font-weight:400;background:rgba(200,220,112,0.10);color:#c8dc70;border:1px solid rgba(200,220,112,0.18)}
.dp.up{background:rgba(232,93,86,0.12);color:#e85d56;border-color:rgba(232,93,86,0.22)}
.dp.dn{background:rgba(76,195,138,0.12);color:#4cc38a;border-color:rgba(76,195,138,0.22)}
.dp-arr{font-size:0.76rem;color:rgba(236,238,242,0.55)}
.sp{width:100%;height:34px;margin-top:6px;background:linear-gradient(180deg, rgba(255,255,255,0.035) 0%, rgba(255,255,255,0.01) 100%);border-radius:6px;display:block}
.mn{font-size:0.68rem;color:rgba(236,238,242,0.44);margin-top:6px;line-height:1.3}

.bar{height:5px;background:rgba(255,255,255,0.07);border-radius:3px;overflow:hidden}.bar b{display:block;height:100%;border-radius:3px}
.rk{width:100%;border-collapse:collapse;font-size:0.78rem}.rk td{padding:7px 8px;border-bottom:1px solid rgba(255,255,255,0.045)}.rk tr:last-child td{border-bottom:0}.rk td:first-child{padding-left:16px;color:#eceef2}.rk .num{text-align:right;font-weight:400;font-variant-numeric:tabular-nums}.rk .dl{text-align:right;font-size:0.7rem;color:rgba(236,238,242,0.45);padding-right:16px;font-variant-numeric:tabular-nums}.rk .dl.up{color:#e85d56}
.stk{display:flex;height:8px;margin:12px 16px 8px;border-radius:4px;overflow:hidden;gap:2px}.lg2{display:flex;justify-content:space-between;padding:0 16px 12px;font-size:0.7rem;color:rgba(236,238,242,0.62)}.lg2 i,.lgd i{display:inline-block;width:7px;height:7px;border-radius:2px;margin-right:6px}

/* Thanh điều hướng góc trên trái & phải (không icon AI, viền kính mảnh) */
.st-key-g_nav,.st-key-g_ctrl,.st-key-g_3d,.st-key-g_map2d,.st-key-g_mapmode{background:none!important;border:0!important;backdrop-filter:none!important;box-shadow:none!important;overflow:visible}
.st-key-g_nav{position:fixed!important;top:14px;left:20px;z-index:9999!important;width:auto!important;pointer-events:auto!important}
.st-key-g_nav [data-testid="stHorizontalBlock"]{gap:6px!important;width:auto!important;display:flex!important;flex-direction:row!important;align-items:center!important}
.st-key-g_nav [data-testid="stColumn"]{width:auto!important;min-width:max-content!important;flex:0 0 auto!important}
.st-key-g_nav button,.st-key-g_ctrl button{
    background:rgba(22, 24, 29, 0.72)!important;
    backdrop-filter:blur(20px)!important;
    border:1px solid rgba(255,255,255,0.10)!important;
    border-radius:999px!important;
    color:rgba(236,238,242,0.82)!important;
    padding:5px 14px!important;
    height:34px!important;
    min-height:34px!important;
    cursor:pointer!important;
    pointer-events:auto!important;
    white-space:nowrap!important;
    width:auto!important;
    font-size:0.76rem!important;
    font-weight:400!important;
    transition:all .18s ease!important;
}
.st-key-g_nav button:hover,.st-key-g_ctrl button:hover{background:rgba(38, 42, 50, 0.88)!important;border-color:rgba(255,255,255,0.22)!important;color:#ffffff!important}
.st-key-g_nav button[data-testid="stBaseButton-primary"],.st-key-g_nav button[kind="primary"]{
    background:rgba(200, 220, 112, 0.18)!important;
    color:#d8ea86!important;
    border:1px solid rgba(200, 220, 112, 0.45)!important;
    font-weight:500!important;
}
.st-key-g_ctrl{position:fixed!important;top:14px;right:20px;z-index:9999!important;width:auto!important;pointer-events:auto!important}
.st-key-g_ctrl [data-testid="stPopover"]{width:auto!important}
.st-key-g_ctrl [data-testid="stPopoverBody"] button{border-radius:10px!important;width:100%!important}
[data-testid="stPopoverBody"],div[data-baseweb="popover"]{pointer-events:auto!important;background:rgba(18, 20, 25, 0.94)!important;backdrop-filter:blur(24px)!important;border:1px solid rgba(255,255,255,0.12)!important;border-radius:16px!important;padding:14px 18px!important;box-shadow:0 20px 44px rgba(0,0,0,0.65)!important;z-index:999999!important;min-width:320px!important}
[data-testid="stPopoverBody"] *{pointer-events:auto!important}

/* Viên thuốc trạng thái duy nhất ở chính giữa đỉnh màn hình */
.status{position:fixed;top:14px;left:50%;transform:translateX(-50%);z-index:6;display:inline-flex;gap:14px;align-items:center;padding:7px 18px;border-radius:999px!important;font-size:0.78rem;white-space:nowrap}
.status span{color:rgba(236,238,242,0.52);font-weight:300}
.status b{font-weight:500;color:#eceef2}

/* Cụm nút 3D / Bản đồ (tách biệt hoàn toàn ở dòng bottom: 118px, không bao giờ đè lên chú giải) */
.st-key-g_3d{position:fixed!important;left:auto!important;right:calc(50vw - min(330px, calc(50vw - 440px)) + 90px);bottom:116px;width:54px;height:34px;z-index:20;pointer-events:auto!important}
.st-key-g_map2d{position:fixed!important;left:auto!important;right:calc(50vw - min(330px, calc(50vw - 440px)));bottom:116px;width:84px;height:34px;z-index:20;pointer-events:auto!important}
.st-key-g_mapmode{position:fixed!important;left:auto!important;right:calc(50vw - min(330px, calc(50vw - 440px)) + 150px);bottom:116px;width:96px;height:34px;z-index:20;pointer-events:auto!important}
.st-key-g_3d button,.st-key-g_map2d button,.st-key-g_mapmode button{
    width:100%!important;height:34px!important;min-height:34px!important;border-radius:999px!important;padding:0 10px!important;font-size:0.74rem!important;
    background:rgba(22, 24, 29, 0.72)!important;backdrop-filter:blur(20px)!important;border:1px solid rgba(255,255,255,0.10)!important;color:rgba(236,238,242,0.78)!important;
}
.st-key-g_3d button[kind="primary"],.st-key-g_map2d button[kind="primary"]{
    background:rgba(200, 220, 112, 0.18)!important;color:#d8ea86!important;border:1px solid rgba(200, 220, 112, 0.45)!important;font-weight:500!important;
}

/* Thanh thời gian dạng viên ở đáy (bottom: 54px) */
.st-key-g_time{
    position:fixed!important;left:50%!important;right:auto!important;bottom:52px!important;transform:translateX(-50%)!important;
    width:min(660px,calc(100vw - 880px))!important;height:54px!important;border-radius:999px!important;padding:6px 18px!important;z-index:30!important;
    display:flex!important;justify-content:center!important;align-items:center!important;margin:0!important;overflow:visible!important;
    background:linear-gradient(155deg, rgba(255,255,255,0.065) 0%, rgba(255,255,255,0.018) 100%), rgba(18, 20, 25, 0.75)!important;
    backdrop-filter:blur(28px)!important;border:1px solid rgba(255,255,255,0.10)!important;
    box-shadow:inset 0 1px 0 rgba(255,255,255,0.10), 0 16px 36px rgba(0,0,0,0.5)!important;
}
.st-key-g_time [data-testid="stHorizontalBlock"]{align-items:center!important;gap:12px!important;height:42px!important;overflow:visible!important}
.st-key-g_time [data-testid="stColumn"]{align-self:center!important;min-width:0!important;overflow:visible!important}
.st-key-g_time [data-testid="stElementContainer"]{width:100%}
.st-key-g_time button{
    height:34px!important;min-height:34px!important;width:100%!important;border-radius:999px!important;
    background:rgba(200, 220, 112, 0.18)!important;color:#d8ea86!important;border:1px solid rgba(200, 220, 112, 0.45)!important;font-size:0.76rem!important;font-weight:500!important;
}
.st-key-g_time button:hover{background:rgba(200, 220, 112, 0.28)!important;color:#ffffff!important}
.st-key-g_time [data-testid="stSlider"]{min-height:18px!important;margin-top:-2px!important;padding:0!important;height:20px!important;overflow:visible!important}
.st-key-g_time [data-testid="stThumbValue"],.st-key-g_time [data-testid="stSliderThumbValue"],.st-key-g_time [data-testid="stTickBar"]{display:none!important}
.st-key-g_time [data-testid="stSlider"] > div{overflow:visible!important}
.st-key-g_time [data-testid="stSlider"] [data-baseweb="slider"]{height:18px!important}
.st-key-g_time [data-testid="stSlider"] [data-baseweb="slider"] > div{min-height:18px!important;height:18px!important}
.st-key-g_time [data-testid="stSlider"] [data-baseweb="slider"] > div > div{height:4px!important;top:7px!important;border-radius:999px!important}
.st-key-g_time [data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child{background:#c8dc70!important}
.st-key-g_time [data-testid="stSlider"] [data-baseweb="slider"] > div > div:last-child{background:rgba(255,255,255,0.14)!important}
.st-key-g_time [data-testid="stSlider"] [role="slider"]{width:13px!important;height:13px!important;top:2.5px!important;background:#c8dc70!important;border:2px solid #f4f6e8!important;box-shadow:0 0 10px rgba(200,220,112,0.5)!important;outline:none!important}
.st-key-g_time label{height:0!important;overflow:hidden!important;position:absolute!important;display:none!important}

/* Thanh chú giải nằm riêng ở sát đáy (bottom: 14px), căn giữa tuyệt đối, không đè lên bất kỳ nút nào */
.lgd{
    position:fixed;left:50%;transform:translateX(-50%);bottom:14px;padding:5px 16px;font-size:0.7rem;color:rgba(236,238,242,0.68);
    display:inline-flex;gap:16px;border-radius:999px!important;z-index:6;white-space:nowrap;height:30px;box-sizing:border-box;align-items:center;
}
.clk{line-height:1.05}.clk b{font-size:1.05rem;font-weight:400;display:block;color:#eceef2;font-variant-numeric:tabular-nums}.clk span{display:block;color:rgba(236,238,242,0.45);font-size:0.62rem;margin-top:2px;white-space:nowrap}
.mini2{display:flex;flex-direction:column;justify-content:center;align-items:flex-end;color:rgba(236,238,242,0.45);text-align:right;line-height:1.05}.mini2 b{display:block;font-size:1.25rem;font-weight:300;color:#eceef2;margin-bottom:2px;font-variant-numeric:tabular-nums}.mini2 span{font-size:0.6rem;white-space:nowrap}
'''


def _navigate_to(page_path: str):
    st.session_state["_nav_target"] = page_path
    st.rerun()


def ramp(h: int) -> float:
    return 0.30 + 0.70 * (h / HOURS) ** 1.3


@st.cache_resource(show_spinner=False)
def _get_model(choice: str = "auto"):
    return load_model(choice)


@st.cache_resource(show_spinner=False)
def _base():
    return build_base()


base = _base()
default_basemap = "Bản đồ"


@st.cache_data(show_spinner=False)
def series(scale: float, t0: float, t1: float, model_choice: str = "auto"):
    mdl, _, _ = _get_model(model_choice)
    S, R, CN = [], [], []
    for h in range(HOURS + 1):
        _, cells, d = compute(base, scale * ramp(h), (t0, t1), mdl)
        c = np.asarray(cells)
        S.append(d["score"].to_numpy())
        R.append(d["rain"].to_numpy())
        CN.append([int((c < t0).sum()), int(((c >= t0) & (c < t1)).sum()), int((c >= t1).sum())])
    return np.array(S), np.array(R), np.array(CN)


def _split_num(val_str: str) -> str:
    """Tách phần nguyên (trắng sáng) và phần thập phân (xám mờ) giống ảnh mẫu {40DBE37A}."""
    if "," in str(val_str):
        p1, p2 = str(val_str).split(",", 1)
        return f'{p1}<span class="dec">,{p2}</span>'
    return str(val_str)


def spark(vals, vmax, t, ref=None, col=AC):
    """Sparkline chấm trắng + vòng tròn mục tiêu tại bước hiện tại theo đúng ảnh mẫu {F83CBF57}."""
    idx = np.unique(np.linspace(0, t, 6).round().astype(int))
    vmax_safe = max(float(vmax), 1e-6)
    ys = [46 - 34 * min(max(float(vals[i]) / vmax_safe, 0), 1) for i in idx]
    xs = np.linspace(16, 184, len(idx)) if len(idx) > 1 else [184]
    ref_y = 46 - 34 * min(max(float(ref) / vmax_safe, 0), 1) if ref is not None else 12.0
    line = f'<line x1="0" x2="200" y1="{ref_y:.1f}" y2="{ref_y:.1f}" stroke="rgba(255,255,255,0.28)" stroke-width="1"/>'
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="rgba(236,238,242,0.88)"/>'
        for x, y in zip(xs[:-1], ys[:-1])
    )
    last = (
        f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="3.2" fill="{col}"/>'
        f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="7.5" fill="none" stroke="{col}" stroke-width="1.2" opacity="0.85"/>'
    )
    return f'<svg class="sp" viewBox="0 0 200 54">{line}{dots}{last}</svg>'


def card(title, val, unit, col, dl=None, fmt=vn, sp="", note="", small=False):
    arr = "↗" if (dl is not None and dl > 0.0005) else ("↘" if (dl is not None and dl < -0.0005) else "→")
    pill = ""
    if dl is not None and abs(float(dl)) > 0.0005:
        c = "up" if dl > 0.0005 else "dn"
        sign = "+" if dl > 0.0005 else ""
        pill = f'<div class="dp-row"><span class="dp {c}">{sign}{fmt(dl)} {unit.replace("/", "").strip()}</span><span class="dp-arr">{arr}</span></div>'
    val_html = val if small else _split_num(val)
    return (
        f'<div class="mc">'
        f'<div><div class="mt"><i style="background:{col}"></i>{title}</div>'
        f'<div class="mv"><div class="mv-left"><span class="n{" t" if small else ""}">{val_html}</span>'
        f'<span class="u">{unit}</span></div><span class="arr">{arr}</span></div>'
        f"{pill}</div>"
        f'<div>{sp}<div class="mn">{note}</div></div></div>'
    )


def _morse_segments(series_1d: np.ndarray, t: int, thr_val: float) -> str:
    """Tạo thanh chấm-gạch biểu diễn chuỗi diễn biến theo phong cách Weight and Trend trong ảnh a04eae92."""
    n_seg = 18
    indices = np.linspace(0, HOURS, n_seg).round().astype(int)
    segs = []
    for idx in indices:
        v = float(series_1d[idx])
        w = 18 if idx <= t and v >= thr_val * 0.7 else (10 if idx <= t else 3)
        cls = "hi" if (idx <= t and v >= thr_val) else ("on" if idx <= t else "")
        segs.append(f'<i class="{cls}" style="width:{w}px"></i>')
    return "".join(segs)


@st.dialog("Phân tích Diễn biến Kịch bản 24 Giờ", width="large")
def show_charts_dialog(S, R, CN, cells, df, k: int, t: int, thr: tuple[float, float]):
    z = df.iloc[k]
    st.caption(
        f"Phân tích chuyên sâu theo giờ kịch bản (Giờ hiện tại: {hh(t)}) · "
        f"Khu vực tiêu điểm: {z['name']} ({z['code']})."
    )
    c1, c2 = st.columns([1, 1.6])
    with c1:
        st.markdown(f"**Mức nguy cơ hiện tại — {z['name']}**")
        st.plotly_chart(fig_gauge(float(z["score"]), str(z["level"]), thr), width="stretch")
    with c2:
        st.markdown(f"**Xu hướng Điểm nguy cơ 24h — {z['name']}**")
        st.plotly_chart(fig_trend(S[:, k], t, thr, str(z["level"])), width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f"**Diễn biến Lượng mưa 24h (mm) — {z['name']}**")
        st.plotly_chart(fig_rain(R[:, k], t), width="stretch")
    with c4:
        st.markdown("**Phân phối Tần suất Điểm nguy cơ 324 Ô lưới**")
        st.plotly_chart(fig_hist(cells, thr), width="stretch")

    st.markdown("**Diễn biến Số lượng Ô lưới theo 3 Mức nguy cơ suốt 24 Giờ**")
    st.plotly_chart(fig_timeline(CN, t, NC * NC), width="stretch")


def _reset_scenario():
    st.session_state["scale"] = 1.0
    st.session_state["thr"] = (0.25, 0.45)
    st.session_state["rain_alert"] = 100
    st.session_state["model_choice"] = "auto"
    st.session_state["show_grid"] = True
    st.session_state["show_areas"] = True
    st.session_state["show_hist"] = True


def monitor():
    ss = st.session_state
    for k_, v_ in dict(
        t_step=HOURS,
        play=False,
        view="3D",
        cat="Nguy cơ",
        scale=1.0,
        area_pick="Tổng quan toàn vùng",
        rain_alert=100,
        thr=(0.25, 0.45),
        model_choice="auto",
        show_grid=True,
        show_areas=True,
        show_hist=True,
    ).items():
        ss.setdefault(k_, v_)
    ss.setdefault("basemap", default_basemap)

    if ss.play:
        now_ts = time.monotonic()
        last_ts = ss.get("_last_play_tick", 0.0)
        if now_ts - last_ts >= 1.15:
            ss["_last_play_tick"] = now_ts
            if ss.t_step >= HOURS:
                ss.play = False
                st.rerun()
            else:
                ss.t_step = int(ss.t_step) + 1
                if ss.t_step >= HOURS:
                    ss.play = False
                    st.rerun()

    t = int(ss.t_step)
    prev = max(t - 1, 0)
    scale, RA = float(ss.scale), float(ss.rain_alert)
    raw_thr = ss.get("thr", (0.25, 0.45))
    if isinstance(raw_thr, (tuple, list, np.ndarray)) and len(raw_thr) == 2:
        lo, hi = sorted((float(raw_thr[0]), float(raw_thr[1])))
        lo = min(max(lo, 0.05), 0.90)
        hi = max(lo + 0.05, min(hi, 0.95))
    else:
        lo, hi = 0.25, 0.45
    thr = (lo, hi)

    model_choice = ss.get("model_choice", "auto")
    model_obj, model_name, _ = _get_model(model_choice)

    S, R, CN = series(scale, thr[0], thr[1], model_choice)
    risk, cells, df = compute(base, scale * ramp(t), thr, model_obj)
    cells = np.asarray(cells)
    names = df["name"].tolist()
    n = len(names)

    raw_pick = ss.get("area_pick")
    selected_area = raw_pick if raw_pick in names else None
    k = names.index(selected_area) if selected_area else int(np.argmax(df["score"].to_numpy()))
    z = df.iloc[k]

    lvl = lambda v: "Cao" if v >= thr[1] else ("Trung bình" if v >= thr[0] else "Thấp")
    lcol = lambda v: HI if v >= thr[1] else (MI if v >= thr[0] else LO)
    cut = np.array(thr)
    lv_all = (S[:, :, None] >= cut[None, None, :]).sum(axis=2)
    nh, nm = (lv_all == 2).sum(axis=1), (lv_all == 1).sum(axis=1)
    n_high, n_mid = int(nh[t]), int(nm[t])
    status, scol = ("Cảnh báo", HI) if n_high else (("Theo dõi", MI) if n_mid else ("Bình thường", LO))
    glow = {"Cảnh báo": "210, 52, 48", "Theo dõi": "215, 155, 50", "Bình thường": "60, 165, 115"}[status]
    st.markdown(
        f"<style>.stApp{{background:radial-gradient(ellipse 80% 40% at 50% 110%, rgba({glow},0.32), "
        f"transparent 70%), #08090c}}</style>",
        unsafe_allow_html=True,
    )

    # ---- Sân khấu 3D / Bản đồ 2D
    with st.container(key="stage"):
        if ss.view == "3D":
            fig = render_3d_terrain(
                base,
                risk,
                df,
                thr,
                show_hist=ss.show_hist,
                show_areas=ss.show_areas,
                height=720,
                selected_area=selected_area,
            )
        else:
            fig = render_2d_workspace(
                base,
                cells,
                df,
                thr,
                map_style=ss.basemap,
                show_risk_grid=ss.show_grid,
                show_hist=ss.show_hist,
                show_areas=ss.show_areas,
                height=720,
                selected_area=selected_area,
                risk_field=risk,
                zoom=9.15,
            )
        chart_selection = st.plotly_chart(
            fig,
            config={"displayModeBar": False, "scrollZoom": True, "responsive": True},
            key="f_stage",
            on_select="rerun",
            selection_mode="points",
            width="stretch",
        )
        clicked_points = getattr(getattr(chart_selection, "selection", None), "points", [])
        if clicked_points:
            clicked = clicked_points[0]
            customdata = clicked.get("customdata")
            clicked_area = ""
            if isinstance(customdata, (list, tuple, np.ndarray)) and len(customdata) > 0:
                if ss.view != "3D" and len(customdata) > 5:
                    clicked_area = str(customdata[5])
                else:
                    clicked_area = str(customdata[0])
            elif customdata is not None:
                clicked_area = str(customdata)

            if clicked_area not in names:
                clat = clicked.get("lat", clicked.get("y"))
                clon = clicked.get("lon", clicked.get("x"))
                if isinstance(clat, (int, float)) and isinstance(clon, (int, float)):
                    if 14.5 <= float(clat) <= 16.0 and 107.0 <= float(clon) <= 109.0:
                        dists = np.hypot(df["lat"] - float(clat), df["lon"] - float(clon))
                        if float(dists.min()) <= 0.12:
                            clicked_area = str(df.iloc[int(dists.argmin())]["name"])

            if clicked_area in names and ss.area_pick != clicked_area:
                ss.area_pick = clicked_area
                st.rerun(scope="fragment")

    # ---- Nhật ký sự kiện
    events = []
    for kk in range(n):
        for h in range(1, t + 1):
            if lv_all[h, kk] != lv_all[h - 1, kk]:
                nw = ["Thấp", "Trung bình", "Cao"][lv_all[h, kk]]
                events.append((
                    h,
                    kk,
                    f"{'lên' if lv_all[h, kk] > lv_all[h - 1, kk] else 'xuống'} mức {nw}",
                    f"Điểm nguy cơ {vn(S[h, kk])}",
                    [LO, MI, HI][lv_all[h, kk]],
                ))
        cr = np.where(R[: t + 1, kk] >= RA)[0]
        if len(cr):
            h = int(cr[0])
            events.append((
                h,
                kk,
                "vượt ngưỡng mưa chú ý",
                f"Mưa 24 giờ {R[h, kk]:.0f} mm · ngưỡng {RA:.0f} mm",
                "#c8dc70",
            ))
    events.sort(key=lambda e: (-e[0], e[1]))
    ev = base["events"]
    if selected_area:
        near = ev[
            (ev["lat"].between(z["lat"] - 0.08, z["lat"] + 0.08))
            & (ev["lon"].between(z["lon"] - 0.08, z["lon"] + 0.08))
        ].sort_values("date", ascending=False)
    else:
        near = ev.sort_values("date", ascending=False)

    # ---- Thẻ chỉ số cột phải theo phong cách {40DBE37A} & {F83CBF57}
    gm = float(S[t].max())
    rmax = max(float(R.max()), float(RA))
    ii = lambda x: f"{int(round(x))}"
    pc = lambda col: f"Cao hơn {100 * float((df[col] < z[col]).mean()):.0f}% số khu vực trong vùng"
    area_selected = selected_area is not None

    if ss.cat == "Nguy cơ":
        cs = [
            card(
                f"Điểm · {z['name']}" if not area_selected else "Điểm khu vực",
                vn(z["score"]),
                "/ 1",
                lcol(z["score"]),
                S[t, k] - S[prev, k],
                vn,
                spark(S[:, k], 1, t, thr[1], lcol(z["score"])),
                f"Mức {lvl(z['score'])}, ngưỡng cao từ {vn(thr[1])}",
            ),
            card(
                "Cao nhất toàn vùng",
                vn(gm),
                "/ 1",
                lcol(gm),
                gm - float(S[prev].max()),
                vn,
                spark(S.max(axis=1), 1, t, thr[1], AC),
                f"Điểm nóng: {names[int(np.argmax(S[t]))]}",
            ),
            card(
                "Khu vực mức cao",
                str(n_high),
                f"/ {n}",
                HI,
                n_high - int(nh[prev]),
                ii,
                spark(nh, n, t, None, HI),
                f"Đang theo dõi: {n_mid} khu vực",
            ),
            card(
                "Ô lưới mức cao",
                str(int(CN[t, 2])),
                f"/ {NC * NC}",
                HI,
                CN[t, 2] - CN[prev, 2],
                ii,
                spark(CN[:, 2], max(int(CN[:, 2].max()), 12), t, None, HI),
                f"Mức trung bình: {int(CN[t, 1])} ô",
            ),
            card(
                f"Mưa 24h · {z['name']}" if not area_selected else "Mưa 24 giờ khu vực",
                f"{R[t, k]:.0f}",
                "mm",
                AC,
                R[t, k] - R[prev, k],
                ii,
                spark(R[:, k], rmax, t, RA, AC),
                f"Ngưỡng chú ý {RA:.0f} mm",
            ),
            card(
                "Mưa lớn nhất vùng",
                f"{R[t].max():.0f}",
                "mm",
                AC,
                R[t].max() - R[prev].max(),
                ii,
                spark(R.max(axis=1), rmax, t, RA, AC),
                f"Tại khu vực {names[int(np.argmax(R[t]))]}",
            ),
            card(
                "Vượt ngưỡng mưa",
                str(int((R[t] >= RA).sum())),
                f"/ {n}",
                MI,
                int((R[t] >= RA).sum()) - int((R[prev] >= RA).sum()),
                ii,
                spark((R >= RA).sum(axis=1), n, t, None, MI),
                "Số xã vượt ngưỡng mưa chú ý",
            ),
            card(
                f"Độ dốc · {z['name']}" if not area_selected else "Độ dốc khu vực",
                vn(z["slope"], 1),
                "°",
                MI,
                None,
                vn,
                "",
                pc("slope"),
            ),
        ]
    elif ss.cat == "Mưa":
        cs = [
            card(
                f"Mưa 24h · {z['name']}" if not area_selected else "Mưa 24 giờ khu vực",
                f"{R[t, k]:.0f}",
                "mm",
                AC,
                R[t, k] - R[prev, k],
                ii,
                spark(R[:, k], rmax, t, RA, AC),
                f"Ngưỡng chú ý {RA:.0f} mm",
            ),
            card(
                "Mưa lớn nhất vùng",
                f"{R[t].max():.0f}",
                "mm",
                AC,
                R[t].max() - R[prev].max(),
                ii,
                spark(R.max(axis=1), rmax, t, RA, AC),
                f"Tại khu vực {names[int(np.argmax(R[t]))]}",
            ),
            card(
                "Mưa trung bình vùng",
                f"{R[t].mean():.0f}",
                "mm",
                AC,
                R[t].mean() - R[prev].mean(),
                ii,
                spark(R.mean(axis=1), rmax, t, RA, AC),
                "Trung bình 12 xã giám sát",
            ),
            card(
                "Mưa nhỏ nhất vùng",
                f"{R[t].min():.0f}",
                "mm",
                LO,
                R[t].min() - R[prev].min(),
                ii,
                spark(R.min(axis=1), rmax, t, RA, LO),
                f"Tại khu vực {names[int(np.argmin(R[t]))]}",
            ),
            card(
                "Vượt ngưỡng mưa",
                str(int((R[t] >= RA).sum())),
                f"/ {n}",
                MI,
                int((R[t] >= RA).sum()) - int((R[prev] >= RA).sum()),
                ii,
                spark((R >= RA).sum(axis=1), n, t, None, MI),
                "Số xã vượt ngưỡng mưa chú ý",
            ),
            card(
                "Độ ẩm đất khu vực",
                f"{100 * float(z.get('soil', 0.5)):.0f}",
                "%",
                AC,
                None,
                vn,
                "",
                f"Hệ số kịch bản mưa: {vn(scale, 1)}×",
            ),
        ]
    else:
        cs = [
            card(
                f"Độ cao · {z['name']}" if not area_selected else "Độ cao khu vực",
                f"{z['elev']:.0f}",
                "m",
                AC,
                None,
                vn,
                "",
                pc("elev"),
            ),
            card(
                f"Độ dốc · {z['name']}" if not area_selected else "Độ dốc khu vực",
                vn(z["slope"], 1),
                "°",
                MI,
                None,
                vn,
                "",
                pc("slope"),
            ),
            card("Lớp phủ bề mặt", z["cover"], "", LO, None, vn, "", f"Khu vực {z['name']} · ESA WorldCover", True),
            card("Tọa độ địa lý", f"{vn(z['lat'])}°B", "", AC, None, vn, "", f"{vn(z['lon'])}°Đ · Mã {z['code']}", True),
            card(
                "Độ cao lớn nhất vùng",
                f"{df['elev'].max():.0f}",
                "m",
                AC,
                None,
                vn,
                "",
                f"Khu vực {df.loc[df['elev'].idxmax(), 'name']}",
            ),
            card(
                "Độ dốc lớn nhất vùng",
                vn(df["slope"].max(), 1),
                "°",
                MI,
                None,
                vn,
                "",
                f"Khu vực {df.loc[df['slope'].idxmax(), 'name']}",
            ),
        ]

    # ---- Cột trái (thiết kế theo mẫu a04eae92)
    with st.container(key="colL"):
        # 1. Viên thuốc chọn khu vực nằm tách biệt phía trên thẻ Hồ sơ (giống Record: Family History ⌄)
        area_options = ["Tổng quan toàn vùng"] + names
        curr_opt = selected_area if selected_area in names else "Tổng quan toàn vùng"
        with st.container(key="g_sel"):
            st.selectbox(
                "Khu vực quan sát",
                area_options,
                index=area_options.index(curr_opt),
                key="area_pick",
                label_visibility="collapsed",
            )

        # 2. Thẻ Hồ sơ khu vực (Patient Profile Glass Card style)
        z_score = float(z["score"])
        z_lvl = lvl(z_score)
        z_col = lcol(z_score)
        card_tone = "critical" if z_lvl == "Cao" else ("watch" if z_lvl == "Trung bình" else "")
        morse_html = _morse_segments(R[:, k], t, RA)

        if not area_selected:
            prof_title = "Hồ sơ toàn vùng"
            c1_l, c1_v = "Phạm vi", f"{len(df)} xã giám sát"
            c2_l, c2_v = "Điểm nóng", str(z["name"])
            c3_l, c3_v = "Độ dốc TB", f"{vn(float(df['slope'].mean()), 1)}°"
            rain_label = f"Mưa lớn nhất và xu hướng ({z['name']})"
            rain_val_str = f"{float(R[t].max()):.0f} mm"
            bot_sub = f"Cao nhất tại {z['name']} ({z['code']})"
        else:
            prof_title = f"Hồ sơ khu vực · {z['name']}"
            c1_l, c1_v = "Độ cao", f"{z['elev']:.0f} m"
            c2_l, c2_v = "Độ dốc", f"{vn(z['slope'], 1)}°"
            c3_l, c3_v = "Lớp phủ", str(z["cover"])
            rain_label = "Lượng mưa 24 giờ và xu hướng"
            rain_val_str = f"{float(R[t, k]):.0f} mm"
            bot_sub = f"Mã: {z['code']} · Độ ẩm {100 * float(z.get('soil', 0.5)):.0f}%"

        st.markdown(
            f'<div class="prof-card {card_tone}">'
            f'<div class="prof-top"><span>{prof_title}</span><small>Giờ {hh(t)}</small></div>'
            f'<div class="prof-grid3">'
            f'<div><div class="lbl">{c1_l}:</div><div class="val">{c1_v}</div></div>'
            f'<div><div class="lbl">{c2_l}:</div><div class="val">{c2_v}</div></div>'
            f'<div><div class="lbl">{c3_l}:</div><div class="val">{c3_v}</div></div>'
            f"</div>"
            f'<div class="prof-trend-hdr"><span>{rain_label}</span><span>{rain_val_str}</span></div>'
            f'<div class="morse-bar">{morse_html}</div>'
            f'<div class="prof-bot">'
            f'<div class="prof-bot-left"><div class="t1">Điểm nguy cơ</div><div class="t2">{bot_sub}</div></div>'
            f'<div class="prof-bot-mid"><span class="prof-dot" style="background:{z_col}"></span><span>{z_lvl}</span></div>'
            f'<div class="prof-bot-right">'
            f'<div class="prof-lvl-row"><b>{vn(z_score)}</b><i style="background:{z_col}"></i><s style="background:{z_col}88"></s></div>'
            f'<div class="prof-lvl-row"><span style="font-size:0.65rem;color:rgba(236,238,242,0.4)">Ngưỡng</span><i style="background:{LO}"></i></div>'
            f'<div class="prof-lvl-row"><b>{vn(thr[0])}</b><i style="background:{MI}"></i></div>'
            f"</div></div></div>",
            unsafe_allow_html=True,
        )

        # 3. Hai thẻ vuông .two (Tomography / Radiography style)
        last_ev = f"Gần nhất {near.iloc[0]['date']}" if len(near) else "Chưa ghi nhận"
        st.markdown(
            '<div class="two">'
            f'<div class="mini"><div><div class="t">Hồ sơ lịch sử<span>↗</span></div><div class="d">{last_ev}</div></div>'
            f'<div class="n">{len(near)}<small>vụ</small></div></div>'
            f'<div class="mini"><div><div class="t">Diễn biến kịch bản<span>↗</span></div><div class="d">Tính đến {hh(t)}</div></div>'
            f'<div class="n">{len(events)}<small>mốc</small></div></div>'
            "</div>",
            unsafe_allow_html=True,
        )

        # 4. Trạm quan sát khu vực
        st.markdown(
            '<div class="g"><div class="ph"><span>Trạm quan sát khu vực</span><small>12 xã trọng điểm</small></div>'
            '<div class="st4">'
            f'<div class="st4cell"><b>{len(df)}</b>Điểm giám sát</div>'
            f'<div class="st4cell"><b>{R[t].mean():.0f} mm</b>Mưa TB toàn vùng</div>'
            f'<div class="st4cell"><b>{vn(float(df["slope"].mean()), 1)}°</b>Độ dốc TB</div>'
            f'<div class="st4cell"><b>{int((R[t] >= RA).sum())}</b>Xã vượt ngưỡng mưa</div>'
            "</div></div>",
            unsafe_allow_html=True,
        )

        # 5. Cảnh báo vận hành (trực tiếp 1 thẻ .g, không bọc st.container gây viền đôi)
        alert_rows = [(names[i], float(R[t, i])) for i in np.where(R[t] >= RA)[0]]
        alert_rows.sort(key=lambda item: item[1], reverse=True)
        if alert_rows:
            alert_html = "".join(
                f'<div class="ev"><span class="tm">{hh(t)}</span><i style="background:{AC}"></i>'
                f'<div><b>{name}</b> · Cảnh báo mưa<div class="sub">{rain:.0f} mm · ngưỡng {RA:.0f} mm</div></div></div>'
                for name, rain in alert_rows
            )
        else:
            alert_html = (
                f'<div class="ev"><span class="tm">{hh(t)}</span><i style="background:{LO}"></i>'
                '<div><b>Toàn vùng ổn định</b><div class="sub">Chưa có xã vượt ngưỡng mưa chú ý</div></div></div>'
            )
        st.markdown(
            f'<div class="g"><div class="ph"><span>Cảnh báo vận hành</span><small>{len(alert_rows)} khu vực</small></div>{alert_html}</div>',
            unsafe_allow_html=True,
        )

        # 6. Nhật ký sự kiện (trực tiếp 1 thẻ .g, không viền đôi)
        log = (
            "".join(
                f'<div class="ev"><span class="tm">{hh(h)}</span><i style="background:{c}"></i>'
                f'<div><b>{names[kk]}</b> {tx}<div class="sub">{sb}</div></div></div>'
                for h, kk, tx, sb, c in events[:20]
            )
            or '<div class="ev"><span class="tm">--:--</span><i style="background:rgba(255,255,255,0.2)"></i>'
            '<div class="sub">Chưa phát sinh sự kiện chuyển mức.</div></div>'
        )
        st.markdown(
            f'<div class="g"><div class="ph"><span>Nhật ký diễn biến</span><small>{len(events)} mốc</small></div>{log}</div>',
            unsafe_allow_html=True,
        )

    # ---- Cột phải
    with st.container(key="colR"):
        with st.container(key="g_cat"):
            st.radio(
                "Nhóm chỉ số",
                ["Nguy cơ", "Mưa", "Địa hình"],
                horizontal=True,
                key="cat",
                label_visibility="collapsed",
            )
        st.markdown('<div class="mg">' + "".join(cs) + "</div>", unsafe_allow_html=True)
        lo_, mi_, hi_ = (int(x) for x in CN[t])
        tot = NC * NC
        st.markdown(
            f'<div class="g"><div class="ph"><span>Phân bố {tot} ô lưới địa hình</span><small>Giờ {hh(t)}</small></div>'
            f'<div class="stk"><b style="width:{100 * lo_ / tot:.1f}%;background:{LO}"></b>'
            f'<b style="width:{100 * mi_ / tot:.1f}%;background:{MI}"></b>'
            f'<b style="width:{100 * hi_ / tot:.1f}%;background:{HI}"></b></div>'
            f'<div class="lg2"><span><i style="background:{LO}"></i>Thấp {lo_}</span>'
            f'<span><i style="background:{MI}"></i>Trung bình {mi_}</span>'
            f'<span><i style="background:{HI}"></i>Cao {hi_}</span></div></div>',
            unsafe_allow_html=True,
        )
        rows = ""
        for i in np.argsort(-S[t])[:3]:
            sc, dl = float(S[t, i]), float(S[t, i] - S[prev, i])
            sg = "+" if dl > 0.0005 else ""
            rows += (
                f"<tr><td>{names[i]}</td>"
                f'<td style="width:36%"><div class="bar"><b style="width:{100 * sc:.0f}%;background:{lcol(sc)}"></b></div></td>'
                f'<td class="num">{vn(sc)}</td>'
                f'<td class="dl {"up" if dl > 0.0005 else ""}">{sg}{vn(dl)}</td></tr>'
            )
        st.markdown(
            f'<div class="g"><div class="ph"><span>Trọng điểm nguy cơ cao nhất</span><small>So với giờ trước</small></div>'
            f'<table class="rk">{rows}</table></div>',
            unsafe_allow_html=True,
        )

    # ---- Viên thuốc trạng thái ở đỉnh & Chú giải ở sát đáy
    st.markdown(
        f'<div class="g status"><i style="width:8px;height:8px;border-radius:50%;background:{scol};box-shadow:0 0 8px {scol}"></i><b>{status}</b>'
        f"<span>{hh(t)} · Giờ {t}/{HOURS}</span><span>{DATA_MODE}</span>"
        f"<span>Mô hình: {MODEL_VI.get(model_name, model_name)}</span></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="g lgd"><span><i style="background:{LO}"></i>Thấp (&lt; {vn(thr[0])})</span>'
        f'<span><i style="background:{MI}"></i>Trung bình ({vn(thr[0])}–{vn(thr[1])})</span>'
        f'<span><i style="background:{HI}"></i>Cao (≥ {vn(thr[1])})</span>'
        '<span><i style="background:#d8dee9;border-radius:50%"></i>Điểm sạt lở lịch sử</span></div>',
        unsafe_allow_html=True,
    )

    # ---- Thanh điều hướng góc trên bên trái (Tối giản, không icon AI)
    with st.container(key="g_nav"):
        nv1, nv2, nv3, nv4 = st.columns(4, gap="small")
        with nv1:
            st.button("Giám sát 3D", key="nav_overview", type="primary")
        with nv2:
            if st.button("Phân tích 24h ↗", key="nav_charts"):
                show_charts_dialog(S, R, CN, cells, df, k, t, thr)
        with nv3:
            if st.button("Hồ sơ lịch sử", key="nav_hist"):
                _navigate_to("app/pages/3_Lich_Su_Sat_Lo.py")
        with nv4:
            if st.button("Đánh giá mô hình", key="nav_ai"):
                _navigate_to("app/pages/2_AI_Evaluation.py")

    # ---- Nút điều chỉnh kịch bản góc trên bên phải
    with st.container(key="g_ctrl"):
        with st.popover("Thiết lập kịch bản ▾"):
            st.selectbox(
                "Mô hình dự báo",
                options=list(MODEL_OPTIONS.keys()),
                format_func=lambda x: MODEL_OPTIONS.get(x, x),
                key="model_choice",
            )
            st.slider("Hệ số lượng mưa (×)", 0.5, 2.0, step=0.1, key="scale")
            st.slider("Ngưỡng phân mức (Trung bình – Cao)", 0.05, 0.95, step=0.05, key="thr")
            st.number_input("Ngưỡng mưa chú ý (mm / 24h)", 30, 400, step=10, key="rain_alert")
            st.checkbox("Lớp lưới nguy cơ", key="show_grid")
            st.checkbox("Điểm xã giám sát", key="show_areas")
            st.checkbox("Điểm sạt lở lịch sử", key="show_hist")
            st.button("Đặt lại mặc định", key="btn_reset_scenario", on_click=_reset_scenario, width="stretch")

    if ss.view != "3D":
        with st.container(key="g_mapmode"):
            with st.popover("Lớp nền ▾"):
                for base_option in BASEMAPS:
                    if st.button(
                        base_option,
                        key=f"basemap_{base_option}",
                        width="stretch",
                        type="primary" if ss.basemap == base_option else "secondary",
                    ):
                        ss.basemap = base_option
                        st.rerun(scope="fragment")

    # ---- Nút chuyển đổi 3D / Bản đồ (nằm riêng ở dòng bottom: 116px)
    with st.container(key="g_3d"):
        if st.button("3D", key="v3d", type="primary" if ss.view == "3D" else "secondary"):
            ss.view = "3D"
            st.rerun(scope="fragment")
    with st.container(key="g_map2d"):
        if st.button("Bản đồ", key="v2d", type="primary" if ss.view != "3D" else "secondary"):
            ss.view = "Bản đồ"
            st.rerun(scope="fragment")

    # ---- Thanh thời gian dạng viên ở đáy (bottom: 52px)
    with st.container(key="g_time"):
        ta, tb, tc, td = st.columns([1.15, 1.1, 4.9, 1.35], gap="small", vertical_alignment="center")
        with ta:
            finished = t >= HOURS
            play_label = "Tạm dừng" if ss.play else ("Phát lại" if finished else "Phát")
            if st.button(play_label, key="btn_play", type="primary"):
                if ss.play:
                    ss.play = False
                else:
                    if finished:
                        ss.t_step = 0
                    ss.play = True
                    ss["_last_play_tick"] = time.monotonic()
                st.rerun()
        with tb:
            st.markdown(f'<div class="clk"><b>{hh(t)}</b><span>{t} / {HOURS} giờ</span></div>', unsafe_allow_html=True)
        with tc:
            st.slider("Giờ của kịch bản", 0, HOURS, key="t_step", format="%d giờ", label_visibility="collapsed")
        with td:
            st.markdown(f'<div class="mini2"><b>{hi_} ô</b><span>mức cao hiện tại</span></div>', unsafe_allow_html=True)


st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

run = st.fragment(run_every=1.2 if st.session_state.get("play") else None)(monitor)
run()
