"""Bản đồ 2D (phân vùng nguy cơ) và địa hình 3D cho trung tâm giám sát."""
from __future__ import annotations

import base64
import io

import numpy as np
import plotly.graph_objects as go

from .theme import C, RISK_COLOR, base_layout  # RISK_COLOR giữ lại để main.py cũ vẫn import được

BASEMAPS = ["Tối", "Vệ tinh", "Địa hình", "Ngoại tuyến"]

_ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
_OTM = "https://a.tile.opentopomap.org/{z}/{x}/{y}.png"


# ----------------------------------------------------------------------------
# Hàm phụ
# ----------------------------------------------------------------------------
def _smooth(a: np.ndarray, passes: int = 2) -> np.ndarray:
    for _ in range(passes):
        p = np.pad(a, 1, mode="edge")
        a = sum(p[i:i + a.shape[0], j:j + a.shape[1]] for i in range(3) for j in range(3)) / 9
    return a


def _nearest(axis: np.ndarray, values) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    return np.abs(axis[None, :] - values[:, None]).argmin(axis=1)


def _sample(base: dict, arr: np.ndarray, lats, lons) -> np.ndarray:
    """Lấy giá trị của lưới arr (hàng theo vĩ độ, cột theo kinh độ) tại các điểm gần nhất."""
    i = _nearest(np.asarray(base["lat"]), lats)
    j = _nearest(np.asarray(base["lon"]), lons)
    return arr[i, j]


_HILLSHADE_CACHE: dict = {}


def hillshade_uri(base: dict) -> str:
    """Ảnh đổ bóng địa hình dựng từ chính dữ liệu độ cao, dùng làm nền bản đồ 2D."""
    from PIL import Image

    lat, lon, elev = np.asarray(base["lat"], float), np.asarray(base["lon"], float), np.asarray(base["elev"], float)
    key = (elev.shape, round(float(elev.sum()), 3), float(lat[0]), float(lon[0]))
    if key in _HILLSHADE_CACHE:
        return _HILLSHADE_CACHE[key]

    e = _smooth(elev, 2)
    y_m = (lat - lat[0]) * 111_000.0
    x_m = (lon - lon[0]) * 111_000.0 * np.cos(np.radians(lat.mean()))
    gy, gx = np.gradient(e * 2.2, y_m, x_m)  # gy: hướng Bắc, gx: hướng Đông
    nx, ny, nz = -gx, -gy, np.ones_like(gx)
    norm = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    az, alt = np.radians(315), np.radians(42)
    light = (np.sin(az) * np.cos(alt), np.cos(az) * np.cos(alt), np.sin(alt))
    shade = np.clip((nx * light[0] + ny * light[1] + nz * light[2]) / norm, 0, 1)
    lo_, hi_ = np.percentile(shade, [2, 98])
    shade = np.clip((shade - lo_) / max(hi_ - lo_, 1e-6), 0, 1)
    height = (e - e.min()) / max(e.max() - e.min(), 1e-6)
    k = 0.75 * shade + 0.25 * height
    dark, bright = np.array([9, 20, 30]), np.array([84, 112, 130])
    rgb = (dark + (bright - dark) * k[..., None]).astype(np.uint8)
    if lat[0] < lat[-1]:      # hàng 0 là phía Nam; ảnh cần phía Bắc ở trên cùng
        rgb = rgb[::-1]
    img = Image.fromarray(rgb).resize((rgb.shape[1] * 6, rgb.shape[0] * 6), Image.BICUBIC)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    _HILLSHADE_CACHE[key] = uri
    return uri


def _map_scale(thr):
    lo, hi = thr
    a, b, c = "rgba(16,185,129,0.10)", "rgba(245,158,11,0.42)", "rgba(239,68,68,0.70)"
    return [[0.0, a], [lo, a], [lo, b], [hi, b], [hi, c], [1.0, c]]


def _terrain_scale(thr):
    lo, hi = thr
    a, b, c = "#2E6B58", "#C6922E", "#C83228"
    return [[0.0, a], [lo, a], [lo, b], [hi, b], [hi, c], [1.0, c]]


