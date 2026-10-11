import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import sys

# Thêm đường dẫn để import module dataset_builder từ thư mục data_pipeline
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_pipeline.dataset_builder import create_mock_dataset, preprocess_features

def evaluate_model(name, model, X_test, y_test):
    """Đánh giá và in ra các chỉ số mô hình (Accuracy, Precision, Recall, F1, ROC-AUC) như Đề cương (Mục 11.1)."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else y_pred

    metrics = {
        "Mô hình": name,
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred),
        "Recall": recall_score(y_test, y_pred),
        "F1-score": f1_score(y_test, y_pred),
    }
    try:
        metrics["ROC-AUC"] = roc_auc_score(y_test, y_prob)
    except ValueError:
        metrics["ROC-AUC"] = float("nan")

    print(f"--- Đánh giá mô hình: {name} ---")
    print(f"Accuracy : {metrics['Accuracy']:.4f}")
    print(f"Precision: {metrics['Precision']:.4f}")
    print(f"Recall   : {metrics['Recall']:.4f}")
    print(f"F1-score : {metrics['F1-score']:.4f}")
    print(f"ROC-AUC  : {metrics['ROC-AUC']:.4f}")
    print("-" * 35)
    return metrics

def train_all_models():
    results = []
    print("[1/5] Đang tạo dữ liệu (Mock Dataset) gồm 5000 mẫu...")
    df = create_mock_dataset(n_samples=5000)
    X, y = preprocess_features(df)
    
    print("[2/5] Phân chia tập Train/Test (80-20)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Chuẩn hóa dữ liệu cho Logistic Regression
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("\n[3/5] Đang huấn luyện Logistic Regression (Baseline)...")
    lr_model = LogisticRegression(max_iter=1000)
    lr_model.fit(X_train_scaled, y_train)
    results.append(evaluate_model("Logistic Regression", lr_model, X_test_scaled, y_test))
    
    print("\n[4/5] Đang huấn luyện Random Forest...")
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    results.append(evaluate_model("Random Forest", rf_model, X_test, y_test))
    
    print("\n[5/5] Đang huấn luyện XGBoost...")
    xgb_model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    xgb_model.fit(X_train, y_train)
    results.append(evaluate_model("XGBoost", xgb_model, X_test, y_test))
    
    # Lưu XGBoost (do thường cho kết quả tốt nhất) và Scaler
    project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    save_dir = os.path.join(project_dir, 'models')
    os.makedirs(save_dir, exist_ok=True)
    
    xgb_path = os.path.join(save_dir, 'xgboost_model.pkl')
    scaler_path = os.path.join(save_dir, 'scaler.pkl')
    
    joblib.dump(xgb_model, xgb_path)
    joblib.dump(scaler, scaler_path)
    print(f"\n[XONG] Đã lưu mô hình XGBoost và Scaler tại:\n- {xgb_path}\n- {scaler_path}")
    return results

if __name__ == "__main__":
    train_all_models()
