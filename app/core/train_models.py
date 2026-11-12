import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import (
    GroupKFold,
    GroupShuffleSplit,
    StratifiedKFold,
    cross_validate,
    train_test_split,
)
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
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

META_PATH = DATA_PATH.with_name("demo_dataset_meta.json")

TARGET = "landslide"
DROP_COLUMNS = ["data_source"]

# Nếu bộ dữ liệu thật có cột khối không gian (ví dụ ô lưới lớn, lưu vực, xã), cột này được dùng
# để chia train/test và kiểm định chéo theo vùng, tránh việc ô gần nhau rơi vào cả hai tập.
GROUP_CANDIDATES = ["block_id", "spatial_block", "group"]
N_SPLITS = 5


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

    # Cột khối không gian (nếu có) chỉ dùng để chia tập, không đưa vào đặc trưng.
    group_col = next((c for c in GROUP_CANDIDATES if c in df.columns), None)
    groups = df[group_col] if group_col else None

    # Loại bỏ cột metadata để không đưa nguồn dữ liệu thành đặc trưng.
    drop_cols = [TARGET] + DROP_COLUMNS + ([group_col] if group_col else [])
    X = df.drop(columns=drop_cols, errors="ignore")
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

    if group_col:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_idx, test_idx = next(splitter.split(X, y, groups))
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        cv = GroupKFold(n_splits=N_SPLITS)
        holdout_desc = f"Chia theo khối không gian (cột {group_col}), 80/20"
        cv_desc = f"GroupKFold {N_SPLITS} phần theo cột {group_col}"
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )
        cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)
        holdout_desc = "Chia ngẫu nhiên có phân tầng theo nhãn, 80/20"
        cv_desc = f"StratifiedKFold {N_SPLITS} phần, xáo trộn ngẫu nhiên"

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
    calibration_data = {}
    cv_data = {}

    for name, estimator in models.items():
        pipeline = Pipeline([
            ("preprocess", make_preprocess()),
            ("model", estimator),
        ])

        # Kiểm định chéo trên toàn bộ dữ liệu: cho biết điểm số ổn định đến đâu giữa các lần chia.
        cv_res = cross_validate(
            pipeline, X, y, cv=cv, groups=groups,
            scoring={"roc_auc": "roc_auc", "average_precision": "average_precision"},
        )
        cv_data[name] = {
            "roc_auc_mean": float(cv_res["test_roc_auc"].mean()),
            "roc_auc_std": float(cv_res["test_roc_auc"].std()),
            "average_precision_mean": float(cv_res["test_average_precision"].mean()),
            "average_precision_std": float(cv_res["test_average_precision"].std()),
        }

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
            "pr_auc": float(average_precision_score(y_test, proba)),
            "brier": float(brier_score_loss(y_test, proba)),
        }

        # Đường hiệu chuẩn: xác suất dự đoán so với tỷ lệ sạt lở thực tế trong từng nhóm.
        frac_pos, mean_pred = calibration_curve(
            y_test, proba, n_bins=10, strategy="quantile"
        )
        calibration_data[name] = {
            "mean_predicted": mean_pred.tolist(),
            "fraction_positive": frac_pos.tolist(),
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

    reference = None
    if META_PATH.exists():
        with open(META_PATH, "r", encoding="utf-8") as f:
            reference = json.load(f)

    best_model = max(cv_data, key=lambda k: cv_data[k]["roc_auc_mean"])
    tz = timezone(timedelta(hours=7))

    report = {
        "dataset_path": DATA_PATH.relative_to(ROOT).as_posix(),
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
        "features": X.columns.tolist(),
        "best_model": best_model,
        "trained_at": datetime.now(tz).strftime("%Y-%m-%d %H:%M (UTC+7)"),
        "positive_rate": float(y.mean()),
        "validation": {
            "holdout": holdout_desc,
            "cross_validation": cv_desc,
            "spatial": group_col is not None,
        },
        "cross_validation": cv_data,
        "calibration_curves": calibration_data,
        "reference": reference,
    }

    with open(REPORT_DIR / "evaluation.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nKẾT QUẢ ĐÁNH GIÁ")
    print(pd.DataFrame(metrics).T.round(4))
    print("\nKIỂM ĐỊNH CHÉO (trung bình ± độ lệch chuẩn)")
    for name, v in cv_data.items():
        print(f"  {name}: ROC-AUC {v['roc_auc_mean']:.3f} ± {v['roc_auc_std']:.3f}, "
              f"PR-AUC {v['average_precision_mean']:.3f} ± {v['average_precision_std']:.3f}")
    print(f"\nMô hình tốt nhất theo ROC-AUC kiểm định chéo: {best_model}")
    print(f"\nBáo cáo: {REPORT_DIR / 'evaluation.json'}")


if __name__ == "__main__":
    main()
