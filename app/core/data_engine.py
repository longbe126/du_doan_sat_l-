import numpy as np
import pandas as pd
from datetime import datetime, timedelta

LAT0, LAT1 = 15.02, 15.46
LON0, LON1 = 107.80, 108.26
N = 72          
BLOCK = 4       
NC = N // BLOCK

# Tọa độ thực tế hoặc mock xấp xỉ
AREAS = [
    ("KV01", "Trà Mai", 15.11, 108.01, "Rừng tự nhiên"),
    ("KV02", "Trà Don", 15.20, 108.09, "Rừng trồng"),
    ("KV03", "Trà Leng", 15.10, 107.94, "Rừng tự nhiên"),
    ("KV04", "Trà Vân", 15.18, 108.15, "Đất nông nghiệp"),
    ("KV05", "Trà Linh", 15.07, 108.12, "Rừng tự nhiên"),
    ("KV06", "Trà Tập", 15.19, 108.01, "Đất trống"),
    ("KV07", "Phước Mỹ", 15.38, 107.88, "Rừng trồng"),
    ("KV08", "Phước Chánh", 15.29, 107.90, "Đất nông nghiệp"),
    ("KV09", "Phước Công", 15.29, 107.84, "Rừng tự nhiên"),
    ("KV10", "Phước Năng", 15.40, 108.00, "Rừng trồng"),
    ("KV11", "Phước Xuân", 15.43, 107.92, "Rừng tự nhiên"),
    ("KV12", "Phước Đức", 15.34, 108.12, "Đất nông nghiệp"),
]

def _smooth(a: np.ndarray, passes: int = 2) -> np.ndarray:
    for _ in range(passes):
        p = np.pad(a, 1, mode="edge")
        a = sum(p[i:i + a.shape[0], j:j + a.shape[1]] for i in range(3) for j in range(3)) / 9
    return a

def _norm_noise(rng, passes: int) -> np.ndarray:
    n = _smooth(rng.normal(size=(N, N)), passes)
    return (n - n.mean()) / n.std()

def risk_from(slope, rain, lc, scale):
    s = np.clip(slope / 35, 0, 1.3)
    r = np.clip(rain * scale / 220, 0, 1.6)
    z = -5.0 + 6.4 * s + 3.8 * r + 1.4 * lc
    return 1 / (1 + np.exp(-z))

