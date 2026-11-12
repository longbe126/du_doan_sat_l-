"""
Trang Đánh giá Mô hình Học máy & Phòng thí nghiệm Dự báo Tương tác
Phong cách thiết kế: Dark Frosted Glass HUD đồng bộ toàn hệ thống (không icon hoạt hình, không đè chữ)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
for p in [str(ROOT), str(ROOT / "app")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core.data_engine import AREAS, COVER_TO_CLASS, build_base
from core.model_loader import load_model, AVAILABLE_MODELS
from src.simulation.rules import true_probability

REPORT_PATH = ROOT / "reports" / "evaluation.json"

if not st.session_state.get("_root_navigation", False):
    st.set_page_config(
        page_title="Đánh giá mô hình học máy",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


def _safe_switch_page(target: str):
    try:
        st.switch_page(target)
    except Exception:
        alt = target.replace("app/", "", 1) if target.startswith("app/") else f"app/{target}"
        st.switch_page(alt)


MODEL_VI = {
    "logistic_regression": "Hồi quy Logistic",
    "random_forest": "Rừng ngẫu nhiên (RF)",
    "xgboost": "XGBoost",
}
MODEL_COLORS = {
    "logistic_regression": "#c8dc70",  # Xanh lime trầm
    "random_forest": "#88b3c8",        # Xanh xám đá trầm
    "xgboost": "#e5a93c",              # Vàng hổ phách trầm
}
FEATURE_VI = {
    "numeric__slope_deg": "Độ dốc địa hình (slope_deg)",
    "numeric__rainfall_mm": "Lượng mưa 24h (rainfall_mm)",
    "numeric__soil_moisture": "Độ ẩm đất (soil_moisture)",
    "numeric__elevation_m": "Độ cao địa hình (elevation_m)",
    "categorical__landcover_bare": "Lớp phủ: Đất trống (bare)",
    "categorical__landcover_forest": "Lớp phủ: Rừng tự nhiên/trồng (forest)",
    "categorical__landcover_agriculture": "Lớp phủ: Đất nông nghiệp (agriculture)",
    "categorical__landcover_urban": "Lớp phủ: Khu dân cư (urban)",
}

CSS_AI = """
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@200;300;400;500;600&display=swap');

html, body, .stApp {
    font-family: 'Be Vietnam Pro', system-ui, -apple-system, sans-serif !important;
    background: radial-gradient(ellipse 80% 42% at 50% 112%, rgba(136, 179, 200, 0.08), transparent 72%), #08090c !important;
    color: #eceef2 !important;
}

[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], footer {
    display: none !important;
}

.block-container {
    max-width: 1420px !important;
    padding: 22px 32px 52px 32px !important;
    margin: 0 auto !important;
}

.brand-box b {
    font-size: 1.15rem;
    font-weight: 500;
    color: #f4f5f7;
    display: block;
    letter-spacing: -0.01em;
}
.brand-box span {
    font-size: 0.78rem;
    color: rgba(236, 238, 242, 0.48);
    display: block;
    margin-top: 3px;
    font-weight: 300;
}

