"""
Khởi tạo cơ sở dữ liệu SQLite: data/landslide.db
Chạy: python init_database.py
"""
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

# Đảm bảo import được data_engine
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "app"))

from core.data_engine import build_base, compute, AREAS

DB_PATH = os.path.join(BASE_DIR, "data", "landslide.db")
CSV_PATH = os.path.join(BASE_DIR, "data", "processed", "landslide_dataset.csv")

def init_db():
    print(f"[*] Bat dau khoi tao co so du lieu tai: {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)

    # Kết nối SQLite
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
        source TEXT DEFAULT 'NASA_GLC'
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
    print("[+] Da tao cau truc cac bang (Schema) thanh cong!")

    # Lấy dữ liệu cơ sở từ data_engine
    print("[*] Dang trich xuat du lieu co so...")
    base = build_base()
    risk, cells, df = compute(base, scale=1.0, thr=(0.40, 0.70))
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
        """, (r.code, r.name, r.lat, r.lon, r.cover, round(r.elev, 1), round(r.slope, 1), 'Active'))
    print(f"[+] Da luu {len(df)} khu vuc vao bang 'areas'.")

    # Nạp bảng landslide_events
    ev = base["events"]
    for r in ev.itertuples():
        cursor.execute("""
        INSERT INTO landslide_events (event_id, event_date, lat, lon, elevation, cause, damage_mil_vnd, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (r.id, r.date, round(r.lat, 4), round(r.lon, 4), round(r.elev, 1), r.cause, int(r.damage), 'Historical_Catalog'))
    print(f"[+] Da luu {len(ev)} vu sat lo vao bang 'landslide_events'.")

    # Nạp bảng predictions (Lần đánh giá hiện tại)
    for r in df.itertuples():
        cursor.execute("""
        INSERT INTO predictions (area_code, model_name, risk_score, risk_level, rainfall_mm, slope_deg, predicted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r.code, 'XGBoost_v1.0', round(r.score, 4), r.level, round(r.rain, 1), round(r.slope, 1), now_str))
    print(f"[+] Da luu {len(df)} ban ghi danh gia vao bang 'predictions'.")

    # Nạp bảng alerts (Cho các vùng có nguy cơ Cao hoặc Trung bình)
    alert_count = 0
    for r in df.itertuples():
        if r.level in ("Cao", "Trung bình"):
            msg = f"Nguy co {r.level.upper()}: Diem rui ro dat {r.score:.3f}. Luong mua do duoc {r.rain:.1f}mm, do doc {r.slope:.1f} deg."
            cursor.execute("""
            INSERT INTO alerts (area_code, area_name, severity, message, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
            """, (r.code, r.name, r.level, msg, now_str))
            alert_count += 1
    print(f"[+] Da luu {alert_count} canh bao vao bang 'alerts'.")

    # Nạp bảng metadata_info
    cursor.execute("INSERT INTO metadata_info VALUES (?, ?, ?)", ("region", "Nam Tra My & Phuoc Son, Quang Nam", now_str))
    cursor.execute("INSERT INTO metadata_info VALUES (?, ?, ?)", ("dem_resolution", "SRTM 30m / Projected EPSG:32648", now_str))
    cursor.execute("INSERT INTO metadata_info VALUES (?, ?, ?)", ("ai_model", "XGBoost Classifier + Logistic Regression Baseline", now_str))
    cursor.execute("INSERT INTO metadata_info VALUES (?, ?, ?)", ("db_version", "1.0.0", now_str))

    conn.commit()
    conn.close()

    # 6. Đồng thời xuất file CSV dataset mẫu vào data/processed/
    print("[*] Dang xuat file training_dataset.csv phuc vu huan luyen Machine Learning...")
    np.random.seed(42)
    n_samples = 3000
    elev_samples = np.random.uniform(50, 1800, n_samples)
    slope_samples = np.random.uniform(2, 65, n_samples)
    aspect_samples = np.random.uniform(0, 360, n_samples)
    rain_samples = np.random.uniform(30, 450, n_samples)
    lc_choices = np.random.choice(['Rung tu nhien', 'Rung trong', 'Dat nong nghiep', 'Dat trong', 'Do thi/Khu dan cu'], n_samples, p=[0.4, 0.25, 0.15, 0.15, 0.05])
    flow_acc = np.random.uniform(10, 5000, n_samples)

    # Tính nhãn sạt lở
    risk_metric = (slope_samples / 65) * 0.45 + (rain_samples / 450) * 0.40 + (elev_samples / 1800) * 0.15
    lc_bias = {'Rung tu nhien': -0.12, 'Rung trong': 0.02, 'Dat nong nghiep': 0.10, 'Dat trong': 0.25, 'Do thi/Khu dan cu': 0.15}
    risk_metric += np.array([lc_bias[lc] for lc in lc_choices])
    labels = (risk_metric > 0.58).astype(int)

    dataset_df = pd.DataFrame({
        "Elevation_m": np.round(elev_samples, 1),
        "Slope_deg": np.round(slope_samples, 1),
        "Aspect_deg": np.round(aspect_samples, 1),
        "Rainfall_24h_mm": np.round(rain_samples, 1),
        "Land_Cover": lc_choices,
        "Flow_Accumulation": np.round(flow_acc, 0),
        "Landslide_Label": labels
    })
    dataset_df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
    print(f"[+] Da tao file dataset: {CSV_PATH} ({len(dataset_df)} dong)")
    print("\n=======================================================")
    print("[THANH CONG] Co so du lieu SQLite da duoc tao hoan chinh!")
    print(f"Duong dan file: {DB_PATH}")
    print("=======================================================")

if __name__ == "__main__":
    init_db()