def build_base() -> dict:
    """Tạo dữ liệu cơ sở tĩnh (Địa hình, Lớp phủ). Cố định Seed để đảm bảo tính tái lập (Reproducible)"""
    rng = np.random.default_rng(11) # Cố định seed
    lat = np.linspace(LAT0, LAT1, N)
    lon = np.linspace(LON0, LON1, N)
    X, Y = np.meshgrid(np.linspace(0, 1, N), np.linspace(0, 1, N))
 
    # Sinh địa hình cơ sở
    elev = np.full((N, N), 330.0)
    for cx, cy, s, h in [(0.25, 0.70, 0.10, 800), (0.60, 0.35, 0.12, 950), (0.78, 0.75, 0.09, 650),
                         (0.45, 0.55, 0.08, 450), (0.15, 0.20, 0.11, 600), (0.88, 0.25, 0.08, 420)]:
        elev += h * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * s ** 2))
    
    # Chỉ dùng noise để tạo chi tiết địa hình thật, không dùng cho nhiễu cảnh báo
    elev += 300 * _norm_noise(rng, 2) + 90 * _norm_noise(rng, 1)
    elev = np.clip(np.where(elev < 80, 80 + 0.25 * (elev - 80), elev), 15, None)
 
    dy = (LAT1 - LAT0) * 111_000 / (N - 1)
    dx = (LON1 - LON0) * 111_000 * np.cos(np.radians(15.2)) / (N - 1)
    gy, gx = np.gradient(elev, dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
 
    # Base rain distribution (historical mean)
    rain = (55 + 95 * np.exp(-((X - 0.55) ** 2 + (Y - 0.35) ** 2) / 0.06)
            + 40 * np.exp(-((X - 0.2) ** 2 + (Y - 0.75) ** 2) / 0.05))
            
    lc = np.clip(0.5 + 0.25 * _norm_noise(rng, 4), 0, 1)
 
    # Grid polygons
    la = np.linspace(LAT0, LAT1, NC + 1)
    lo = np.linspace(LON0, LON1, NC + 1)
    feats = []
    for i in range(NC):
        for j in range(NC):
            ring = [[float(lo[j]), float(la[i])], [float(lo[j + 1]), float(la[i])],
                    [float(lo[j + 1]), float(la[i + 1])], [float(lo[j]), float(la[i + 1])],
                    [float(lo[j]), float(la[i])]]
            feats.append({"type": "Feature", "id": f"{i}-{j}", "properties": {},
                          "geometry": {"type": "Polygon", "coordinates": [ring]}})
    geojson = {"type": "FeatureCollection", "features": feats}
 
    # Sự kiện lịch sử tĩnh
    base_risk = risk_from(slope, rain, lc, 1.0).ravel()
    p = base_risk ** 3
    pick = rng.choice(N * N, size=46, replace=False, p=p / p.sum())
    ei, ej = np.divmod(pick, N)
    days = rng.integers(0, 365 * 6, size=len(pick))
    
    causes = ["Mưa lớn kéo dài", "Bão số 9", "Suy yếu địa chất", "Hoạt động nhân tạo"]
    events = pd.DataFrame({
        "id": [f"EV-{i:03d}" for i in range(len(pick))],
        "lat": lat[ei],
        "lon": lon[ej],
        "elev": elev[ei, ej],
        "date": [(datetime(2019, 1, 1) + timedelta(days=int(d))).strftime("%Y-%m-%d") for d in days],
        "cause": [rng.choice(causes) for _ in range(len(pick))],
        "damage": rng.integers(10, 500, size=len(pick))
    })
    
    # Metadata
    metadata = {
        "last_updated": (datetime.now() - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
        "model_run": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return dict(lat=lat, lon=lon, elev=elev, slope=slope, rain=rain, lc=lc,
                geojson=geojson, cell_ids=[f["id"] for f in feats], events=events, metadata=metadata)

def _idx(lat: float, lon: float) -> tuple[int, int]:
    i = int(round((lat - LAT0) / (LAT1 - LAT0) * (N - 1)))
    j = int(round((lon - LON0) / (LON1 - LON0) * (N - 1)))
    return min(max(i, 0), N - 1), min(max(j, 0), N - 1)

def level_of(score: float, thr: tuple[float, float]) -> str:
    return "Cao" if score >= thr[1] else ("Trung bình" if score >= thr[0] else "Thấp")

def compute(base: dict, scale: float, thr: tuple[float, float]):
    """Chạy đánh giá mô hình. Input đầu vào là rain * scale. Không thêm nhiễu ngẫu nhiên."""
    risk = risk_from(base["slope"], base["rain"], base["lc"], scale)
    cells = risk.reshape(NC, BLOCK, NC, BLOCK).mean(axis=(1, 3)).ravel()
    rows = []
    for code, name, lat, lon, cover in AREAS:
        i, j = _idx(lat, lon)
        w = (slice(max(i - 2, 0), i + 3), slice(max(j - 2, 0), j + 3))
        score = float(risk[w].mean())
        # Lưu ý: "Risk Score" - Điểm rủi ro (không gọi là xác suất)
        rows.append(dict(code=code, name=name, lat=lat, lon=lon, cover=cover,
                         score=score, slope=float(base["slope"][w].mean()),
                         rain=float(base["rain"][w].mean() * scale), elev=float(base["elev"][w].mean())))
    df = pd.DataFrame(rows)
    df["level"] = df["score"].map(lambda s: level_of(s, thr))
    return risk, cells, df
