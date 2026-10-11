from pathlib import Path
import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "reports" / "evaluation.json"

st.set_page_config(
    page_title="AI Evaluation",
    page_icon="",
    layout="wide",
)

st.title("AI Model Evaluation")
st.caption(
    "Kết quả được đọc từ báo cáo sinh ra bởi pipeline huấn luyện."
)

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

metric_name = st.selectbox(
    "Chỉ số để so sánh",
    ["f1", "recall", "precision", "roc_auc", "accuracy"],
)

metric_values = metrics[[metric_name]].dropna()
st.bar_chart(metric_values)

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