"""
Trang tra cứu và phân tích Hồ sơ Lịch sử Sạt lở Đất
Khu vực: Nam Trà My & Phước Sơn, Quảng Nam
Trọng tâm: Địa điểm cụ thể (Xã/Huyện), Nguyên nhân kích hoạt & Thiệt hại ước tính
Phong cách thiết kế: Dark Glassmorphic HUD Dashboard
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "app") not in sys.path:
    sys.path.insert(0, str(ROOT / "app"))

from core.data_engine import build_base, assign_commune_info

DB_PATH = ROOT / "data" / "landslide.db"

if not st.session_state.get("_root_navigation", False):
    st.set_page_config(
        page_title="Hồ sơ Lịch sử Sạt lở Đất",
        page_icon="📜",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def _safe_switch_page(target: str):
    try:
        st.switch_page(target)
    except Exception:
        alt = target.replace("app/", "", 1) if target.startswith("app/") else f"app/{target}"
        st.switch_page(alt)


CAUSE_COLORS = {
    "Mưa lớn kéo dài": "#38bdf8",           # Cyan
    "Suy yếu địa chất": "#f5b942",          # Amber
    "Hoạt động nhân tạo": "#d4e88a",        # Lime
    "Bão hoặc áp thấp nhiệt đới": "#ff5a52", # Red
}

CSS_PAGE = """
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@200;300;400;500;600;700&display=swap');

html, body, .stApp {
    font-family: 'Be Vietnam Pro', system-ui, sans-serif !important;
    background: radial-gradient(ellipse 85% 42% at 50% 112%, rgba(212, 232, 138, 0.12), transparent 72%), #07080b !important;
    color: #e8e9ec !important;
}

[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], footer {
    display: none !important;
}

.block-container {
    max-width: 1440px !important;
    padding: 18px 28px 48px 28px !important;
    margin: 0 auto !important;
}

.brand-box b {
    font-size: 1.18rem;
    font-weight: 600;
    color: #ffffff;
    display: block;
    letter-spacing: -0.01em;
}
.brand-box span {
    font-size: 0.8rem;
    color: #8b8f98;
    display: block;
    margin-top: 2px;
}

/* Nút bấm navigation pills */
.stButton button, .stDownloadButton button {
    background: rgba(34, 36, 40, 0.85) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 999px !important;
    color: #e8e9ec !important;
    font-weight: 500 !important;
    padding: 6px 16px !important;
    font-size: 0.8rem !important;
    white-space: nowrap !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}
.stButton button:hover, .stDownloadButton button:hover {
    background: rgba(50, 54, 60, 0.95) !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    color: #ffffff !important;
}
.stButton button[data-testid="stBaseButton-primary"], .stButton button[kind="primary"] {
    background: #d4e88a !important;
    color: #1b2208 !important;
    border-color: #d4e88a !important;
    font-weight: 600 !important;
    cursor: default !important;
}

/* KPI Cards */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 14px 0 20px 0;
}
.kpi-card {
    background: rgba(34, 36, 40, 0.58);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 14px 18px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}
.kpi-head {
    font-size: 0.76rem;
    color: #8b8f98;
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 500;
}
.kpi-head i {
    width: 3px;
    height: 12px;
    border-radius: 2px;
    display: inline-block;
}
.kpi-num {
    font-size: 1.85rem;
    font-weight: 200;
    color: #ffffff;
    line-height: 1.15;
    margin: 6px 0 2px 0;
    font-variant-numeric: tabular-nums;
}
.kpi-unit {
    font-size: 0.78rem;
    color: #8b8f98;
    font-weight: 400;
}
.kpi-sub {
    font-size: 0.72rem;
    color: #8b8f98;
}

/* Khung kính chuẩn thông qua st.container(key="glass_...") */
[class*="st-key-glass_"] {
    background: rgba(34, 36, 40, 0.58) !important;
    backdrop-filter: blur(18px) !important;
    -webkit-backdrop-filter: blur(18px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 20px !important;
    padding: 16px 20px !important;
    margin-bottom: 18px !important;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35) !important;
}
.panel-head {
    font-size: 0.86rem;
    font-weight: 600;
    color: #d6d8dc;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.panel-head small {
    font-size: 0.72rem;
    color: #8b8f98;
    font-weight: 400;
}

