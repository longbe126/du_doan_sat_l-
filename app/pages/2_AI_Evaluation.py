"""
Trang Đánh giá Mô hình Học máy & Phòng thí nghiệm Dự báo Tương tác (AI Evaluation & Sandbox)
Phong cách thiết kế: Dark Glassmorphic HUD Dashboard đồng bộ toàn hệ thống
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
        page_title="Đánh giá Mô hình AI",
        page_icon="🧠",
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
    "logistic_regression": "#d4e88a",
    "random_forest": "#38bdf8",
    "xgboost": "#f5b942",
}
FEATURE_VI = {
    "numeric__slope_deg": "Độ dốc địa hình (slope_deg)",
    "numeric__rainfall_mm": "Lượng mưa 24h (rainfall_mm)",
    "numeric__soil_moisture": "Độ ẩm đất (soil_moisture)",
    "numeric__elevation_m": "Độ cao địa hình (elevation_m)",
    "categorical__landcover_bare": "Lớp phủ: Đất trống (bare)",
    "categorical__landcover_forest": "Lớp phủ: Rừng (forest)",
    "categorical__landcover_agriculture": "Lớp phủ: Nông nghiệp (agriculture)",
    "categorical__landcover_urban": "Lớp phủ: Đô thị/Dân cư (urban)",
}

CSS_AI = """
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@200;300;400;500;600;700&display=swap');

