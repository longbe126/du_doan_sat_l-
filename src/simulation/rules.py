"""Quy luật MÔ PHỎNG dùng chung cho bộ dữ liệu huấn luyện và bản đồ trong giao diện.

Cả hai nơi cùng dùng một "thế giới mô phỏng" nên mô hình huấn luyện trên bảng dữ liệu
có thể chạy trực tiếp trên các ô lưới của bản đồ. Đây KHÔNG phải công thức địa chất
đã kiểm chứng.
"""
from __future__ import annotations

import numpy as np

# Năm đặc trưng đầu vào của mô hình (đúng tên cột trong bộ dữ liệu huấn luyện)
FEATURES = ["slope_deg", "elevation_m", "rainfall_mm", "soil_moisture", "landcover"]

LANDCOVER_CLASSES = ["forest", "agriculture", "bare", "urban"]
LANDCOVER_PRIOR = [0.55, 0.25, 0.10, 0.10]

# Độ lệch chuẩn của nhiễu thêm vào khi sinh nhãn: nhiễu này quyết định "trần" độ chính xác
NOISE_SD = 0.8


def deterministic_score(slope, elevation, rainfall, soil_moisture, landcover):
    """Điểm logit không có nhiễu. Thứ tự phép cộng giữ nguyên để dữ liệu sinh ra không đổi."""
    landcover = np.asarray(landcover)
    return (
        -4.0
        + 0.075 * slope
        + 0.006 * rainfall
        + 1.2 * soil_moisture
        + 0.0002 * elevation
        + 0.8 * (landcover == "bare")
        + 0.25 * (landcover == "agriculture")
        - 0.3 * (landcover == "forest")
    )


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def true_probability(slope, elevation, rainfall, soil_moisture, landcover):
    """Xác suất sạt lở kỳ vọng trong thế giới mô phỏng (đã lấy trung bình theo nhiễu)."""
    z = deterministic_score(slope, elevation, rainfall, soil_moisture, landcover)
    return sigmoid(z / np.sqrt(1.0 + np.pi * NOISE_SD ** 2 / 8.0))
