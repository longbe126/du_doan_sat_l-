
from pathlib import Path

import numpy as np
import pandas as pd


SEED = 42
N_SAMPLES = 5000

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "processed" / "demo_dataset.csv"


def generate_dataset(n_samples=N_SAMPLES, seed=SEED):
    rng = np.random.default_rng(seed)

    slope = rng.uniform(0, 65, n_samples)
    elevation = rng.uniform(0, 2500, n_samples)
    rainfall = rng.gamma(shape=2.0, scale=60.0, size=n_samples)
    soil_moisture = rng.uniform(0.05, 0.95, n_samples)

    landcover = rng.choice(
        ["forest", "agriculture", "bare", "urban"],
        size=n_samples,
        p=[0.55, 0.25, 0.10, 0.10],
    )

    # Quy luật tạo nhãn MÔ PHỎNG, không phải công thức địa chất đã kiểm chứng.
    score = (
        -4.0
        + 0.075 * slope
        + 0.006 * rainfall
        + 1.2 * soil_moisture
        + 0.0002 * elevation
        + 0.8 * (landcover == "bare")
        + 0.25 * (landcover == "agriculture")
        - 0.3 * (landcover == "forest")
        + rng.normal(0, 0.8, n_samples)
    )

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

    return df


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    df = generate_dataset()
    df.to_csv(OUTPUT, index=False)

    print(f"Đã tạo: {OUTPUT}")
    print(f"Số dòng: {len(df)}")
    print("\nPhân bố nhãn:")
    print(df["landslide"].value_counts())
    print("\nTỷ lệ sạt lở:")
    print(round(df["landslide"].mean() * 100, 2), "%")