/* Input / Select styling */
div[data-baseweb="select"] > div {
    background: rgba(22, 24, 28, 0.85) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 12px !important;
    color: #e8e9ec !important;
    font-size: 0.82rem !important;
}
div[data-baseweb="input"] {
    background: rgba(22, 24, 28, 0.85) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 12px !important;
    font-size: 0.82rem !important;
}
div[data-baseweb="input"] input {
    color: #e8e9ec !important;
}
label p {
    font-size: 0.78rem !important;
    color: #8b8f98 !important;
    margin-bottom: 4px !important;
}

/* Pills for Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(25, 27, 31, 0.7) !important;
    border-radius: 999px !important;
    padding: 4px !important;
    gap: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    width: fit-content !important;
    margin-bottom: 14px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 6px 18px !important;
    color: #8b8f98 !important;
    font-size: 0.8rem !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: #d4e88a !important;
    color: #1b2208 !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

[data-testid="stPlotlyChart"] {
    border-radius: 14px !important;
    overflow: hidden !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
}

.map-note {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.72rem;
    color: #8b8f98;
    margin-top: 8px;
    padding: 0 4px;
}
"""
st.markdown(f"<style>{CSS_PAGE}</style>", unsafe_allow_html=True)


@st.cache_data
def load_data_with_locations() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tải 46 sự kiện và liên kết chính xác với xã/huyện địa bàn."""
    areas_df = pd.DataFrame()
    events_df = pd.DataFrame()

    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(DB_PATH)
            areas_df = pd.read_sql_query("SELECT code, name, lat, lon FROM areas", conn)
            events_df = pd.read_sql_query(
                "SELECT event_id AS id, event_date AS date, lat, lon, elevation AS elev, "
                "cause, damage_mil_vnd AS damage, source FROM landslide_events ORDER BY event_date DESC",
                conn,
            )
            conn.close()
        except Exception:
            pass

    if areas_df.empty or events_df.empty:
        base = build_base()
        areas_df = pd.DataFrame([
            {"code": "KV01", "name": "Trà Mai", "lat": 15.11, "lon": 108.01},
            {"code": "KV02", "name": "Trà Don", "lat": 15.20, "lon": 108.09},
            {"code": "KV03", "name": "Trà Leng", "lat": 15.10, "lon": 107.94},
            {"code": "KV04", "name": "Trà Vân", "lat": 15.18, "lon": 108.15},
            {"code": "KV05", "name": "Trà Linh", "lat": 15.07, "lon": 108.12},
            {"code": "KV06", "name": "Trà Tập", "lat": 15.19, "lon": 108.01},
            {"code": "KV07", "name": "Phước Mỹ", "lat": 15.38, "lon": 107.88},
            {"code": "KV08", "name": "Phước Chánh", "lat": 15.29, "lon": 107.90},
            {"code": "KV09", "name": "Phước Công", "lat": 15.29, "lon": 107.84},
            {"code": "KV10", "name": "Phước Năng", "lat": 15.40, "lon": 108.00},
            {"code": "KV11", "name": "Phước Xuân", "lat": 15.43, "lon": 107.92},
            {"code": "KV12", "name": "Phước Đức", "lat": 15.34, "lon": 108.12},
        ])
        events_df = base["events"].copy().sort_values("date", ascending=False).reset_index(drop=True)
        if "source" not in events_df.columns:
            events_df["source"] = "Historical_Catalog"

    if "damage" not in events_df.columns:
        events_df["damage"] = 100

    events_df = assign_commune_info(events_df, areas_df)
    events_df["year"] = pd.to_datetime(events_df["date"], errors="coerce").dt.year.fillna(2020).astype(int)
    return events_df, areas_df


df_events, df_areas = load_data_with_locations()

if df_events.empty:
    st.warning("Chưa có dữ liệu sự kiện sạt lở lịch sử.")
    st.stop()


# -------------------------------------------------------------
# 1. HEADER & TOP NAVIGATION (ĐỒNG BỘ 3 TRANG)
# -------------------------------------------------------------
col_hdr1, col_hdr2 = st.columns([2.6, 2.2], vertical_alignment="center")
with col_hdr1:
    st.markdown(
        '<div class="brand-box"><b>📜 HỒ SƠ LỊCH SỬ SẠT LỞ ĐẤT</b>'
        f'<span>Nam Trà My và Phước Sơn, Quảng Nam · Cơ sở dữ liệu {len(df_events)} sự kiện đã định danh địa điểm</span></div>',
        unsafe_allow_html=True,
    )
with col_hdr2:
    nb1, nb2, nb3 = st.columns([1.1, 1.25, 1.15], gap="small")
    with nb1:
        if st.button("⛰️ Giám sát 3D", key="nav_back_main", width="stretch"):
            _safe_switch_page("app/main.py")
    with nb2:
        st.button("📜 Lịch sử sạt lở", key="nav_hist_active", type="primary", width="stretch")
    with nb3:
        if st.button("🧠 Đánh giá AI", key="nav_to_ai", width="stretch"):
            _safe_switch_page("app/pages/2_AI_Evaluation.py")


# -------------------------------------------------------------
# 2. KPI METRIC CARDS (TẬP TRUNG ĐỊA ĐIỂM, NGUYÊN NHÂN & THIỆT HẠI)
# -------------------------------------------------------------
total_count = len(df_events)
cause_counts = df_events["cause"].value_counts()
top_cause_1 = cause_counts.index[0]
top_cnt_1 = int(cause_counts.iloc[0])

commune_counts = df_events["commune"].value_counts()
top_commune = commune_counts.index[0]
top_commune_cnt = int(commune_counts.iloc[0])

ntm_cnt = int((df_events["district"] == "Nam Trà My").sum())
ps_cnt = int((df_events["district"] == "Phước Sơn").sum())
total_damage_bil = float(df_events["damage"].sum()) / 1000.0

st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#d4e88a"></i>Tổng số sự kiện</div>
            <div class="kpi-num">{total_count} <span class="kpi-unit">vụ</span></div>
            <div class="kpi-sub">Nam Trà My: <b>{ntm_cnt} vụ</b> · Phước Sơn: <b>{ps_cnt} vụ</b></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#38bdf8"></i>Nguyên nhân hàng đầu</div>
            <div class="kpi-num" style="font-size:1.38rem;font-weight:400;margin-top:10px">{top_cause_1}</div>
            <div class="kpi-sub">{top_cnt_1} sự kiện (chiếm {top_cnt_1/total_count*100:.1f}%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#ff5a52"></i>Điểm nóng sạt lở nhất</div>
            <div class="kpi-num" style="font-size:1.38rem;font-weight:400;margin-top:10px">{top_commune}</div>
            <div class="kpi-sub">{top_commune_cnt} sự kiện ghi nhận tại địa bàn</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#f5b942"></i>Tổng thiệt hại ước tính (mô phỏng)</div>
            <div class="kpi-num">{total_damage_bil:.2f} <span class="kpi-unit">tỷ VNĐ</span></div>
            <div class="kpi-sub">Trung bình {df_events["damage"].mean():.0f} triệu VNĐ / sự kiện</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -------------------------------------------------------------
# 3. BỘ LỌC TẬP TRUNG THEO ĐỊA PHƯƠNG, NGUYÊN NHÂN & NĂM
# -------------------------------------------------------------
with st.container(key="glass_filter"):
    st.markdown(
        '<div class="panel-head">'
        "<span>🔍 Bộ lọc theo Địa bàn, Nguyên nhân & Thời gian</span>"
        "<small>Tra cứu nhanh địa điểm xảy ra sạt lở</small>"
        "</div>",
        unsafe_allow_html=True,
    )
    col_f1, col_f2, col_f3, col_f4 = st.columns([1.4, 1.6, 1.1, 1.8], gap="small")

    with col_f1:
        all_causes = ["Tất cả nguyên nhân"] + list(df_events["cause"].unique())
        selected_cause = st.selectbox("Nguyên nhân kích hoạt", all_causes, key="f_cause")

    with col_f2:
        all_places = [
            "Tất cả địa bàn",
            f"Huyện Nam Trà My ({ntm_cnt} vụ)",
            f"Huyện Phước Sơn ({ps_cnt} vụ)",
        ] + [f"{c} ({v} vụ)" for c, v in commune_counts.items()]
        selected_place = st.selectbox("Địa điểm / Xã", all_places, key="f_place")

    with col_f3:
        years_sorted = sorted(df_events["year"].unique().tolist(), reverse=True)
        selected_year = st.selectbox("Năm xảy ra", ["Tất cả các năm"] + [str(y) for y in years_sorted], key="f_year")

    with col_f4:
        search_text = st.text_input(
            "Tìm kiếm tự do",
            placeholder="Nhập tên xã, huyện, mã MP-..., ngày xảy ra...",
            key="f_search",
        )

# Xử lý lọc dữ liệu
filtered_df = df_events.copy()

if selected_cause != "Tất cả nguyên nhân":
    filtered_df = filtered_df[filtered_df["cause"] == selected_cause]

if selected_place != "Tất cả địa bàn":
    if selected_place.startswith("Huyện Nam Trà My"):
        filtered_df = filtered_df[filtered_df["district"] == "Nam Trà My"]
    elif selected_place.startswith("Huyện Phước Sơn"):
        filtered_df = filtered_df[filtered_df["district"] == "Phước Sơn"]
    else:
        commune_name = selected_place.split(" (")[0]
        filtered_df = filtered_df[filtered_df["commune"] == commune_name]

if selected_year != "Tất cả các năm":
    filtered_df = filtered_df[filtered_df["year"] == int(selected_year)]

if search_text:
    q = search_text.strip().lower()
    mask = (
        filtered_df["id"].str.lower().str.contains(q)
        | filtered_df["location"].str.lower().str.contains(q)
        | filtered_df["commune"].str.lower().str.contains(q)
        | filtered_df["district"].str.lower().str.contains(q)
        | filtered_df["cause"].str.lower().str.contains(q)
        | filtered_df["date"].str.contains(q)
    )
    filtered_df = filtered_df[mask]


# -------------------------------------------------------------
# 4. BẢN ĐỒ GIS VÀ BIỂU ĐỒ NGUYÊN NHÂN / ĐỊA ĐIỂM
# -------------------------------------------------------------
def build_map(df_plot: pd.DataFrame, areas_df: pd.DataFrame) -> go.Figure:
    """Tạo bản đồ GIS hiển thị rõ nhãn xã/khu vực và điểm sạt lở theo nguyên nhân."""
    is_plotly_7 = hasattr(go, "Scattermap")
    ScatterTrace = getattr(go, "Scattermap", getattr(go, "Scattermapbox", None))
    map_key = "map" if is_plotly_7 else "mapbox"

    fig = go.Figure()

    # 1. Thêm nhãn tên các xã / khu vực để người dùng nhìn rõ vị trí địa lý
    fig.add_trace(
        ScatterTrace(
            lat=areas_df["lat"],
            lon=areas_df["lon"],
            mode="markers+text",
            marker=dict(size=7, color="#ffffff", opacity=0.7),
            text=areas_df["name"],
            textposition="top center",
            textfont=dict(size=12, color="#ffffff", family="Be Vietnam Pro, sans-serif"),
            name="Địa bàn xã (12 xã)",
            hoverinfo="text",
            hovertext=["Xã " + n for n in areas_df["name"]],
        )
    )

    # 2. Thêm các điểm sạt lở phân màu theo Nguyên nhân
    for cause, col in CAUSE_COLORS.items():
        sub = df_plot[df_plot["cause"] == cause]
        if sub.empty:
            continue
        customdata = np.stack(
            [
                sub["id"],
                sub["location"],
                sub["cause"],
                sub["date"],
                sub["elev"].astype(int).astype(str),
                sub["lat"].map(lambda x: f"{x:.4f}"),
                sub["lon"].map(lambda x: f"{x:.4f}"),
                sub["damage"].astype(int).astype(str),
            ],
            axis=-1,
        )

        fig.add_trace(
            ScatterTrace(
                lat=sub["lat"],
                lon=sub["lon"],
                mode="markers",
                marker=dict(size=13, color=col, opacity=0.92),
                name=f"{cause} ({len(sub)})",
                customdata=customdata,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "📍 <b>Địa điểm:</b> %{customdata[1]}<br>"
                    "⚠️ <b>Nguyên nhân:</b> %{customdata[2]}<br>"
                    "📅 <b>Thời gian:</b> %{customdata[3]}<br>"
                    "⛰️ <b>Độ cao:</b> %{customdata[4]} m<br>"
                    "💰 <b>Thiệt hại ước tính:</b> %{customdata[7]} triệu VNĐ<br>"
                    "🌐 <b>Tọa độ:</b> %{customdata[5]}°B, %{customdata[6]}°Đ<extra></extra>"
                ),
            )
        )

    center_lat = float(df_plot["lat"].mean()) if not df_plot.empty else float(areas_df["lat"].mean())
    center_lon = float(df_plot["lon"].mean()) if not df_plot.empty else float(areas_df["lon"].mean())

    map_cfg = dict(
        style="carto-darkmatter",
        center=dict(lat=center_lat, lon=center_lon),
        zoom=9.35,
    )

    layout_dict = {
        map_key: map_cfg,
        "margin": dict(r=0, t=0, b=0, l=0),
        "height": 520,
        "paper_bgcolor": "#0c0e12",
        "plot_bgcolor": "#0c0e12",
        "font": dict(color="#e2e8f0", family="Be Vietnam Pro, sans-serif"),
        "legend": dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(20, 22, 26, 0.85)",
            bordercolor="rgba(255, 255, 255, 0.12)",
            borderwidth=1,
            font=dict(size=11),
        ),
    }
    fig.update_layout(**layout_dict)
    return fig


tab_map, tab_chart = st.tabs([
    "🗺️ Bản đồ GIS Xác định Vị trí & Nguyên nhân",
    "📊 Phân bố Thống kê theo Địa phương, Nguyên nhân & Thời gian",
])

with tab_map:
    with st.container(key="glass_map"):
        if filtered_df.empty:
            st.info("Không tìm thấy điểm sạt lở nào phù hợp với bộ lọc hiện tại.")
        else:
            fig_map = build_map(filtered_df, df_areas)
            st.plotly_chart(fig_map, width="stretch", config={"displayModeBar": True, "scrollZoom": True})
            st.markdown(
                f'<div class="map-note">'
                f'<span>📍 Đang hiển thị <b>{len(filtered_df)}</b> / {len(df_events)} điểm sạt lở kèm tên 12 Xã định vị</span>'
                "<span>💡 Di chuột lên từng điểm để xem chi tiết Địa bàn, Nguyên nhân và Thiệt hại</span></div>",
                unsafe_allow_html=True,
            )

with tab_chart:
    chart_source_df = filtered_df if not filtered_df.empty else df_events
    filter_badge = f"Đang lọc: {len(chart_source_df)}/{len(df_events)} vụ" if len(chart_source_df) != len(df_events) else f"Toàn bộ {len(df_events)} sự kiện"

    col_c1, col_c2 = st.columns(2, gap="medium")
    with col_c1:
        with st.container(key="glass_pie"):
            st.markdown(
                f'<div class="panel-head"><span>Cơ cấu Nguyên nhân Kích hoạt</span><small>{filter_badge}</small></div>',
                unsafe_allow_html=True,
            )
            fig_pie = px.pie(
                chart_source_df,
                names="cause",
                hole=0.52,
                color="cause",
                color_discrete_map=CAUSE_COLORS,
            )
            fig_pie.update_traces(
                textposition="inside",
                textinfo="percent+value",
                hovertemplate="<b>%{label}</b><br>Số sự kiện: %{value} vụ<br>Tỷ lệ: %{percent}<extra></extra>",
                marker=dict(line=dict(color="#0c0e12", width=2)),
            )
            fig_pie.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
                height=340,
            )
            st.plotly_chart(fig_pie, width="stretch")

    with col_c2:
        with st.container(key="glass_bar"):
            st.markdown(
                f'<div class="panel-head"><span>Số vụ sạt lở theo từng Xã / Khu vực</span><small>{filter_badge}</small></div>',
                unsafe_allow_html=True,
            )
            commune_plot_df = (
                chart_source_df.groupby(["commune", "district"])
                .size()
                .reset_index(name="count")
                .sort_values("count", ascending=True)
            )

            fig_bar = px.bar(
                commune_plot_df,
                x="count",
                y="commune",
                orientation="h",
                color="district",
                color_discrete_map={"Nam Trà My": "#d4e88a", "Phước Sơn": "#38bdf8"},
                labels={"count": "Số vụ sạt lở", "commune": "Địa bàn xã", "district": "Huyện"},
                text="count",
            )
            fig_bar.update_traces(textposition="outside", cliponaxis=False)
            fig_bar.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
                height=340,
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False),
                legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_bar, width="stretch")

    with st.container(key="glass_yearly"):
        st.markdown(
            f'<div class="panel-head"><span>Diễn biến Số vụ Sạt lở & Thiệt hại Ước tính theo Năm</span><small>{filter_badge}</small></div>',
            unsafe_allow_html=True,
        )
        yearly_df = (
            chart_source_df.groupby("year")
            .agg(events_count=("id", "count"), total_damage=("damage", "sum"))
            .reset_index()
            .sort_values("year")
        )
        fig_year = go.Figure()
        fig_year.add_trace(
            go.Bar(
                x=yearly_df["year"].astype(str),
                y=yearly_df["events_count"],
                name="Số sự kiện (vụ)",
                marker_color="#38bdf8",
                text=yearly_df["events_count"],
                textposition="outside",
                hovertemplate="Năm %{x}: <b>%{y} vụ</b><extra></extra>",
            )
        )
        fig_year.add_trace(
            go.Scatter(
                x=yearly_df["year"].astype(str),
                y=yearly_df["total_damage"],
                name="Thiệt hại (triệu VNĐ)",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color="#d4e88a", width=3),
                marker=dict(size=8, color="#d4e88a"),
                hovertemplate="Năm %{x}: <b>%{y:,} triệu VNĐ</b><extra></extra>",
            )
        )
        fig_year.update_layout(
            height=290,
            margin=dict(t=15, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
            xaxis=dict(title="Năm ghi nhận", showgrid=False),
            yaxis=dict(title="Số sự kiện (vụ)", showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
            yaxis2=dict(title="Thiệt hại (triệu VNĐ)", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
        )
        st.plotly_chart(fig_year, width="stretch")


# -------------------------------------------------------------
# 5. CHI TIẾT BẢNG DỮ LIỆU ĐỊNH DANH ĐỊA BÀN & XUẤT CSV
# -------------------------------------------------------------
with st.container(key="glass_table"):
    st.markdown(
        f'<div class="panel-head"><span>📋 Danh mục Hồ sơ Sự kiện ({len(filtered_df)} / {len(df_events)} sự kiện)</span>'
        "<small>Hiển thị chi tiết Tên xã, Huyện, Nguyên nhân và Thiệt hại</small></div>",
        unsafe_allow_html=True,
    )

    display_df = filtered_df[
        ["id", "location", "commune", "district", "cause", "date", "elev", "damage", "lat", "lon"]
    ].rename(
        columns={
            "id": "Mã sự kiện",
            "location": "Địa điểm cụ thể",
            "commune": "Xã / Khu vực",
            "district": "Huyện",
            "cause": "Nguyên nhân kích hoạt",
            "date": "Ngày xảy ra",
            "elev": "Độ cao (m)",
            "damage": "Thiệt hại (triệu VNĐ)",
            "lat": "Vĩ độ (°B)",
            "lon": "Kinh độ (°Đ)",
        }
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        height=380,
        column_config={
            "Mã sự kiện": st.column_config.TextColumn(width="small"),
            "Địa điểm cụ thể": st.column_config.TextColumn(width="medium"),
            "Xã / Khu vực": st.column_config.TextColumn(width="small"),
            "Huyện": st.column_config.TextColumn(width="small"),
            "Nguyên nhân kích hoạt": st.column_config.TextColumn(width="medium"),
            "Ngày xảy ra": st.column_config.TextColumn(width="small"),
            "Độ cao (m)": st.column_config.NumberColumn(format="%d m"),
            "Thiệt hại (triệu VNĐ)": st.column_config.NumberColumn(format="%d tr"),
            "Vĩ độ (°B)": st.column_config.NumberColumn(format="%.4f"),
            "Kinh độ (°Đ)": st.column_config.NumberColumn(format="%.4f"),
        },
    )

    dl_col1, dl_col2 = st.columns([3, 1.2])
    with dl_col2:
        csv_bytes = display_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 Xuất danh sách CSV",
            data=csv_bytes,
            file_name="ho_so_lich_su_sat_lo.csv",
            mime="text/csv",
            width="stretch",
        )


# -------------------------------------------------------------
# 6. EXPANDER: VAI TRÒ DỮ LIỆU ĐỊA ĐIỂM & NGUYÊN NHÂN
# -------------------------------------------------------------
with st.expander("ℹ️ Ý nghĩa của Dữ liệu Địa điểm & Nguyên nhân đối với Giám sát Cảnh báo", expanded=False):
    st.markdown(
        f"""
        - **Định danh địa bàn:** Tọa độ của {len(df_events)} điểm sạt lở được đối chiếu trên 12 xã giám sát thuộc 2 huyện trọng điểm **Nam Trà My** ({ntm_cnt} vụ) và **Phước Sơn** ({ps_cnt} vụ), trong đó {df_events["commune"].nunique()} xã đã ghi nhận sự kiện lịch sử.
        - **Phân loại nguyên nhân:** 4 nhóm nguyên nhân chính (**Mưa lớn kéo dài**, **Suy yếu địa chất**, **Hoạt động nhân tạo**, **Bão hoặc áp thấp nhiệt đới**) giúp mô hình phân bổ trọng số cảnh báo theo từng kịch bản thời tiết và địa hình cụ thể.
        - **Hỗ trợ điều hành:** Giúp lực lượng phòng chống thiên tai xác định nhanh điểm nóng thuộc xã nào để lên phương án ứng phó, kiểm tra tuyến đường hoặc sơ tán kịp thời.
        """
    )