.stButton button {
    background: rgba(22, 24, 29, 0.72) !important;
    backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    border-radius: 999px !important;
    color: rgba(236, 238, 242, 0.82) !important;
    font-weight: 400 !important;
    padding: 6px 16px !important;
    height: 36px !important;
    min-height: 36px !important;
    font-size: 0.78rem !important;
    white-space: nowrap !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
}
.stButton button:hover {
    background: rgba(38, 42, 50, 0.88) !important;
    border-color: rgba(255, 255, 255, 0.22) !important;
    color: #ffffff !important;
}
.stButton button[data-testid="stBaseButton-primary"], .stButton button[kind="primary"] {
    background: rgba(200, 220, 112, 0.18) !important;
    color: #d8ea86 !important;
    border: 1px solid rgba(200, 220, 112, 0.45) !important;
    font-weight: 500 !important;
    cursor: default !important;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 18px 0 22px 0;
}
.kpi-card {
    background: linear-gradient(155deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.015) 100%), rgba(20, 22, 27, 0.62);
    backdrop-filter: blur(26px) saturate(140%);
    -webkit-backdrop-filter: blur(26px) saturate(140%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.09), 0 14px 34px rgba(0, 0, 0, 0.38);
    border-radius: 22px;
    padding: 16px 20px;
}
.kpi-head {
    font-size: 0.78rem;
    color: rgba(236, 238, 242, 0.78);
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 400;
}
.kpi-head i {
    width: 2.5px;
    height: 12px;
    border-radius: 2px;
    display: inline-block;
}
.kpi-num {
    font-size: 2.0rem;
    font-weight: 200;
    color: #f5f6f8;
    line-height: 1.15;
    margin: 8px 0 4px 0;
    letter-spacing: -0.02em;
    font-variant-numeric: tabular-nums;
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}
.kpi-unit {
    font-size: 0.78rem;
    color: rgba(236, 238, 242, 0.42);
    font-weight: 300;
    margin-left: 4px;
}
.kpi-arr {
    font-size: 0.85rem;
    color: rgba(236, 238, 242, 0.48);
    font-weight: 300;
}
.kpi-sub {
    font-size: 0.7rem;
    color: rgba(236, 238, 242, 0.45);
    margin-top: 4px;
}

[class*="st-key-glass_"] {
    background: linear-gradient(155deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.012) 100%), rgba(20, 22, 27, 0.62) !important;
    backdrop-filter: blur(26px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(26px) saturate(140%) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 22px !important;
    padding: 18px 22px !important;
    margin-bottom: 18px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 14px 34px rgba(0, 0, 0, 0.38) !important;
}
.panel-head {
    font-size: 0.88rem;
    font-weight: 400;
    color: #eceef2;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.panel-head small {
    font-size: 0.72rem;
    color: rgba(236, 238, 242, 0.45);
    font-weight: 300;
}

div[data-baseweb="select"] > div {
    background: rgba(16, 18, 23, 0.75) !important;
    border: 1px solid rgba(255, 255, 255, 0.09) !important;
    border-radius: 14px !important;
    color: #eceef2 !important;
    font-size: 0.82rem !important;
}
label p {
    font-size: 0.75rem !important;
    color: rgba(236, 238, 242, 0.52) !important;
    margin-bottom: 4px !important;
    font-weight: 300 !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: rgba(20, 22, 27, 0.68) !important;
    border-radius: 999px !important;
    padding: 4px !important;
    gap: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    width: fit-content !important;
    margin-bottom: 16px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 999px !important;
    padding: 6px 18px !important;
    color: rgba(236, 238, 242, 0.62) !important;
    font-size: 0.78rem !important;
    border: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(200, 220, 112, 0.18) !important;
    color: #d8ea86 !important;
    border: 1px solid rgba(200, 220, 112, 0.42) !important;
    font-weight: 500 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}
