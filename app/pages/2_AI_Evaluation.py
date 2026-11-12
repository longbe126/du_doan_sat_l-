from pathlib import Path
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "reports" / "evaluation.json"

if not st.session_state.get("_root_navigation", False):
    st.set_page_config(
        page_title="AI Evaluation",
        page_icon="??",
        layout="wide",
    )

CSS_AI = """
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&display=swap');
html, body, .stApp {
    font-family: 'Be Vietnam Pro', system-ui, sans-serif !important;
    background: #07080b !important;
    color: #e8e9ec !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 300 !important;
    color: #ffffff !important;
}
div[data-testid="stMetric"] {
    background: rgba(34, 36, 40, 0.58) !important;
    backdrop-filter: blur(18px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 18px !important;
    padding: 14px 18px !important;
}
.stButton button {
    background: rgba(34, 36, 40, 0.85) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 999px !important;
    color: #e8e9ec !important;
    font-weight: 500 !important;
    white-space: nowrap !important;
}
.stButton button[data-testid="stBaseButton-primary"], .stButton button[kind="primary"] {
    background: #d4e88a !important;
    color: #1b2208 !important;
    border-color: #d4e88a !important;
    font-weight: 600 !important;
}
[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}
"""
st.markdown(f"<style>{CSS_AI}</style>", unsafe_allow_html=True)

col_hdr1, col_hdr2 = st.columns([2.5, 2])
with col_hdr1:
    st.title("🧠 Đánh giá Mô hình Học máy (AI Evaluation)")
    st.caption("Kết quả được đọc từ báo cáo sinh ra bởi pipeline huấn luyện (reports/evaluation.json).")
with col_hdr2:
    st.write("")
    n1, n2, n3 = st.columns([1, 1.2, 1.2])
    with n1:
        if st.button("Tổng quan", key="nav_overview"):
            st.switch_page("app/main.py")
    with n2:
        if st.button("Lịch sử sạt lở 📜", key="nav_hist"):
            st.switch_page("app/pages/3_Lich_Su_Sat_Lo.py")
    with n3:
        if st.button("Đánh giá AI 🧠", key="nav_ai", type="primary"):
            pass

if not REPORT_PATH.exists():
    st.warning(
        "Chưa có báo cáo đánh giá. Hãy chạy "
        "`python app/core/train_models.py` trước."
    )
    st.stop()

with open(REPORT_PATH, "r", encoding="utf-8") as f:
    report = json.load(f)

sources = report.get("dataset_source", ["UNSPECIFIED"])
is_simulated = any("SIMULATED" in s.upper() for s in sources)

if is_simulated:
    st.warning(
        "DATASET MÔ PHỎNG — các chỉ số chỉ dùng kiểm thử pipeline, "
        "không đại diện cho độ chính xác dự báo sạt lở thực tế."
    )
elif any("UNSPECIFIED" in s.upper() for s in sources):
    st.info("Nguồn dataset chưa được xác minh trong metadata.")
else:
    st.info(f"Nguồn dữ liệu: {', '.join(sources)}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Số mẫu", f"{report['n_rows']:,}")
c2.metric("Số đặc trưng", report["n_features"])
c3.metric("Train", f"{report['train_rows']:,}")
c4.metric("Test", f"{report['test_rows']:,}")

validation = report.get("validation", {})
if validation:
    st.caption(
        f"Cách chia tập: {validation.get('holdout', 'không rõ')}. "
        f"Kiểm định chéo: {validation.get('cross_validation', 'không rõ')}."
    )
    if not validation.get("spatial"):
        st.warning(
            "Chưa kiểm định theo không gian. Bộ dữ liệu mô phỏng không có toạ độ hay khối không gian, "
            "nên các ô gần nhau có thể nằm ở cả tập huấn luyện lẫn tập kiểm tra. Khi dùng dữ liệu thật, "
            "hãy thêm cột `block_id` (xã, lưu vực hoặc ô lưới lớn); quy trình huấn luyện sẽ tự chia theo khối "
            "để điểm số không bị thổi phồng."
        )

best_model = report.get("best_model")
if best_model:
    st.success(
        f"Mô hình đang chạy trên bảng điều khiển: **{best_model}** "
        f"(chọn theo ROC-AUC kiểm định chéo, huấn luyện lúc {report.get('trained_at', 'không rõ')})."
    )

st.subheader("Phân bố nhãn")
target_dist = report.get("target_distribution", {})
distribution_df = pd.DataFrame({
    "Nhãn": [
        "Không sạt lở (0)" if label == "0"
        else "Sạt lở (1)" if label == "1"
        else f"Nhãn {label}"
        for label in target_dist.keys()
    ],
    "Số mẫu": list(target_dist.values()),
})

st.bar_chart(distribution_df.set_index("Nhãn"))

st.subheader("So sánh mô hình")
metrics = pd.DataFrame(report["metrics"]).T
st.dataframe(
    metrics.style.format("{:.3f}"),
    width="stretch",
)

st.caption(
    "PR-AUC là diện tích dưới đường precision-recall; Brier là sai số bình phương trung bình của "
    "xác suất dự đoán (càng thấp càng tốt)."
)

metric_name = st.selectbox(
    "Chỉ số để so sánh",
    ["f1", "recall", "precision", "roc_auc", "pr_auc", "accuracy", "brier"],
)

metric_values = metrics[[metric_name]].dropna()
st.bar_chart(metric_values)