html, body, .stApp {
    font-family: 'Be Vietnam Pro', system-ui, sans-serif !important;
    background: radial-gradient(ellipse 85% 42% at 50% 112%, rgba(56, 189, 248, 0.12), transparent 72%), #07080b !important;
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

.stButton button {
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
.stButton button:hover {
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
"""
st.markdown(f"<style>{CSS_AI}</style>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. HEADER & TOP NAVIGATION
# -------------------------------------------------------------
col_hdr1, col_hdr2 = st.columns([2.6, 2.2], vertical_alignment="center")
with col_hdr1:
    st.markdown(
        '<div class="brand-box"><b>🧠 ĐÁNH GIÁ MÔ HÌNH HỌC MÁY & THỬ NGHIỆM AI</b>'
        "<span>So sánh Logistic Regression, Random Forest và XGBoost · Kiểm định độc lập & Hiệu chuẩn xác suất</span></div>",
        unsafe_allow_html=True,
    )
with col_hdr2:
    n1, n2, n3 = st.columns([1.1, 1.25, 1.15], gap="small")
    with n1:
        if st.button("⛰️ Giám sát 3D", key="nav_overview", width="stretch"):
            _safe_switch_page("app/main.py")
    with n2:
        if st.button("📜 Lịch sử sạt lở", key="nav_hist", width="stretch"):
            _safe_switch_page("app/pages/3_Lich_Su_Sat_Lo.py")
    with n3:
        st.button("🧠 Đánh giá AI", key="nav_ai", type="primary", width="stretch")

if not REPORT_PATH.exists():
    st.warning("Chưa có báo cáo đánh giá. Đang tự động khởi tạo báo cáo từ pipeline huấn luyện...")
    try:
        from core import train_models
        train_models.main()
    except Exception as exc:
        st.error(f"Không thể chạy pipeline huấn luyện tự động: {exc}")
        st.stop()

with open(REPORT_PATH, "r", encoding="utf-8") as f:
    report = json.load(f)

# -------------------------------------------------------------
# 2. KPI METRIC CARDS
# -------------------------------------------------------------
best_model = report.get("best_model", "logistic_regression")
best_vi = MODEL_VI.get(best_model, best_model)
best_cv_auc = report.get("cross_validation", {}).get(best_model, {}).get("roc_auc_mean", 0.0)
best_test_auc = report.get("metrics", {}).get(best_model, {}).get("roc_auc", 0.0)
ceiling = (report.get("reference") or {}).get("ceiling_roc_auc", 0.806)
pos_rate = float(report.get("positive_rate", 0.5)) * 100.0

st.markdown(
    f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#d4e88a"></i>Mô hình tối ưu nhất (CV)</div>
            <div class="kpi-num" style="font-size:1.45rem;font-weight:500;margin-top:9px;color:#d4e88a">{best_vi}</div>
            <div class="kpi-sub">ROC-AUC CV: <b>{best_cv_auc:.3f}</b> · Test: <b>{best_test_auc:.3f}</b></div>
        </div>
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#38bdf8"></i>Quy mô Bộ dữ liệu</div>
            <div class="kpi-num">{report['n_rows']:,} <span class="kpi-unit">mẫu</span></div>
            <div class="kpi-sub">Train: <b>{report['train_rows']:,}</b> (80%) · Test độc lập: <b>{report['test_rows']:,}</b> (20%)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#f5b942"></i>Trần lý thuyết (Oracle AUC)</div>
            <div class="kpi-num">{ceiling:.3f} <span class="kpi-unit">ROC-AUC</span></div>
            <div class="kpi-sub">Nhiễu sinh nhãn σ = {(report.get('reference') or {}).get('noise_sd', 0.8)}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-head"><i style="background:#4ade80"></i>Đặc trưng & Tỷ lệ nhãn dương</div>
            <div class="kpi-num">{report['n_features']} <span class="kpi-unit">đặc trưng</span></div>
            <div class="kpi-sub">Tỷ lệ sạt lở: <b>{pos_rate:.1f}%</b> · Nguồn: {', '.join(report.get('dataset_source', ['SIMULATED']))}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# 3. CÁC TAB PHÂN TÍCH CHUYÊN SÂU & SANDBOX DỰ BÁO
# -------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Bảng điểm & Kiểm định chéo",
    "📈 Đường cong ROC, PR & Hiệu chuẩn",
    "🎯 Ma trận Nhầm lẫn & Đặc trưng Quan trọng",
    "🧪 Phòng thí nghiệm Dự báo Tương tác (What-If)",
])

metrics_df = pd.DataFrame(report["metrics"]).T
metrics_df.index = [MODEL_VI.get(idx, idx) for idx in metrics_df.index]

with tab1:
    c_left, c_right = st.columns([1.45, 1.0], gap="medium")
    with c_left:
        with st.container(key="glass_metrics_chart"):
            st.markdown(
                '<div class="panel-head"><span>So sánh Đa chỉ số trên Tập Kiểm tra Độc lập (20% Test)</span>'
                "<small>Điểm càng cao càng tốt (riêng Brier càng thấp càng tốt)</small></div>",
                unsafe_allow_html=True,
            )
            fig_m = go.Figure()
            metric_cols = ["roc_auc", "pr_auc", "f1", "accuracy", "precision", "recall", "brier"]
            metric_labels = ["ROC-AUC", "PR-AUC", "F1-Score", "Accuracy", "Precision", "Recall", "Brier (Sai số)"]
            for raw_name, m_vals in report["metrics"].items():
                fig_m.add_trace(
                    go.Bar(
                        name=MODEL_VI.get(raw_name, raw_name),
                        x=metric_labels,
                        y=[float(m_vals.get(k, 0.0)) for k in metric_cols],
                        marker_color=MODEL_COLORS.get(raw_name, "#d4e88a"),
                        text=[f"{float(m_vals.get(k, 0.0)):.3f}" for k in metric_cols],
                        textposition="outside",
                    )
                )
            fig_m.update_layout(
                barmode="group",
                height=360,
                margin=dict(t=20, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
                yaxis=dict(range=[0, 1.05], showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
            )
            st.plotly_chart(fig_m, width="stretch")

    with c_right:
        with st.container(key="glass_dist_chart"):
            st.markdown(
                '<div class="panel-head"><span>Phân bố Nhãn trong Bộ dữ liệu</span>'
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
                    hole=0.56,
                    marker=dict(colors=["#ff5a52", "#4ade80"], line=dict(color="#0c0e12", width=2)),
                    textinfo="label+percent+value",
                )
            )
            fig_dist.update_layout(
                height=360,
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
                showlegend=False,
            )
            st.plotly_chart(fig_dist, width="stretch")

    with st.container(key="glass_cv_table"):
        validation = report.get("validation", {})
        st.markdown(
            '<div class="panel-head"><span>Bảng tổng hợp Chỉ số Kiểm tra (Holdout 20%) & Kiểm định chéo 5-Fold (Train 80%)</span>'
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
            "💡 **Giải thích khoa học:** Nhãn của bộ dữ liệu mô phỏng được sinh từ hàm tuyến tính logit cộng nhiễu Gaussian (σ = 0.8), "
            f"nên trần lý thuyết (Oracle ROC-AUC) là **{ceiling:.3f}**. Hồi quy Logistic khớp đúng cấu trúc hàm sinh dữ liệu nên đạt sát trần lý thuyết; "
            "Random Forest và XGBoost có độ linh hoạt phi tuyến cao hơn nên bám nhẹ vào nhiễu ngẫu nhiên trên dữ liệu giả lập."
        )

with tab2:
    col_roc, col_pr = st.columns(2, gap="medium")
    with col_roc:
        with st.container(key="glass_roc"):
            st.markdown(
                '<div class="panel-head"><span>Đường cong ROC (Receiver Operating Characteristic)</span>'
                "<small>Đánh giá khả năng phân tách 2 lớp</small></div>",
                unsafe_allow_html=True,
            )
            roc_data = report.get("roc_curves", {})
            fig_roc = go.Figure()
            for raw_name, curve in roc_data.items():
                auc_val = report["metrics"][raw_name].get("roc_auc")
                lbl = f"{MODEL_VI.get(raw_name, raw_name)} (AUC = {auc_val:.3f})" if auc_val else MODEL_VI.get(raw_name, raw_name)
                fig_roc.add_trace(
                    go.Scatter(
                        x=curve["fpr"],
                        y=curve["tpr"],
                        mode="lines",
                        line=dict(width=2.5, color=MODEL_COLORS.get(raw_name, "#d4e88a")),
                        name=lbl,
                    )
                )
            fig_roc.add_trace(
                go.Scatter(
                    x=[0, 1],
                    y=[0, 1],
                    mode="lines",
                    line=dict(dash="dash", color="rgba(255,255,255,0.35)"),
                    name="Ngẫu nhiên (AUC = 0.500)",
                )
            )
            fig_roc.update_layout(
                xaxis_title="Tỷ lệ Báo động giả (False Positive Rate)",
                yaxis_title="Tỷ lệ Phát hiện đúng (True Positive Rate / Recall)",
                xaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.06)"),
                height=390,
                margin=dict(t=15, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_roc, width="stretch")

    with col_pr:
        with st.container(key="glass_pr"):
            st.markdown(
                '<div class="panel-head"><span>Đường cong Precision – Recall (PR Curve)</span>'
                "<small>Quan trọng khi dữ liệu sạt lở thực tế hiếm</small></div>",
                unsafe_allow_html=True,
            )
            pr_data = report.get("pr_curves", {})
            fig_pr = go.Figure()
            for raw_name, curve in pr_data.items():
                pr_auc = report["metrics"][raw_name].get("pr_auc")
                lbl = f"{MODEL_VI.get(raw_name, raw_name)} (AP = {pr_auc:.3f})" if pr_auc else MODEL_VI.get(raw_name, raw_name)
                fig_pr.add_trace(
                    go.Scatter(
                        x=curve["recall"],
                        y=curve["precision"],
                        mode="lines",
                        line=dict(width=2.5, color=MODEL_COLORS.get(raw_name, "#38bdf8")),
                        name=lbl,
                    )
                )
            base_pos = float(report.get("positive_rate", 0.5))
            fig_pr.add_trace(
                go.Scatter(
                    x=[0, 1],
                    y=[base_pos, base_pos],
                    mode="lines",
                    line=dict(dash="dash", color="rgba(255,255,255,0.35)"),
                    name=f"Tỷ lệ nền ({base_pos:.2f})",
                )
            )
            fig_pr.update_layout(
                xaxis_title="Độ nhạy (Recall)",
                yaxis_title="Độ chính xác dương (Precision)",
                xaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(range=[0, 1.02], gridcolor="rgba(255,255,255,0.06)"),
                height=390,
                margin=dict(t=15, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
            )
            st.plotly_chart(fig_pr, width="stretch")

    with st.container(key="glass_cal"):
        st.markdown(
            '<div class="panel-head"><span>Đường Hiệu chuẩn Xác suất (Reliability / Calibration Curve)</span>'
            "<small>Đánh giá mức độ tin cậy của điểm nguy cơ dự báo so với tần suất thực tế</small></div>",
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
                    marker=dict(size=8),
                    line=dict(width=2.5, color=MODEL_COLORS.get(raw_name, "#d4e88a")),
                    name=f"{MODEL_VI.get(raw_name, raw_name)} (Brier = {brier_v:.3f})",
                )
            )
        cal_fig.add_trace(
            go.Scatter(
                x=[0, 1],
                y=[0, 1],
                mode="lines",
                line=dict(dash="dash", color="rgba(255,255,255,0.45)"),
                name="Hiệu chuẩn hoàn hảo (y = x)",
            )
        )
        cal_fig.update_layout(
            xaxis_title="Xác suất dự đoán trung bình trong từng phân vị (Mean Predicted Probability)",
            yaxis_title="Tỷ lệ sạt lở thực tế quan sát được (Empirical Fraction Positive)",
            xaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(range=[0, 1], gridcolor="rgba(255,255,255,0.06)"),
            height=360,
            margin=dict(t=15, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1.0),
        )
        st.plotly_chart(cal_fig, width="stretch")

with tab3:
    col_cm, col_fi = st.columns([1.05, 1.35], gap="medium")
    with col_cm:
        with st.container(key="glass_cm"):
            st.markdown(
                '<div class="panel-head"><span>Ma trận Nhầm lẫn (Confusion Matrix Heatmap)</span>'
                "<small>Trên 1.000 mẫu kiểm tra độc lập</small></div>",
                unsafe_allow_html=True,
            )
            matrix_models = report.get("confusion_matrices", {})
            selected_cm_model = st.selectbox(
                "Chọn mô hình xem Ma trận nhầm lẫn",
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
                    textfont={"size": 14, "color": "#ffffff"},
                    colorscale=[[0.0, "#16202a"], [0.5, "#1e4e68"], [1.0, "#2f855a"]],
                    showscale=False,
                )
            )
            fig_cm.update_layout(
                height=320,
                margin=dict(t=15, b=15, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
            )
            st.plotly_chart(fig_cm, width="stretch")
            st.caption(
                f"**Phân tích sai số ({MODEL_VI.get(selected_cm_model, selected_cm_model)}):** "
                f"Phát hiện đúng **{tp}** vụ sạt lở (TP), bỏ sót **{fn}** vụ (FN - cần giảm thiểu trong thực tế), "
                f"báo động nhầm **{fp}** trường hợp (FP)."
            )

    with col_fi:
        with st.container(key="glass_fi"):
            st.markdown(
                '<div class="panel-head"><span>Mức độ Đóng góp Đặc trưng (Feature Importance & Hệ số có dấu)</span>'
                "<small>Giải thích hộp đen AI</small></div>",
                unsafe_allow_html=True,
            )
            importance_data = report.get("feature_importance", {})
            selected_fi_model = st.selectbox(
                "Chọn mô hình phân tích đặc trưng",
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
                "#4ade80" if (is_lr and v < 0) else ("#ff5a52" if is_lr else "#38bdf8")
                for v in plot_vals
            ]

            fig_fi = go.Figure(
                go.Bar(
                    x=plot_vals,
                    y=fi_df["label"],
                    orientation="h",
                    marker_color=bar_colors,
                    text=[f"{v:+.3f}" if is_lr else f"{v:.3f}" for v in plot_vals],
                    textposition="outside",
                    cliponaxis=False,
                )
            )
            fig_fi.update_layout(
                height=320,
                margin=dict(t=15, b=15, l=10, r=45),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e9ec", family="Be Vietnam Pro, sans-serif"),
                xaxis=dict(
                    title="Hệ số chuẩn hóa có dấu (+ tăng nguy cơ / - giảm nguy cơ)" if is_lr else "Tầm quan trọng tương đối (Importance)",
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.06)",
                    zeroline=True,
                    zerolinecolor="rgba(255,255,255,0.25)",
                ),
            )
            st.plotly_chart(fig_fi, width="stretch")
            if is_lr:
                st.caption(
                    "🔴 **Thanh màu đỏ (+):** Làm **tăng** xác suất sạt lở (Độ dốc lớn, Mưa nhiều, Độ ẩm đất cao, Đất trống). "
                    "🟢 **Thanh màu xanh (-):** Làm **giảm** nguy cơ sạt lở (Lớp phủ Rừng giữ đất)."
                )
            else:
                st.caption(
                    "🔵 **Feature Importance của mô hình cây:** Cho biết mức độ đóng góp tương đối khi phân nhánh quyết định "
                    "(Độ dốc, Lượng mưa và Độ ẩm đất chiếm tỷ trọng chi phối lớn nhất)."
                )

with tab4:
    with st.container(key="glass_sandbox"):
        st.markdown(
            '<div class="panel-head"><span>🧪 Phòng thí nghiệm Dự báo Tương tác (Interactive What-If AI Predictor)</span>'
            "<small>Thử nghiệm kịch bản địa chất – thủy văn bất kỳ và đối chiếu kết quả của cả 3 mô hình AI</small></div>",
            unsafe_allow_html=True,
        )
        preset_options = ["Tùy chỉnh tự do"] + [f"{name} ({code} - {cover})" for code, name, _, _, cover in AREAS]
        chosen_preset = st.selectbox("Chọn nhanh thông số nền từ 12 xã giám sát (hoặc tùy chỉnh):", preset_options, key="sb_preset")

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
            in_slope = st.slider("Độ dốc sườn (slope_deg - °)", 0.0, 65.0, value=default_slope, step=0.5)
            in_elev = st.slider("Độ cao địa hình (elevation_m - m)", 20.0, 2200.0, value=default_elev, step=10.0)
        with sc2:
            in_rain = st.slider("Lượng mưa 24 giờ (rainfall_mm - mm)", 0.0, 450.0, value=default_rain, step=5.0)
            in_soil = st.slider("Độ ẩm đất (soil_moisture)", 0.05, 0.98, value=default_soil, step=0.01)
        with sc3:
            cover_Display = ["Rừng tự nhiên", "Rừng trồng", "Đất nông nghiệp", "Đất trống", "Đô thị / Khu dân cư"]
            cover_map_ext = {**COVER_TO_CLASS, "Đô thị / Khu dân cư": "urban"}
            in_cover_vi = st.selectbox(
                "Lớp phủ bề mặt (landcover)",
                cover_Display,
                index=cover_Display.index(default_cover) if default_cover in cover_Display else 0,
            )
            in_cover_code = cover_map_ext[in_cover_vi]
            st.caption(f"Mã hóa đầu vào mô hình: `landcover = '{in_cover_code}'`")

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
            lvl_col = "#ff5a52" if prob_val >= 0.45 else ("#f5b942" if prob_val >= 0.25 else "#4ade80")
            with pred_cols[idx_m]:
                st.markdown(
                    f'<div class="kpi-card" style="border-color:{lvl_col}44">'
                    f'<div class="kpi-head"><i style="background:{MODEL_COLORS[m_key]}"></i>{MODEL_VI[m_key]}</div>'
                    f'<div class="kpi-num" style="color:{lvl_col}">{prob_val:.3f}</div>'
                    f'<div class="kpi-sub">Phân mức: <b style="color:{lvl_col}">{lvl_str}</b></div>'
                    "</div>",
                    unsafe_allow_html=True,
                )
        with pred_cols[3]:
            lvl_o = "Cao" if oracle_prob >= 0.45 else ("Trung bình" if oracle_prob >= 0.25 else "Thấp")
            col_o = "#ff5a52" if oracle_prob >= 0.45 else ("#f5b942" if oracle_prob >= 0.25 else "#4ade80")
            st.markdown(
                f'<div class="kpi-card">'
                '<div class="kpi-head"><i style="background:#e8e9ec"></i>Quy luật Tham chiếu</div>'
                f'<div class="kpi-num">{oracle_prob:.3f}</div>'
                f'<div class="kpi-sub">Mức kỳ vọng: <b style="color:{col_o}">{lvl_o}</b></div>'
                "</div>",
                unsafe_allow_html=True,
            )