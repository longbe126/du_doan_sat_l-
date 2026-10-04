"""Bảng màu, kiểu chữ và hàm tiện ích dùng chung cho toàn bộ giao diện."""
from __future__ import annotations

FONT = "Be Vietnam Pro, system-ui, sans-serif"

C = dict(
    bg="#0b1120",       # nền trang
    panel="#0f172a",    # nền khung
    panel2="#0c1426",   # nền thanh tiêu đề khung
    line="#1e293b",     # đường kẻ mảnh
    line2="#334155",    # đường kẻ nổi
    text="#e2e8f0",
    muted="#8a9bb0",
    accent="#0ea5e9",
    low="#10b981",
    mid="#f59e0b",
    high="#ef4444",
)

# giữ tên cũ để các tệp khác của dự án vẫn import được
RISK_COLOR = {"Cao": C["high"], "Trung bình": C["mid"], "Thấp": C["low"]}

HOURS = 24  # số giờ của kịch bản mô phỏng


def vn(x: float, d: int = 2) -> str:
    """Định dạng số theo kiểu Việt Nam (dấu phẩy thập phân)."""
    return f"{x:.{d}f}".replace(".", ",")


def hh(t: int) -> str:
    return f"{t:02d}:00"


def level_of(score: float, thr) -> str:
    return "Cao" if score >= thr[1] else ("Trung bình" if score >= thr[0] else "Thấp")


def base_layout(height: int) -> dict:
    return dict(
        height=height, margin=dict(l=4, r=4, t=6, b=4),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=C["text"], size=12), separators=",.",
    )