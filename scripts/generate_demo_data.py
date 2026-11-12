import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')

import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.simulation.rules import (  # noqa: E402
    LANDCOVER_CLASSES, LANDCOVER_PRIOR, NOISE_SD, deterministic_score,
)


SEED = 42
N_SAMPLES = 5000

OUTPUT = ROOT / "data" / "processed" / "demo_dataset.csv"
META_OUTPUT = ROOT / "data" / "processed" / "demo_dataset_meta.json"


def generate_dataset(n_samples=N_SAMPLES, seed=SEED):
    rng = np.random.default_rng(seed)

    slope = rng.uniform(0, 65, n_samples)
    elevation = rng.uniform(0, 2500, n_samples)
    rainfall = rng.gamma(shape=2.0, scale=60.0, size=n_samples)
    soil_moisture = rng.uniform(0.05, 0.95, n_samples)

    landcover = rng.choice(LANDCOVER_CLASSES, size=n_samples, p=LANDCOVER_PRIOR)

    # Quy luật tạo nhãn MÔ PHỎNG (dùng chung với bản đồ), không phải công thức địa chất đã kiểm chứng.
    base_score = deterministic_score(slope, elevation, rainfall, soil_moisture, landcover)
    score = base_score + rng.normal(0, NOISE_SD, n_samples)

    probability = 1 / (1 + np.exp(-score))
    landslide = rng.binomial(1, probability)

    df = pd.DataFrame({
        "slope_deg": slope,
        "elevation_m": elevation,
        "rainfall_mm": rainfall,
        "soil_moisture": soil_moisture,
        "landcover": landcover,
        "landslide": landslide,
        "data_source": "SIMULATED",
    })

    # Gắn điểm không nhiễu để tính "trần" AUC; không đưa vào bảng dữ liệu.
    df.attrs["base_score"] = base_score
    return df


def reference_metadata(df, seed=SEED):
    """Trần AUC: mô hình biết đúng quy luật nhưng không biết nhiễu thì chỉ đạt tới mức này."""
    return {
        "generator": "scripts/generate_demo_data.py",
        "seed": seed,
        "n_rows": int(len(df)),
        "noise_sd": NOISE_SD,
        "positive_rate": float(df["landslide"].mean()),
        "ceiling_roc_auc": float(roc_auc_score(df["landslide"], df.attrs["base_score"])),
    }


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    df = generate_dataset()
    df.to_csv(OUTPUT, index=False)

    meta = reference_metadata(df)
    with open(META_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"Trần ROC-AUC theo quy luật sinh dữ liệu: {meta['ceiling_roc_auc']:.3f}")

    print(f"Đã tạo: {OUTPUT}")
    print(f"Số dòng: {len(df)}")
    print("\nPhân bố nhãn:")
    print(df["landslide"].value_counts())
    print("\nTỷ lệ sạt lở:")
    print(round(df["landslide"].mean() * 100, 2), "%")