# ----------------------------------------------------------------------------
# Bản đồ 2D
# ----------------------------------------------------------------------------
def render_2d_workspace(base, risk_cells, df, thr, map_style="Tối",
                        show_risk_grid=True, show_hist=True, show_areas=True, height=600,
                        selected_area: str | None = None):
    lat, lon = np.asarray(base["lat"], float), np.asarray(base["lon"], float)
    west, east, south, north = lon.min(), lon.max(), lat.min(), lat.max()
    fig = go.Figure()

    if show_risk_grid:
        fig.add_trace(go.Choroplethmap(
            geojson=base["geojson"], locations=base["cell_ids"], z=risk_cells,
            colorscale=_map_scale(thr), zmin=0, zmax=1, showscale=False,
            marker_opacity=1, marker_line_width=0.3, marker_line_color="rgba(160,190,210,0.18)",
            hovertemplate="Điểm nguy cơ của ô: %{z:.2f}<extra></extra>"))

    if show_hist:
        ev = base["events"]
        fig.add_trace(go.Scattermap(
            lat=ev["lat"], lon=ev["lon"], mode="markers",
            marker=dict(size=5, color="#c9d6df", opacity=0.9),
            text=(ev["id"].astype(str) + "<br>" + ev["date"].astype(str) + "<br>" + ev["cause"].astype(str)),
            hovertemplate="<b>Sạt lở lịch sử (mô phỏng)</b><br>%{text}<extra></extra>"))

    if show_areas:
        fig.add_trace(go.Scattermap(
            lat=df["lat"], lon=df["lon"], mode="markers",
            marker=dict(size=21, color=C["bg"]),
            customdata=df[["score", "rain", "slope", "elev", "code", "name"]],
            hoverinfo="skip"
        ))
        fig.add_trace(go.Scattermap(
            lat=df["lat"], lon=df["lon"], mode="markers+text",
            marker=dict(size=14, color=[RISK_COLOR[l] for l in df["level"]]),
            text=df["name"], textposition="top center", textfont=dict(size=11, color="#e8f0f5"),
            customdata=df[["score", "rain", "slope", "elev", "code", "name"]],
            hovertemplate=("<b>%{text}</b> [%{customdata[4]}]<br>"
                           "Điểm nguy cơ: <b>%{customdata[0]:.3f}</b><br>"
                           "Mưa 24 giờ: %{customdata[1]:.1f} mm<br>"
                           "Độ dốc: %{customdata[2]:.1f}°<br>"
                           "Độ cao: %{customdata[3]:.0f} m<extra></extra>")))

        if selected_area and selected_area in df["name"].values:
            sel = df[df["name"] == selected_area].iloc[0]
            # Vòng hào quang sáng màu cyan nổi bật xung quanh điểm được chọn
            fig.add_trace(go.Scattermap(
                lat=[sel["lat"]], lon=[sel["lon"]], mode="markers",
                marker=dict(size=34, color="rgba(14, 165, 233, 0.40)"),
                hoverinfo="skip"
            ))
            fig.add_trace(go.Scattermap(
                lat=[sel["lat"]], lon=[sel["lon"]], mode="markers",
                marker=dict(size=23, color="rgba(56, 189, 248, 0.85)"),
                hoverinfo="skip"
            ))
            fig.add_trace(go.Scattermap(
                lat=[sel["lat"]], lon=[sel["lon"]], mode="markers",
                marker=dict(size=14, color=RISK_COLOR[sel["level"]]),
                hoverinfo="skip"
            ))

    layers = []
    style = "white-bg"
    shade_opacity = 0.0
    if map_style == "Tối":
        style, shade_opacity = "carto-darkmatter", 0.50
    elif map_style == "Vệ tinh":
        layers.append(dict(sourcetype="raster", source=[_ESRI], below="traces", opacity=1,
                           sourceattribution="Esri, Maxar, Earthstar Geographics"))
    elif map_style == "Địa hình":
        layers.append(dict(sourcetype="raster", source=[_OTM], below="traces", opacity=1,
                           sourceattribution="© OpenTopoMap (CC-BY-SA), © OpenStreetMap"))
    else:  # Ngoại tuyến: không cần mạng, tự phủ nền tối
        big = {"type": "Feature", "properties": {}, "geometry": {"type": "Polygon", "coordinates": [[
            [west - 4, south - 4], [east + 4, south - 4], [east + 4, north + 4], [west - 4, north + 4],
            [west - 4, south - 4]]]}}
        layers.append(dict(sourcetype="geojson", source=big, type="fill", color="#0b1620", opacity=1, below="traces"))
        shade_opacity = 0.95
    if shade_opacity > 0:
        layers.append(dict(sourcetype="image", source=hillshade_uri(base), below="traces", opacity=shade_opacity,
                           coordinates=[[west, north], [east, north], [east, south], [west, south]]))

    fig.update_layout(**base_layout(height), showlegend=False, clickmode="event+select")
    fig.update_layout(map=dict(style=style, zoom=9.7, layers=layers,
                               center=dict(lat=float((south + north) / 2), lon=float((west + east) / 2))))
    return fig


