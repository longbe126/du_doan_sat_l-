
from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "demo_dataset.csv"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"

TARGET = "landslide"
DROP_COLUMNS = ["data_source"]


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Không tìm thấy {DATA_PATH}. "
            "Hãy tạo dataset hoặc đặt dataset đã xử lý đúng vị trí."
        )

    df = pd.read_csv(DATA_PATH)

    required = {
        "slope_deg",
        "elevation_m",
        "rainfall_mm",
        "soil_moisture",
        "landcover",
        TARGET,
    }
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Dataset thiếu các cột: {sorted(missing)}")

    df = df.dropna(subset=[TARGET]).copy()
    df[TARGET] = df[TARGET].astype(int)

    if set(df[TARGET].unique()) != {0, 1}:
        raise ValueError("Nhãn landslide phải có cả hai giá trị 0 và 1.")

    # Loại bỏ cột metadata để không đưa nguồn dữ liệu thành đặc trưng.
    X = df.drop(columns=[TARGET] + DROP_COLUMNS, errors="ignore")
    y = df[TARGET]

    if y.value_counts().min() < 2:
        raise ValueError("Mỗi lớp cần ít nhất 2 mẫu để chia train/test.")

    numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = X.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    def make_preprocess():
        numeric_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])

        categorical_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ])

        return ColumnTransformer([
            ("numeric", numeric_pipe, numeric_cols),
            ("categorical", categorical_pipe, categorical_cols),
        ])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    models = {
        "logistic_regression": LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "xgboost": XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
            n_jobs=-1,
        ),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    metrics = {}
    roc_data = {}
    confusion_data = {}
    feature_importance = {}

    for name, estimator in models.items():
        pipeline = Pipeline([
            ("preprocess", make_preprocess()),
            ("model", estimator),
        ])

        pipeline.fit(X_train, y_train)

        pred = pipeline.predict(X_test)
        proba = pipeline.predict_proba(X_test)[:, 1]

        auc = (
            roc_auc_score(y_test, proba)
            if y_test.nunique() == 2
            else None
        )

        metrics[name] = {
            "accuracy": float(accuracy_score(y_test, pred)),
            "precision": float(
                precision_score(y_test, pred, zero_division=0)
            ),
            "recall": float(
                recall_score(y_test, pred, zero_division=0)
            ),
            "f1": float(f1_score(y_test, pred, zero_division=0)),
            "roc_auc": float(auc) if auc is not None else None,
        }

        cm = confusion_matrix(y_test, pred, labels=[0, 1])
        confusion_data[name] = cm.tolist()

        if auc is not None:
            fpr, tpr, thresholds = roc_curve(y_test, proba)
            roc_data[name] = {
                "fpr": fpr.tolist(),
                "tpr": tpr.tolist(),
                "thresholds": thresholds.tolist(),
            }

        # Tên đặc trưng sau One-Hot Encoding.
        fitted_preprocess = pipeline.named_steps["preprocess"]
        names = fitted_preprocess.get_feature_names_out()
        fitted_model = pipeline.named_steps["model"]

        if hasattr(fitted_model, "feature_importances_"):
            values = fitted_model.feature_importances_
        elif hasattr(fitted_model, "coef_"):
            values = np.abs(fitted_model.coef_[0])
        else:
            values = np.zeros(len(names))

        feature_importance[name] = sorted(
            [
                {"feature": str(feature), "importance": float(value)}
                for feature, value in zip(names, values)
            ],
            key=lambda item: item["importance"],
            reverse=True,
        )

        joblib.dump(pipeline, MODEL_DIR / f"{name}.pkl")
        print(f"Đã huấn luyện và lưu {name}")

    data_source = (
        sorted(df["data_source"].astype(str).unique().tolist())
        if "data_source" in df.columns
        else ["UNSPECIFIED"]
    )

    report = {
        "dataset_path": str(DATA_PATH.relative_to(ROOT)),
        "dataset_source": data_source,
        "n_rows": int(len(df)),
        "n_features": int(X.shape[1]),
        "target_distribution": {
            str(k): int(v) for k, v in y.value_counts().items()
        },
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "metrics": metrics,
        "confusion_matrices": confusion_data,
        "roc_curves": roc_data,
        "feature_importance": feature_importance,
        "random_state": 42,
    }

    with open(REPORT_DIR / "evaluation.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nKẾT QUẢ ĐÁNH GIÁ")
    print(pd.DataFrame(metrics).T.round(4))
    print(f"\nBáo cáo: {REPORT_DIR / 'evaluation.json'}")


if __name__ == "__main__":
    main()