st.subheader("Kiểm định chéo và trần lý thuyết")
cv_report = report.get("cross_validation", {})
reference = report.get("reference") or {}
if cv_report:
    cv_df = pd.DataFrame({
        name: {
            "ROC-AUC (trung bình)": v["roc_auc_mean"],
            "ROC-AUC (độ lệch chuẩn)": v["roc_auc_std"],
            "PR-AUC (trung bình)": v["average_precision_mean"],
            "PR-AUC (độ lệch chuẩn)": v["average_precision_std"],
        }
        for name, v in cv_report.items()
    }).T
    st.dataframe(cv_df.style.format("{:.3f}"), width="stretch")

ceiling = reference.get("ceiling_roc_auc")
if ceiling is not None:
    st.info(
        f"Trần ROC-AUC của bộ dữ liệu mô phỏng là khoảng {ceiling:.3f}. Nhãn được sinh từ một hàm logistic "
        f"cộng nhiễu (độ lệch chuẩn {reference.get('noise_sd', '?')}); ngay cả mô hình biết đúng quy luật cũng "
        "không thể vượt mức này vì không biết được nhiễu. Hồi quy logistic đạt gần đúng trần vì quy luật sinh nhãn "
        "vốn có dạng logistic; rừng ngẫu nhiên và XGBoost không thể cao hơn trần, chúng chỉ có thêm khả năng học "
        "nhầm nhiễu nên thấp hơn một chút. Vì vậy, thứ hạng giữa các mô hình ở đây không cho biết mô hình nào "
        "sẽ tốt hơn trên dữ liệu sạt lở thật."
    )
positive_rate = report.get("positive_rate")
if positive_rate is not None:
    st.caption(
        f"Tỷ lệ sạt lở trong tập mô phỏng là {100 * positive_rate:.1f}%. Sạt lở ngoài thực tế hiếm hơn nhiều, "
        "khi đó accuracy dễ gây hiểu lầm; cần xem recall, PR-AUC và độ hiệu chuẩn."
    )

st.subheader("Đường hiệu chuẩn")
calibration = report.get("calibration_curves", {})
if calibration:
    cal_fig = go.Figure()
    for model_name, curve in calibration.items():
        cal_fig.add_trace(go.Scatter(
            x=curve["mean_predicted"], y=curve["fraction_positive"],
            mode="lines+markers", name=model_name,
        ))
    cal_fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines", line=dict(dash="dash"), name="Hiệu chuẩn hoàn hảo",
    ))
    cal_fig.update_layout(
        xaxis_title="Xác suất dự đoán (trung bình mỗi nhóm)",
        yaxis_title="Tỷ lệ sạt lở thực tế trong nhóm",
        xaxis=dict(range=[0, 1]), yaxis=dict(range=[0, 1]),
        height=420, legend_title="Mô hình",
    )
    st.plotly_chart(cal_fig, width="stretch")
    st.caption(
        "Điểm càng gần đường chéo thì xác suất dự đoán càng sát tỷ lệ thực tế. Đây là kiểm tra trên dữ liệu mô phỏng "
        "(tỷ lệ sạt lở khoảng 50%); với dữ liệu thật cần hiệu chuẩn lại trước khi đọc điểm số như xác suất."
    )
else:
    st.info("Báo cáo chưa có đường hiệu chuẩn. Hãy chạy lại `python app/core/train_models.py`.")

st.subheader("ROC Curve")
roc_data = report.get("roc_curves", {})

if roc_data:
    fig = go.Figure()

    for model_name, curve in roc_data.items():
        auc_value = report["metrics"][model_name].get("roc_auc")
        label = (
            f"{model_name} (AUC = {auc_value:.3f})"
            if auc_value is not None
            else model_name
        )
        fig.add_trace(go.Scatter(
            x=curve["fpr"],
            y=curve["tpr"],
            mode="lines",
            name=label,
        ))

    fig.add_trace(go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode="lines",
        line=dict(dash="dash"),
        name="Đường tham chiếu",
    ))

    fig.update_layout(
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate",
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1]),
        height=480,
        legend_title="Mô hình",
    )
    st.plotly_chart(fig, width="stretch")
else:
    st.info("Không có dữ liệu ROC để hiển thị.")

st.subheader("Confusion Matrix")

matrix_models = report.get("confusion_matrices", {})
if matrix_models:
    selected_model = st.selectbox(
        "Chọn mô hình",
        list(matrix_models.keys()),
    )
    cm = matrix_models[selected_model]

    cm_df = pd.DataFrame(
        cm,
        index=["Thực tế: 0", "Thực tế: 1"],
        columns=["Dự đoán: 0", "Dự đoán: 1"],
    )
    st.dataframe(cm_df, width="stretch")

st.subheader("Feature Importance / Hệ số mô hình")

importance_data = report.get("feature_importance", {})
if importance_data:
    selected_importance_model = st.selectbox(
        "Mô hình phân tích đặc trưng",
        list(importance_data.keys()),
        key="importance_model",
    )

    top_features = importance_data[selected_importance_model][:15]
    importance_df = pd.DataFrame(top_features)

    st.bar_chart(
        importance_df.set_index("feature")["importance"]
    )

    if selected_importance_model == "logistic_regression":
        st.caption(
            "Logistic Regression hiển thị trị tuyệt đối của hệ số. "
            "Giá trị này không cho biết chiều tác động; "
            "cần xem hệ số có dấu nếu muốn diễn giải."
        )
    else:
        st.caption(
            "Feature importance là mức độ đóng góp tương đối theo "
            "cách tính của mô hình, không chứng minh quan hệ nhân quả."
        )

st.caption(f"Dataset: {report['dataset_path']}")
st.caption(
    "Lưu ý: điểm số phụ thuộc vào nguồn dữ liệu, cách gán nhãn, "
    "cách chia tập và chất lượng đặc trưng."
)