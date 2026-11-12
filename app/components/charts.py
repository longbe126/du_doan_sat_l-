"""Các biểu đồ thống kê của trung tâm giám sát (đồng bộ phong cách Dark Frosted Glass)."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from .theme import C, RISK_COLOR, HOURS, base_layout


def _hour_axis(fig, step: int = 4):
    fig.update_xaxes(
        tickvals=list(range(0, HOURS + 1, step)),
        ticktext=[f"{h:02d}h" for h in range(0, HOURS + 1, step)],
        showgrid=False,
        linecolor=C["line2"],
        tickfont=dict(color=C["muted"], size=10),
    )


def fig_gauge(value: float, level: str, thr) -> go.Figure:
    lo, hi = thr
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number=dict(
                valueformat=".2f",
                font=dict(size=34, color=C["text"], family="Be Vietnam Pro, sans-serif"),
            ),
            gauge=dict(
                axis=dict(
                    range=[0, 1],
                    tickvals=[0, lo, hi, 1],
                    ticktext=["0,00", f"{lo:.2f}".replace(".", ","), f"{hi:.2f}".replace(".", ","), "1,00"],
                    tickcolor="rgba(255,255,255,0.22)",
                    tickwidth=1,
                    tickfont=dict(size=10, color=C["muted"]),
                ),
                bar=dict(color=RISK_COLOR[level], thickness=0.28),
                bgcolor="rgba(255,255,255,0.03)",
                borderwidth=0,
                steps=[
                    dict(range=[0, lo], color="rgba(76,195,138,0.14)"),
                    dict(range=[lo, hi], color="rgba(229,169,60,0.16)"),
                    dict(range=[hi, 1], color="rgba(232,93,86,0.20)"),
                ],
            ),
        )
    )
    lay = base_layout(185)
    # Tăng lề trên và dưới để các nhãn mốc 0,00 / 0,25 / 0,45 / 1,00 không bao giờ bị cắt
    lay["margin"] = dict(l=38, r=38, t=32, b=22)
    fig.update_layout(**lay)
    return fig


def fig_timeline(counts: np.ndarray, t: int, n_cells: int) -> go.Figure:
    """Số ô lưới theo từng mức nguy cơ trong suốt kịch bản; đường sáng là giờ đang xem."""
    xs = list(range(HOURS + 1))
    fig = go.Figure()
    for k, (name, col) in enumerate([
        ("Thấp", "rgba(76,195,138,0.38)"),
        ("Trung bình", "rgba(229,169,60,0.58)"),
        ("Cao", "rgba(232,93,86,0.78)"),
    ]):
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=counts[:, k],
                mode="lines",
                stackgroup="s",
                line=dict(width=0.5, color="rgba(255,255,255,0.12)"),
                fillcolor=col,
                name=name,
                hovertemplate=f"{name}: %{{y:.0f}} ô<extra></extra>",
            )
        )
    fig.add_vline(x=t, line=dict(color=C["accent"], width=1.8, dash="dot"))
    lay = base_layout(135)
    lay["margin"] = dict(l=16, r=16, t=12, b=24)
    fig.update_layout(**lay, showlegend=False, hovermode="x unified")
    _hour_axis(fig, 2)
    fig.update_xaxes(range=[0, HOURS])
    fig.update_yaxes(showgrid=False, showticklabels=False, range=[0, n_cells])
    return fig


def fig_trend(series: np.ndarray, t: int, thr, level: str) -> go.Figure:
    xs = list(range(HOURS + 1))
    fig = go.Figure()
    for y0, y1, col in [(0, thr[0], C["low"]), (thr[0], thr[1], C["mid"]), (thr[1], 1, C["high"])]:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=col, opacity=0.07, line_width=0)
    fig.add_hline(y=thr[1], line=dict(color="rgba(232,93,86,0.35)", width=1, dash="dot"))
    fig.add_hline(y=thr[0], line=dict(color="rgba(229,169,60,0.30)", width=1, dash="dot"))
    fig.add_trace(
        go.Scatter(
            x=xs[: t + 1],
            y=series[: t + 1],
            mode="lines",
            line=dict(color=C["accent"], width=2.2),
            hovertemplate="%{x}h: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=xs[t:],
            y=series[t:],
            mode="lines",
            line=dict(color=C["accent"], width=1.4, dash="dot"),
            opacity=0.4,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[t],
            y=[series[t]],
            mode="markers",
            hoverinfo="skip",
            marker=dict(size=9, color=RISK_COLOR[level], line=dict(color="#ffffff", width=1.8)),
        )
    )
    lay = base_layout(185)
    lay["margin"] = dict(l=32, r=16, t=14, b=24)
    fig.update_layout(**lay, showlegend=False)
    fig.update_yaxes(
        range=[0, 1],
        tickvals=[0, 0.5, 1],
        gridcolor=C["line"],
        zeroline=False,
        tickfont=dict(color=C["muted"], size=10),
    )
    _hour_axis(fig)
    return fig


def fig_rain(series: np.ndarray, t: int) -> go.Figure:
    xs = list(range(HOURS + 1))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=xs[: t + 1],
            y=series[: t + 1],
            mode="lines",
            fill="tozeroy",
            line=dict(color="#c8dc70", width=2),
            fillcolor="rgba(200,220,112,0.12)",
            hovertemplate="%{x}h: %{y:.0f} mm<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=xs[t:],
            y=series[t:],
            mode="lines",
            line=dict(color="#c8dc70", width=1.4, dash="dot"),
            opacity=0.4,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[t],
            y=[series[t]],
            mode="markers",
            hoverinfo="skip",
            marker=dict(size=8, color=C["text"], line=dict(color=C["bg"], width=2)),
        )
    )
    lay = base_layout(180)
    lay["margin"] = dict(l=36, r=16, t=14, b=24)
    fig.update_layout(**lay, showlegend=False)
    fig.update_yaxes(
        gridcolor=C["line"],
        zeroline=False,
        tickfont=dict(color=C["muted"], size=10),
        rangemode="tozero",
    )
    _hour_axis(fig)
    return fig


def fig_hist(cells: np.ndarray, thr) -> go.Figure:
    lo, hi = thr
    edges = np.linspace(0, 1, 21)
    cnt, _ = np.histogram(cells, bins=edges)
    mids = (edges[:-1] + edges[1:]) / 2
    cols = [C["low"] if m < lo else (C["mid"] if m < hi else C["high"]) for m in mids]
    fig = go.Figure(
        go.Bar(
            x=mids,
            y=cnt,
            marker_color=cols,
            marker_opacity=0.82,
            marker_line_width=0,
            width=0.042,
            hovertemplate="Điểm %{x:.2f}: %{y} ô<extra></extra>",
        )
    )
    lay = base_layout(180)
    lay["margin"] = dict(l=32, r=16, t=14, b=24)
    fig.update_layout(**lay, showlegend=False)
    fig.update_xaxes(
        range=[0, 1],
        tickvals=[0, 0.25, 0.5, 0.75, 1],
        showgrid=False,
        linecolor=C["line2"],
        tickfont=dict(color=C["muted"], size=10),
    )
    fig.update_yaxes(gridcolor=C["line"], zeroline=False, tickfont=dict(color=C["muted"], size=10))
    return fig