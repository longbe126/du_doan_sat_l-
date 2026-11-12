"""
Khởi tạo cơ sở dữ liệu SQLite: data/landslide.db
Chạy: python init_database.py
"""
import os
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd

# Đảm bảo import được data_engine và model_loader
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if os.path.join(BASE_DIR, "app") not in sys.path:
    sys.path.insert(0, os.path.join(BASE_DIR, "app"))

from core.data_engine import build_base, compute, AREAS
from core.model_loader import load_best_model
from src.simulation.rules import LANDCOVER_CLASSES, LANDCOVER_PRIOR, NOISE_SD, deterministic_score

DB_PATH = os.path.join(BASE_DIR, "data", "landslide.db")
CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "landslide_dataset.csv")


def init_db():
    print(f"[*] Bắt đầu khởi tạo cơ sở dữ liệu tại: {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Bảng areas (Khu vực theo dõi)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS areas (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        land_cover TEXT,
        elevation REAL,
        slope REAL,
        status TEXT DEFAULT 'Active'
    );
    """)

    # 2. Bảng landslide_events (Sự kiện sạt lở lịch sử)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS landslide_events (
        event_id TEXT PRIMARY KEY,
        event_date TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL,
        elevation REAL,
        cause TEXT,
        damage_mil_vnd INTEGER,
        source TEXT DEFAULT 'Historical_Catalog'
    );
    """)

    # 3. Bảng predictions (Lịch sử các lần mô hình AI đánh giá)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_code TEXT,
        model_name TEXT,
        risk_score REAL,
        risk_level TEXT,
        rainfall_mm REAL,
        slope_deg REAL,
        predicted_at TEXT,
        FOREIGN KEY (area_code) REFERENCES areas (code)
    );
    """)

    # 4. Bảng alerts (Lịch sử cảnh báo nguy cơ)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_code TEXT,
        area_name TEXT,
        severity TEXT,
        message TEXT,
        created_at TEXT,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (area_code) REFERENCES areas (code)
    );
    """)

    # 5. Bảng metadata_info (Thông tin nguồn dữ liệu & phiên bản)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS metadata_info (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TEXT
    );
    """)

    conn.commit()
    print("[+] Đã tạo cấu trúc các bảng (Schema) thành công!")

    # Lấy dữ liệu cơ sở và mô hình tốt nhất
    print("[*] Đang trích xuất dữ liệu cơ sở và chạy mô hình đánh giá...")
    base = build_base()
    model_obj, model_name, _ = load_best_model()
    default_thr = (0.25, 0.45)
    risk, cells, df = compute(base, scale=1.0, thr=default_thr, model=model_obj)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Xóa dữ liệu cũ nếu có
    cursor.execute("DELETE FROM areas")
    cursor.execute("DELETE FROM landslide_events")
    cursor.execute("DELETE FROM predictions")
    cursor.execute("DELETE FROM alerts")
    cursor.execute("DELETE FROM metadata_info")

    # Nạp bảng areas
    for r in df.itertuples():
        cursor.execute("""
        INSERT INTO areas (code, name, lat, lon, land_cover, elevation, slope, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (r.code, r.name, r.lat, r.lon, r.cover, round(r.elev, 1), round(r.slope, 1), "Active"))
    print(f"[+] Đã lưu {len(df)} khu vực vào bảng 'areas'.")

    # Nạp bảng landslide_events
    ev = base["events"]
    for r in ev.itertuples():
        cursor.execute("""
        INSERT INTO landslide_events (event_id, event_date, lat, lon, elevation, cause, damage_mil_vnd, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (r.id, r.date, round(r.lat, 4), round(r.lon, 4), round(r.elev, 1), r.cause, int(r.damage), "Historical_Catalog"))
    print(f"[+] Đã lưu {len(ev)} vụ sạt lở vào bảng 'landslide_events'.")

    # Nạp bảng predictions (Lần đánh giá hiện tại)
    for r in df.itertuples():
        cursor.execute("""
        INSERT INTO predictions (area_code, model_name, risk_score, risk_level, rainfall_mm, slope_deg, predicted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r.code, model_name, round(r.score, 4), r.level, round(r.rain, 1), round(r.slope, 1), now_str))
    print(f"[+] Đã lưu {len(df)} bản ghi đánh giá ({model_name}) vào bảng 'predictions'.")

    # Nạp bảng alerts (Cho các vùng có nguy cơ Cao hoặc Trung bình theo ngưỡng chuẩn)
    alert_count = 0
    for r in df.itertuples():
        if r.level in ("Cao", "Trung bình"):
            msg = (
                f"Nguy cơ {r.level.upper()}: Điểm rủi ro đạt {r.score:.3f}. "
                f"Lượng mưa 24h {r.rain:.1f} mm, độ dốc {r.slope:.1f}°."
            )
            cursor.execute("""
            INSERT INTO alerts (area_code, area_name, severity, message, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """, (r.code, r.name, r.level, msg, now_str))
            alert_count += 1
    print(f"[+] Đã lưu {alert_count} cảnh báo vào bảng 'alerts'.")

    # Nạp bảng metadata_info
    cursor.execute("INSERT INTO metadata_info VALUES (?, ?, ?)", ("region", "Nam Trà My & Phước Sơn, Quảng Nam", now_str))
    cursor.execute("INSERT INTO metadata_info VALUES (?, ?, ?)", ("dem_resolution", "Mô phỏng 72x72 / EPSG:32648", now_str))
    cursor.execute("INSERT INTO metadata_info VALUES (?, ?, ?)", ("ai_model", model_name, now_str))
    cursor.execute("INSERT INTO metadata_info VALUES (?, ?, ?)", ("thresholds", f"{default_thr[0]}-{default_thr[1]}", now_str))
    cursor.execute("INSERT INTO metadata_info VALUES (?, ?, ?)", ("db_version", "2.0.0", now_str))

    conn.commit()
    conn.close()

    # 6. Đồng thời xuất file CSV dataset mẫu có kèm block_id (xã/khu vực) tương thích 100% với train_models.py
    print("[*] Đang xuất file landslide_dataset.csv chuẩn schema huấn luyện Machine Learning...")
    rng = np.random.default_rng(42)
    n_samples = 3000
    slope_samples = rng.uniform(0, 65, n_samples)
    elev_samples = rng.uniform(0, 2500, n_samples)
    rain_samples = rng.gamma(shape=2.0, scale=60.0, size=n_samples)
    soil_samples = rng.uniform(0.05, 0.95, n_samples)
    lc_choices = rng.choice(LANDCOVER_CLASSES, size=n_samples, p=LANDCOVER_PRIOR)
    block_ids = rng.choice([code for code, _, _, _, _ in AREAS], size=n_samples)

    base_score = deterministic_score(slope_samples, elev_samples, rain_samples, soil_samples, lc_choices)
    score = base_score + rng.normal(0, NOISE_SD, n_samples)
    prob = 1.0 / (1.0 + np.exp(-score))
    labels = rng.binomial(1, prob)

    dataset_df = pd.DataFrame({
        "slope_deg": np.round(slope_samples, 2),
        "elevation_m": np.round(elev_samples, 1),
        "rainfall_mm": np.round(rain_samples, 2),
        "soil_moisture": np.round(soil_samples, 3),
        "landcover": lc_choices,
        "block_id": block_ids,
        "landslide": labels,
        "data_source": "SIMULATED_SPATIAL",
    })
    dataset_df.to_csv(CSV_PATH, index=False, encoding="utf-8")
    print(f"[+] Đã tạo file dataset: {CSV_PATH} ({len(dataset_df)} dòng, tương thích chuẩn train_models.py)")
    print("\n=======================================================")
    print("[THÀNH CÔNG] Cơ sở dữ liệu SQLite đã được tạo hoàn chỉnh!")
    print(f"Đường dẫn file: {DB_PATH}")
    print("=======================================================")


if __name__ == "__main__":
    init_db()