"""
st.markdown(f"<style>{CSS_AI}</style>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. HEADER & TOP NAVIGATION
# -------------------------------------------------------------
col_hdr1, col_hdr2 = st.columns([2.6, 2.0], vertical_alignment="center")
with col_hdr1:
    st.markdown(
        '<div class="brand-box"><b>Đánh giá mô hình học máy và thử nghiệm kịch bản</b>'
        "<span>Đối chiếu Hồi quy Logistic, Rừng ngẫu nhiên và XGBoost · Kiểm định độc lập và hiệu chuẩn xác suất</span></div>",
        unsafe_allow_html=True,
    )
with col_hdr2:
    n1, n2, n3 = st.columns([1.1, 1.15, 1.25], gap="small")
    with n1:
        if st.button("Giám sát 3D", key="nav_overview", width="stretch"):
            _safe_switch_page("app/main.py")
    with n2:
        if st.button("Hồ sơ lịch sử", key="nav_hist", width="stretch"):
            _safe_switch_page("app/pages/3_Lich_Su_Sat_Lo.py")
    with n3:
        st.button("Đánh giá mô hình", key="nav_ai", type="primary", width="stretch")

if not REPORT_PATH.exists():
    try:
        from core import train_models
        train_models.main()
    except Exception as exc:
        st.error(f"Không thể chạy pipeline huấn luyện tự động: {exc}")
        st.stop()

with open(REPORT_PATH, "r", encoding="utf-8") as f:
    report = json.load(f)

# -------------------------------------------------------------
# 2. KPI METRIC CARDS (Phong cách HbA1c / Testosterone {40DBE37A})
# -------------------------------------------------------------
best_model = report.get("best_model", "logistic_regression")
best_vi = MODEL_VI.get(best_model, best_model)
best_cv_auc = report.get("cross_validation", {}).get(best_model, {}).get("roc_auc_mean", 0.0)
best_test_auc = report.get("metrics", {}).get(best_model, {}).get("roc_auc", 0.0)
ceiling = float((report.get("reference") or {}).get("ceiling_roc_auc", 0.806))
pos_rate = float(report.get("positive_rate", 0.5)) * 100.0
ceil_int, ceil_dec = f"{ceiling:.3f}".split(".")

st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#c8dc70"></i>Mô hình hiệu quả nhất (CV)</div>
            <div class="kpi-num" style="font-size:1.36rem;font-weight:300;margin-top:11px"><span>{best_vi}</span><span class="kpi-arr">↗</span></div>
            <div class="kpi-sub">ROC-AUC CV: {best_cv_auc:.3f} · Tập kiểm tra: {best_test_auc:.3f}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#88b3c8"></i>Quy mô tập dữ liệu</div>
            <div class="kpi-num"><span>{report['n_rows']:,}<span class="kpi-unit">mẫu</span></span><span class="kpi-arr">→</span></div>
            <div class="kpi-sub">Huấn luyện: {report['train_rows']:,} (80%) · Kiểm tra: {report['test_rows']:,} (20%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#e5a93c"></i>Trần lý thuyết (Oracle AUC)</div>
            <div class="kpi-num"><span>{ceil_int}<span style="color:rgba(236,238,242,0.42)">,{ceil_dec}</span><span class="kpi-unit">AUC</span></span><span class="kpi-arr">→</span></div>
            <div class="kpi-sub">Độ lệch chuẩn nhiễu sinh nhãn σ = {(report.get('reference') or {}).get('noise_sd', 0.8)}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#4cc38a"></i>Cấu trúc đặc trưng</div>
            <div class="kpi-num"><span>{report['n_features']}<span class="kpi-unit">biến đầu vào</span></span><span class="kpi-arr">→</span></div>
            <div class="kpi-sub">Tỷ lệ nhãn dương: {pos_rate:.1f}% · Nguồn: {', '.join(report.get('dataset_source', ['SIMULATED']))}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# 3. CÁC TAB PHÂN TÍCH CHUYÊN SÂU
# -------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Bảng điểm và kiểm định chéo",
    "Đường cong ROC, PR và hiệu chuẩn",
    "Ma trận nhầm lẫn và đặc trưng",
    "Thử nghiệm dự báo tương tác (What-If)",
])

with tab1:
    c_left, c_right = st.columns([1.45, 1.0], gap="medium")
    with c_left:
        with st.container(key="glass_metrics_chart"):
            st.markdown(
                '<div class="panel-head"><span>So sánh đa chỉ số trên tập kiểm tra độc lập (20% Test)</span>'
                "<small>Di chuột lên cột để xem giá trị chính xác</small></div>",
                unsafe_allow_html=True,
            )
            fig_m = go.Figure()
            metric_cols = ["roc_auc", "pr_auc", "f1", "accuracy", "precision", "recall", "brier"]
            metric_labels = ["ROC-AUC", "PR-AUC", "F1-Score", "Accuracy", "Precision", "Recall", "Brier (Sai số)"]
            for raw_name, m_vals in report["metrics"].items():
                # Không hiển thị text chồng chéo trên đỉnh 21 cột; dùng khoảng cách thoáng và tooltip rõ nét
                fig_m.add_trace(
                    go.Bar(
                        name=MODEL_VI.get(raw_name, raw_name),
                        x=metric_labels,
                        y=[float(m_vals.get(k, 0.0)) for k in metric_cols],
                        marker_color=MODEL_COLORS.get(raw_name, "#c8dc70"),
                        marker_opacity=0.88,
                        marker_line_width=0,
                        hovertemplate="<b>%{fullData.name}</b><br>%{x}: <b>%{y:.4f}</b><extra></extra>",
                    )
                )
            fig_m.update_layout(
                barmode="group",
                bargap=0.30,
                bargroupgap=0.14,
                height=350,
                margin=dict(t=16, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#eceef2", family="Be Vietnam Pro, sans-serif"),
                yaxis=dict(range=[0, 1.0], showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False),
                xaxis=dict(showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
            )
            st.plotly_chart(fig_m, width="stretch", config={"displayModeBar": False})

    with c_right:
        with st.container(key="glass_dist_chart"):
            st.markdown(
                '<div class="panel-head"><span>Phân bố nhãn trong bộ dữ liệu</span>'
                f"<small>Tổng cộng {report['n_rows']:,} mẫu</small></div>",
                unsafe_allow_html=True,
            )
            target_dist = report.get("target_distribution", {})
            labels_pie = [
                "Không sạt lở (0)" if k == "0" else ("Sạt lở (1)" if k == "1" else f"Nhãn {k}")
                for k in target_dist.keys()
            ]
            values_pie = [int(v) for v in target_dist.values()]
            fig_dist = go.Figure(
                go.Pie(
                    labels=labels_pie,
                    values=values_pie,
                    hole=0.62,
                    marker=dict(
                        colors=["rgba(232, 93, 86, 0.78)", "rgba(76, 195, 138, 0.78)"],
                        line=dict(color="#121419", width=2),
                    ),
                    textinfo="percent",
                    textfont=dict(size=13, color="#eceef2"),
                    hovertemplate="<b>%{label}</b><br>Số lượng: %{value:,} mẫu (%{percent})<extra></extra>",
                )
            )
            fig_dist.update_layout(
                height=350,
                margin=dict(t=16, b=24, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#eceef2", family="Be Vietnam Pro, sans-serif"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_dist, width="stretch", config={"displayModeBar": False})

    with st.container(key="glass_cv_table"):
        validation = report.get("validation", {})
        st.markdown(
            '<div class="panel-head"><span>Bảng tổng hợp chỉ số kiểm tra (20% Holdout) và kiểm định chéo 5-Fold (80% Train)</span>'
            f"<small>{validation.get('cross_validation', 'StratifiedKFold 5 phần')}</small></div>",
            unsafe_allow_html=True,
        )
        cv_report = report.get("cross_validation", {})
        combined_rows = []
        for raw_name, m_vals in report["metrics"].items():
            cv_v = cv_report.get(raw_name, {})
            combined_rows.append({
                "Mô hình": MODEL_VI.get(raw_name, raw_name),
                "CV ROC-AUC (TB ± SD)": f"{cv_v.get('roc_auc_mean', 0):.3f} ± {cv_v.get('roc_auc_std', 0):.3f}",
                "CV PR-AUC (TB ± SD)": f"{cv_v.get('average_precision_mean', 0):.3f} ± {cv_v.get('average_precision_std', 0):.3f}",
                "Test ROC-AUC": round(float(m_vals.get("roc_auc", 0)), 4),
                "Test PR-AUC": round(float(m_vals.get("pr_auc", 0)), 4),
                "F1-Score": round(float(m_vals.get("f1", 0)), 4),
                "Precision": round(float(m_vals.get("precision", 0)), 4),
                "Recall": round(float(m_vals.get("recall", 0)), 4),
                "Accuracy": round(float(m_vals.get("accuracy", 0)), 4),
                "Brier Score (↓)": round(float(m_vals.get("brier", 0)), 4),
            })
        st.dataframe(pd.DataFrame(combined_rows), width="stretch", hide_index=True)
        st.caption(
            f"Ghi chú chuyên môn: Nhãn của bộ dữ liệu mô phỏng được sinh từ hàm tuyến tính logit cộng nhiễu Gaussian (σ = 0.8), "
            f"nên trần lý thuyết (Oracle ROC-AUC) đạt {ceiling:.3f}. Hồi quy Logistic khớp đúng cấu trúc hàm sinh dữ liệu nên tiệm cận trần lý thuyết."
        )

with tab2:
    col_roc, col_pr = st.columns(2, gap="medium")
    with col_roc:
        with st.container(key="glass_roc"):
            st.markdown(
                '<div class="panel-head"><span>Đường cong ROC (Receiver Operating Characteristic)</span>'
                "<small>Khả năng phân tách hai lớp</small></div>",
                unsafe_allow_html=True,
            )
            roc_data = report.get("roc_curves", {})
            fig_roc = go.Figure()
            for raw_name, curve in roc_data.items():
                auc_val = report["metrics"][raw_name].get("roc_auc")
                lbl = f"{MODEL_VI.get(raw_name, raw_name)} ({auc_val:.3f})" if auc_val else MODEL_VI.get(raw_name, raw_name)
                fig_roc.add_trace(
                    go.Scatter(
                        x=curve["fpr"],
                        y=curve["tpr"],
                        mode="lines",
                        line=dict(width=2.2, color=MODEL_COLORS.get(raw_name, "#c8dc70")),
                        name=lbl,
                    )
                )
            fig_roc.add_trace(
                go.Scatter(
                    x=[0, 1],
                    y=[0, 1],
                    mode="lines",
                    line=dict(dash="dot", color="rgba(255,255,255,0.28)"),
                    name="Tham chiếu (0.500)",
                )
            )
            fig_roc.update_layout(
                xaxis_title="Tỷ lệ báo động giả (FPR)",
                yaxis_title="Tỷ lệ phát hiện đúng (TPR)",
                xaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.05)"),
                height=380,
                margin=dict(t=15, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#eceef2", family="Be Vietnam Pro, sans-serif"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.26, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_roc, width="stretch", config={"displayModeBar": False})

    with col_pr:
        with st.container(key="glass_pr"):
            st.markdown(
                '<div class="panel-head"><span>Đường cong Precision – Recall (PR Curve)</span>'
                "<small>Đánh giá độ chính xác dương theo độ nhạy</small></div>",
                unsafe_allow_html=True,
            )
            pr_data = report.get("pr_curves", {})
            fig_pr = go.Figure()
            for raw_name, curve in pr_data.items():
                pr_auc = report["metrics"][raw_name].get("pr_auc")
                lbl = f"{MODEL_VI.get(raw_name, raw_name)} ({pr_auc:.3f})" if pr_auc else MODEL_VI.get(raw_name, raw_name)
                fig_pr.add_trace(
                    go.Scatter(
                        x=curve["recall"],
                        y=curve["precision"],
                        mode="lines",
                        line=dict(width=2.2, color=MODEL_COLORS.get(raw_name, "#88b3c8")),
                        name=lbl,
                    )
                )
            base_pos = float(report.get("positive_rate", 0.5))
            fig_pr.add_trace(
                go.Scatter(
                    x=[0, 1],
                    y=[base_pos, base_pos],
                    mode="lines",
                    line=dict(dash="dot", color="rgba(255,255,255,0.28)"),
                    name=f"Tỷ lệ nền ({base_pos:.2f})",
                )
            )
            fig_pr.update_layout(
                xaxis_title="Độ nhạy (Recall)",
                yaxis_title="Độ chính xác dương (Precision)",
                xaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(range=[0, 1.02], gridcolor="rgba(255,255,255,0.05)"),
                height=380,
                margin=dict(t=15, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#eceef2", family="Be Vietnam Pro, sans-serif"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.26, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_pr, width="stretch", config={"displayModeBar": False})

    with st.container(key="glass_cal"):
        st.markdown(
            '<div class="panel-head"><span>Đường hiệu chuẩn xác suất (Calibration Curve)</span>'
            "<small>Đối chiếu xác suất dự đoán với tần suất thực tế</small></div>",
            unsafe_allow_html=True,
        )
        calibration = report.get("calibration_curves", {})
        cal_fig = go.Figure()
        for raw_name, curve in calibration.items():
            brier_v = report["metrics"][raw_name].get("brier", 0.0)
            cal_fig.add_trace(
                go.Scatter(
                    x=curve["mean_predicted"],
                    y=curve["fraction_positive"],
                    mode="lines+markers",
                    marker=dict(size=7),
                    line=dict(width=2.2, color=MODEL_COLORS.get(raw_name, "#c8dc70")),
                    name=f"{MODEL_VI.get(raw_name, raw_name)} (Brier = {brier_v:.3f})",
                )
            )
        cal_fig.add_trace(
            go.Scatter(
                x=[0, 1],
                y=[0, 1],
                mode="lines",
                line=dict(dash="dot", color="rgba(255,255,255,0.35)"),
                name="Hiệu chuẩn lý tưởng (y = x)",
            )
        )
        cal_fig.update_layout(
            xaxis_title="Xác suất dự đoán trung bình trong từng nhóm phân vị",
            yaxis_title="Tỷ lệ sạt lở thực tế trong nhóm",
            xaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.05)"),
            height=340,
            margin=dict(t=15, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eceef2", family="Be Vietnam Pro, sans-serif"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
        )
        st.plotly_chart(cal_fig, width="stretch", config={"displayModeBar": False})

with tab3:
    col_cm, col_fi = st.columns([1.05, 1.35], gap="medium")
    with col_cm:
        with st.container(key="glass_cm"):
            st.markdown(
                '<div class="panel-head"><span>Ma trận nhầm lẫn (Confusion Matrix)</span>'
                "<small>Trên 1.000 mẫu kiểm tra độc lập</small></div>",
                unsafe_allow_html=True,
            )
            matrix_models = report.get("confusion_matrices", {})
            selected_cm_model = st.selectbox(
                "Mô hình hiển thị ma trận nhầm lẫn",
                list(matrix_models.keys()),
                format_func=lambda k: MODEL_VI.get(k, k),
                key="sel_cm_model",
            )
            cm = np.asarray(matrix_models[selected_cm_model], dtype=int)
            tot_cm = max(int(cm.sum()), 1)
            tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

            annot_text = [
                [
                    f"<b>TN: {tn}</b><br>({tn / tot_cm * 100:.1f}%)",
                    f"<b>FP: {fp}</b><br>({fp / tot_cm * 100:.1f}%)",
                ],
                [
                    f"<b>FN: {fn}</b><br>({fn / tot_cm * 100:.1f}%)",
                    f"<b>TP: {tp}</b><br>({tp / tot_cm * 100:.1f}%)",
                ],
            ]
            fig_cm = go.Figure(
                data=go.Heatmap(
                    z=cm[::-1],
                    x=["Dự đoán: Không sạt lở (0)", "Dự đoán: Sạt lở (1)"],
                    y=["Thực tế: Sạt lở (1)", "Thực tế: Không sạt lở (0)"],
                    text=annot_text[::-1],
                    texttemplate="%{text}",
                    textfont={"size": 13, "color": "#eceef2"},
                    colorscale=[[0.0, "#161920"], [0.5, "#233642"], [1.0, "#3a5a4e"]],
                    showscale=False,
                )
            )
            fig_cm.update_layout(
                height=310,
                margin=dict(t=15, b=15, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#eceef2", family="Be Vietnam Pro, sans-serif"),
            )
            st.plotly_chart(fig_cm, width="stretch", config={"displayModeBar": False})
            st.caption(
                f"Phân tích sai số ({MODEL_VI.get(selected_cm_model, selected_cm_model)}): "
                f"Phát hiện đúng {tp} vụ sạt lở (TP), bỏ sót {fn} vụ (FN), báo động giả {fp} mẫu (FP)."
            )

    with col_fi:
        with st.container(key="glass_fi"):
            st.markdown(
                '<div class="panel-head"><span>Mức độ đóng góp đặc trưng và chiều tác động</span>'
                "<small>Hệ số mô hình sau chuẩn hóa</small></div>",
                unsafe_allow_html=True,
            )
            importance_data = report.get("feature_importance", {})
            selected_fi_model = st.selectbox(
                "Mô hình phân tích đặc trưng",
                list(importance_data.keys()),
                format_func=lambda k: MODEL_VI.get(k, k),
                key="sel_fi_model",
            )
            fi_rows = importance_data.get(selected_fi_model, [])[:12]
            fi_df = pd.DataFrame(fi_rows)
            if "signed_importance" not in fi_df.columns:
                fi_df["signed_importance"] = fi_df["importance"]
            fi_df["label"] = fi_df["feature"].map(lambda x: FEATURE_VI.get(x, x))
            fi_df = fi_df.sort_values("importance", ascending=True)

            is_lr = selected_fi_model == "logistic_regression"
            plot_vals = fi_df["signed_importance"] if is_lr else fi_df["importance"]
            bar_colors = [
                "rgba(76, 195, 138, 0.82)" if (is_lr and v < 0) else ("rgba(232, 93, 86, 0.82)" if is_lr else "rgba(200, 220, 112, 0.82)")
                for v in plot_vals
            ]

            fig_fi = go.Figure(
                go.Bar(
                    x=plot_vals,
                    y=fi_df["label"],
                    orientation="h",
                    marker_color=bar_colors,
                    marker_line_width=0,
                    text=[f"{v:+.3f}" if is_lr else f"{v:.3f}" for v in plot_vals],
                    textposition="outside",
                    cliponaxis=False,
                )
            )
            fig_fi.update_layout(
                height=310,
                margin=dict(t=15, b=15, l=10, r=48),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#eceef2", family="Be Vietnam Pro, sans-serif"),
                xaxis=dict(
                    title="Hệ số chuẩn hóa có dấu (+ làm tăng nguy cơ / - làm giảm nguy cơ)" if is_lr else "Tầm quan trọng tương đối (Importance)",
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.05)",
                    zeroline=True,
                    zerolinecolor="rgba(255,255,255,0.22)",
                ),
            )
            st.plotly_chart(fig_fi, width="stretch", config={"displayModeBar": False})
            if is_lr:
                st.caption(
                    "Hệ số dương (+): Làm tăng nguy cơ sạt lở (Độ dốc lớn, Mưa nhiều, Độ ẩm đất cao, Đất trống). "
                    "Hệ số âm (-): Làm giảm nguy cơ sạt lở (Lớp phủ Rừng)."
                )
            else:
                st.caption("Mô hình tổ hợp cây đánh giá mức độ đóng góp tương đối khi phân nhánh quyết định.")

with tab4:
    with st.container(key="glass_sandbox"):
        st.markdown(
            '<div class="panel-head"><span>Thử nghiệm dự báo tương tác (What-If Scenario)</span>'
            "<small>Điều chỉnh thông số địa hình – thủy văn và đối chiếu kết quả của 3 mô hình</small></div>",
            unsafe_allow_html=True,
        )
        preset_options = ["Tùy chỉnh tự do"] + [f"{name} ({code} · {cover})" for code, name, _, _, cover in AREAS]
        chosen_preset = st.selectbox("Chọn thông số nền từ 12 xã giám sát:", preset_options, key="sb_preset")

        base_data = build_base()
        default_slope, default_elev, default_rain, default_soil, default_cover = 28.0, 650.0, 140.0, 0.62, "Đất trống"
        if chosen_preset != "Tùy chỉnh tự do":
            idx_p = preset_options.index(chosen_preset) - 1
            _, p_name, p_lat, p_lon, p_cover = AREAS[idx_p]
            i_lat = int(np.abs(base_data["lat"] - p_lat).argmin())
            j_lon = int(np.abs(base_data["lon"] - p_lon).argmin())
            default_slope = float(np.round(base_data["slope"][i_lat, j_lon], 1))
            default_elev = float(np.round(base_data["elev"][i_lat, j_lon], 0))
            default_rain = float(np.round(base_data["rain"][i_lat, j_lon], 0))
            default_soil = float(np.round(base_data["soil"][i_lat, j_lon], 2))
            default_cover = p_cover

        sc1, sc2, sc3 = st.columns(3, gap="medium")
        with sc1:
            in_slope = st.slider("Độ dốc sườn (°)", 0.0, 65.0, value=default_slope, step=0.5)
            in_elev = st.slider("Độ cao địa hình (m)", 20.0, 2200.0, value=default_elev, step=10.0)
        with sc2:
            in_rain = st.slider("Lượng mưa 24 giờ (mm)", 0.0, 450.0, value=default_rain, step=5.0)
            in_soil = st.slider("Độ ẩm đất (0–1)", 0.05, 0.98, value=default_soil, step=0.01)
        with sc3:
            cover_display = ["Rừng tự nhiên", "Rừng trồng", "Đất nông nghiệp", "Đất trống", "Đô thị / Khu dân cư"]
            cover_map_ext = {**COVER_TO_CLASS, "Đô thị / Khu dân cư": "urban"}
            in_cover_vi = st.selectbox(
                "Lớp phủ bề mặt",
                cover_display,
                index=cover_display.index(default_cover) if default_cover in cover_display else 0,
            )
            in_cover_code = cover_map_ext[in_cover_vi]
            st.caption(f"Nhóm lớp phủ đưa vào mô hình: `{in_cover_code}`")

        sample_X = pd.DataFrame([{
            "slope_deg": in_slope,
            "elevation_m": in_elev,
            "rainfall_mm": in_rain,
            "soil_moisture": in_soil,
            "landcover": in_cover_code,
        }])

        oracle_prob = float(true_probability(in_slope, in_elev, in_rain, in_soil, in_cover_code))
        pred_cols = st.columns(4, gap="small")
        for idx_m, m_key in enumerate(AVAILABLE_MODELS):
            mdl_obj, _, _ = load_model(m_key)
            prob_val = float(mdl_obj.predict_proba(sample_X)[:, 1][0])
            lvl_str = "Cao" if prob_val >= 0.45 else ("Trung bình" if prob_val >= 0.25 else "Thấp")
            lvl_col = "#e85d56" if prob_val >= 0.45 else ("#e5a93c" if prob_val >= 0.25 else "#4cc38a")
            p_int, p_dec = f"{prob_val:.3f}".split(".")
            with pred_cols[idx_m]:
                st.markdown(
                    f'<div class="kpi-card" style="border-color:{lvl_col}33">'
                    f'<div class="kpi-head"><i style="background:{MODEL_COLORS[m_key]}"></i>{MODEL_VI[m_key]}</div>'
                    f'<div class="kpi-num"><span>{p_int}<span style="color:rgba(236,238,242,0.42)">,{p_dec}</span><span class="kpi-unit">/ 1</span></span><span class="kpi-arr">→</span></div>'
                    f'<div class="kpi-sub">Phân mức: <b style="color:{lvl_col};font-weight:400">{lvl_str}</b></div>'
                    "</div>",
                    unsafe_allow_html=True,
                )
        with pred_cols[3]:
            lvl_o = "Cao" if oracle_prob >= 0.45 else ("Trung bình" if oracle_prob >= 0.25 else "Thấp")
            col_o = "#e85d56" if oracle_prob >= 0.45 else ("#e5a93c" if oracle_prob >= 0.25 else "#4cc38a")
            o_int, o_dec = f"{oracle_prob:.3f}".split(".")
            st.markdown(
                '<div class="kpi-card">'
                '<div class="kpi-head"><i style="background:#eceef2"></i>Quy luật tham chiếu</div>'
                f'<div class="kpi-num"><span>{o_int}<span style="color:rgba(236,238,242,0.42)">,{o_dec}</span><span class="kpi-unit">/ 1</span></span><span class="kpi-arr">→</span></div>'
                f'<div class="kpi-sub">Mức kỳ vọng: <b style="color:{col_o};font-weight:400">{lvl_o}</b></div>'
                "</div>",
                unsafe_allow_html=True,
            )