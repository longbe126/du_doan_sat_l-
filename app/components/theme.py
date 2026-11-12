"""Bảng màu, kiểu chữ và hàm tiện ích dùng chung cho toàn bộ giao diện Dark Frosted Glass."""
from __future__ import annotations

FONT = "Be Vietnam Pro, system-ui, sans-serif"

C = dict(
    bg="#08090c",       # nền trang đen khói sâu
    panel="#14161b",    # nền khung kính
    panel2="#101217",   # nền thanh tiêu đề khung
    line="rgba(255,255,255,0.06)",     # đường kẻ mảnh
    line2="rgba(255,255,255,0.12)",    # đường kẻ nổi
    text="#eceef2",
    muted="#7e828c",
    accent="#c8dc70",   # xanh lime trầm sang trọng theo ảnh mẫu
    low="#4cc38a",      # xanh lục trầm tự nhiên
    mid="#e5a93c",      # vàng hổ phách trầm
    high="#e85d56",     # đỏ san hô trầm
)

RISK_COLOR = {"Cao": C["high"], "Trung bình": C["mid"], "Thấp": C["low"]}

HOURS = 24  # số giờ của kịch bản mô phỏng


def vn(x: float, d: int = 2) -> str:
    """Định dạng số theo kiểu Việt Nam (dấu phẩy thập phân)."""
    return f"{x:.{d}f}".replace(".", ",")


def hh(t: int) -> str:
    return f"{t:02d}:00"


def level_of(score: float, thr) -> str:
    return "Cao" if score >= thr[1] else ("Trung bình" if score >= thr[0] else "Thấp")


def base_layout(height: int | None) -> dict:
    return dict(
        height=height,
        margin=dict(l=8, r=8, t=10, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=C["text"], size=11),
        separators=",.",
    )