# ----------------------------------------------------------------------------
# Địa hình 3D
# ----------------------------------------------------------------------------
def render_3d_terrain(base, risk, df, thr, show_hist=True, show_areas=True, height=720,
                      selected_area: str | None = None):
    lat, lon = np.asarray(base["lat"], float), np.asarray(base["lon"], float)
    elev = _smooth(np.asarray(base["elev"], float), 4)
    risk_s = _smooth(np.asarray(risk, float), 3) if np.shape(risk) == elev.shape else risk

    fig = go.Figure(go.Surface(
        x=lon, y=lat, z=elev, surfacecolor=risk_s, cmin=0, cmax=1, colorscale=_terrain_scale(thr),
        showscale=False, lighting=dict(ambient=0.65, diffuse=0.85, roughness=0.7, specular=0.08, fresnel=0.15),
        contours=dict(z=dict(show=True, start=0, end=float(np.ceil(elev.max() / 100) * 100), size=250,
                             color="rgba(226,232,240,0.16)", width=1)),
        hovertemplate=("Kinh độ %{x:.3f}<br>Vĩ độ %{y:.3f}<br>Độ cao %{z:.0f} m<br>"
                       "Điểm nguy cơ %{surfacecolor:.2f}<extra></extra>")))

    if show_hist:
        ev = base["events"]
        fig.add_trace(go.Scatter3d(
            x=ev["lon"], y=ev["lat"], z=_sample(base, elev, ev["lat"], ev["lon"]) + 25, mode="markers",
            marker=dict(size=4, color="#ffffff", opacity=0.9),
            text=(ev["id"].astype(str) + "<br>" + ev["date"].astype(str)),
            hovertemplate="<b>Sạt lở lịch sử (mô phỏng)</b><br>%{text}<extra></extra>"))

    if show_areas:
        zs = _sample(base, elev, df["lat"], df["lon"]) + 40
        fig.add_trace(go.Scatter3d(
            x=df["lon"], y=df["lat"], z=zs, mode="markers+text", text=df["name"], textposition="top center",
            textfont=dict(size=11, color="#f1f5f9", family="Be Vietnam Pro, sans-serif"),
            marker=dict(size=6, color=[RISK_COLOR[l] for l in df["level"]], line=dict(color="#ffffff", width=1.5)),
            customdata=df["name"],
            hoverinfo="text"))
        hx, hy, hz = [], [], []
        head_x, head_y, head_z = [], [], []
        for r, z0 in zip(df.itertuples(), zs):
            if r.level == "Cao":
                hx += [r.lon, r.lon, None]
                hy += [r.lat, r.lat, None]
                hz += [z0, z0 + 520, None]
                head_x.append(r.lon)
                head_y.append(r.lat)
                head_z.append(z0 + 520)
        if hx:
            fig.add_trace(go.Scatter3d(x=hx, y=hy, z=hz, mode="lines",
                                       line=dict(color="#ef4444", width=5), hoverinfo="skip"))
            fig.add_trace(go.Scatter3d(x=head_x, y=head_y, z=head_z, mode="markers",
                                       marker=dict(size=7, color="#ef4444", line=dict(color="#ffffff", width=1.5)),
                                       hoverinfo="skip"))

        if selected_area and selected_area in df["name"].values:
            sel = df[df["name"] == selected_area].iloc[0]
            sel_z = float(_sample(base, elev, [sel["lat"]], [sel["lon"]])[0]) + 40
            fig.add_trace(go.Scatter3d(
                x=[sel["lon"], sel["lon"]],
                y=[sel["lat"], sel["lat"]],
                z=[sel_z, sel_z + 650],
                mode="lines+markers",
                line=dict(color="#38bdf8", width=7),
                marker=dict(size=[6, 11], color=["#38bdf8", "#ffffff"]),
                hoverinfo="skip"
            ))

    layout_args = base_layout(height)
    layout_args["margin"] = dict(l=0, r=0, t=0, b=0)
    fig.update_layout(
        **layout_args,
        showlegend=False,
        clickmode="event+select",
        scene=dict(
            xaxis=dict(visible=False, showgrid=False, zeroline=False, showbackground=False),
            yaxis=dict(visible=False, showgrid=False, zeroline=False, showbackground=False),
            zaxis=dict(visible=False, showgrid=False, zeroline=False, showbackground=False),
            aspectmode="manual",
            aspectratio=dict(x=1.35, y=1.35, z=0.38),
            camera=dict(eye=dict(x=1.1, y=-1.35, z=0.8), center=dict(x=0, y=0, z=-0.1)),
            bgcolor="rgba(0,0,0,0)"
        )
    )
    return fig