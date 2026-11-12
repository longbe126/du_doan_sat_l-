"""Bản đồ 2D (phân vùng nguy cơ) và địa hình 3D tràn toàn màn hình cho trung tâm giám sát."""
from __future__ import annotations

import base64
import io

import numpy as np
import plotly.graph_objects as go

from .theme import C, RISK_COLOR, base_layout

BASEMAPS = ["Bản đồ", "Vệ tinh", "Địa hình"]

_ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
_OTM = "https://a.tile.opentopomap.org/{z}/{x}/{y}.png"

_HAS_MAP_V7 = hasattr(go, "Scattermap") and hasattr(go, "Choroplethmap")
_ScatterMap = getattr(go, "Scattermap", getattr(go, "Scattermapbox", None))
_ChoroplethMap = getattr(go, "Choroplethmap", getattr(go, "Choroplethmapbox", None))
_MAP_LAYOUT_KEY = "map" if _HAS_MAP_V7 else "mapbox"


def _smooth(a: np.ndarray, passes: int = 2) -> np.ndarray:
    for _ in range(passes):
        p = np.pad(a, 1, mode="edge")
        a = sum(p[i : i + a.shape[0], j : j + a.shape[1]] for i in range(3) for j in range(3)) / 9
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
    gy, gx = np.gradient(e * 2.2, y_m, x_m)
    nx, ny, nz = -gx, -gy, np.ones_like(gx)
    norm = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    az, alt = np.radians(315), np.radians(42)
    light = (np.sin(az) * np.cos(alt), np.cos(az) * np.cos(alt), np.sin(alt))
    shade = np.clip((nx * light[0] + ny * light[1] + nz * light[2]) / norm, 0, 1)
    lo_, hi_ = np.percentile(shade, [2, 98])
    shade = np.clip((shade - lo_) / max(hi_ - lo_, 1e-6), 0, 1)
    height = (e - e.min()) / max(e.max() - e.min(), 1e-6)
    k = 0.75 * shade + 0.25 * height
    dark, bright = np.array([10, 14, 18]), np.array([68, 82, 96])
    rgb = (dark + (bright - dark) * k[..., None]).astype(np.uint8)
    if lat[0] < lat[-1]:
        rgb = rgb[::-1]
    img = Image.fromarray(rgb).resize((rgb.shape[1] * 6, rgb.shape[0] * 6), Image.BICUBIC)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    _HILLSHADE_CACHE[key] = uri
    return uri


def _map_scale(thr):
    lo, hi = thr
    a, b, c = "rgba(76,195,138,0.10)", "rgba(229,169,60,0.38)", "rgba(232,93,86,0.65)"
    return [[0.0, a], [lo, a], [lo, b], [hi, b], [hi, c], [1.0, c]]


def _ramp_stops(thr):
    """Thang màu địa hình trầm tự nhiên: đen khói ở chân địa hình -> lục rêu trầm -> vàng đất -> cam trầm -> đỏ sẫm."""
    lo, hi = thr
    return [
        (0.0, "#121c1b"),
        (lo * 0.55, "#26443c"),
        (lo, "#68874d"),
        ((lo + hi) / 2, "#c28738"),
        (hi, "#c65039"),
        (1.0, "#a62624"),
    ]


def _terrain_scale(thr):
    return [[p, c] for p, c in _ramp_stops(thr)]


def _cell_scale(thr):
    """Ô lưới chỉ tô nhẹ từ mức Trung bình trở lên, mức Thấp để trong suốt cho nhìn thấy bản đồ nhiệt bên dưới."""
    lo, hi = thr
    z, a, r = "rgba(0,0,0,0)", "rgba(229,169,60,0.20)", "rgba(232,93,86,0.32)"
    return [[0.0, z], [lo, z], [lo, a], [hi, a], [hi, r], [1.0, r]]


_HEAT_CACHE: dict = {}


def risk_heat_uri(base: dict, risk, thr) -> str:
    """Bản đồ nhiệt liên tục dựng từ toàn bộ lưới điểm nguy cơ (không gộp thành ô)."""
    from PIL import Image

    lat = np.asarray(base["lat"], float)
    r = np.clip(_smooth(np.asarray(risk, float), 1), 0, 1)
    key = (r.shape, round(float(r.sum()), 4), tuple(np.round(thr, 3)))
    if key in _HEAT_CACHE:
        return _HEAT_CACHE[key]
    stops = _ramp_stops(thr)
    xs = [s[0] for s in stops]
    cols = np.array([[int(c[i : i + 2], 16) for i in (1, 3, 5)] for _, c in stops], float)
    rgb = np.stack([np.interp(r, xs, cols[:, k]) for k in range(3)], -1).astype(np.uint8)
    if lat[0] < lat[-1]:
        rgb = rgb[::-1]
    img = Image.fromarray(rgb).resize((rgb.shape[1] * 8, rgb.shape[0] * 8), Image.BICUBIC)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    uri = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    if len(_HEAT_CACHE) > 60:
        _HEAT_CACHE.clear()
    _HEAT_CACHE[key] = uri
    return uri


def _resolve_event_locations(ev, df):
    """Lấy danh sách nhãn hiển thị và tên xã gốc gần nhất cho các sự kiện lịch sử."""
    locs, raw_names = [], []
    for _, r in ev.iterrows():
        dists = [np.hypot(r["lat"] - a["lat"], r["lon"] - a["lon"]) for _, a in df.iterrows()]
        m_idx = int(np.argmin(dists))
        c_name = str(df.iloc[m_idx]["name"])
        distr = "Nam Trà My" if "Trà" in c_name else "Phước Sơn"
        locs.append(f"Xã {c_name} ({distr})")
        raw_names.append(c_name)
    return locs, raw_names


# ----------------------------------------------------------------------------
# Bản đồ 2D (Tràn toàn màn hình)
# ----------------------------------------------------------------------------
def render_2d_workspace(
    base,
    risk_cells,
    df,
    thr,
    map_style="Bản đồ",
    show_risk_grid=True,
    show_hist=True,
    show_areas=True,
    height=1080,
    selected_area: str | None = None,
    risk_field=None,
    zoom: float = 9.3,
):
    lat, lon = np.asarray(base["lat"], float), np.asarray(base["lon"], float)
    west, east, south, north = lon.min(), lon.max(), lat.min(), lat.max()
    fig = go.Figure()

    if show_risk_grid:
        fig.add_trace(
            _ChoroplethMap(
                geojson=base["geojson"],
                locations=base["cell_ids"],
                z=risk_cells,
                colorscale=_cell_scale(thr) if risk_field is not None else _map_scale(thr),
                zmin=0,
                zmax=1,
                showscale=False,
                marker_opacity=1,
                marker_line_width=0.3,
                marker_line_color="rgba(255,255,255,0.12)",
                hovertemplate="Điểm nguy cơ của ô: %{z:.2f}<extra></extra>",
            )
        )

    if show_hist:
        ev = base["events"]
        locs, raw_names = _resolve_event_locations(ev, df)

        fig.add_trace(
            _ScatterMap(
                lat=ev["lat"],
                lon=ev["lon"],
                mode="markers",
                name="hist-events",
                marker=dict(size=7.5, color="#d8dee9", opacity=0.9),
                customdata=np.column_stack([
                    ev["id"],
                    locs,
                    ev["cause"],
                    ev["date"],
                    ev["elev"].round().astype(int),
                    raw_names,
                ]),
                hovertemplate=(
                    "<b>Sạt lở lịch sử [%{customdata[0]}]</b><br>"
                    "Địa điểm: %{customdata[1]}<br>"
                    "Nguyên nhân: %{customdata[2]}<br>"
                    "Ngày xảy ra: %{customdata[3]}<br>"
                    "Độ cao: %{customdata[4]} m<extra></extra>"
                ),
            )
        )

    if show_areas:
        fig.add_trace(
            _ScatterMap(
                lat=df["lat"],
                lon=df["lon"],
                mode="markers",
                marker=dict(size=20, color=C["bg"]),
                customdata=df[["score", "rain", "slope", "elev", "code", "name"]],
                hoverinfo="skip",
            )
        )
        for row in df.itertuples(index=False):
            fig.add_trace(
                _ScatterMap(
                    lat=[row.lat],
                    lon=[row.lon],
                    mode="markers+text",
                    name="area-markers",
                    marker=dict(size=13, color=str(RISK_COLOR[row.level])),
                    text=[row.name],
                    textposition="top center",
                    textfont=dict(size=11, color="#eceef2"),
                    customdata=[[row.score, row.rain, row.slope, row.elev, row.code, row.name]],
                    hovertemplate=(
                        "<b>%{text}</b> [%{customdata[4]}]<br>"
                        "Điểm nguy cơ: <b>%{customdata[0]:.3f}</b><br>"
                        "Mưa 24 giờ: %{customdata[1]:.1f} mm<br>"
                        "Độ dốc: %{customdata[2]:.1f}°<br>"
                        "Độ cao: %{customdata[3]:.0f} m<extra></extra>"
                    ),
                )
            )

        if selected_area and selected_area in df["name"].values:
            sel = df[df["name"] == selected_area].iloc[0]
            sel_custom = [[sel["score"], sel["rain"], sel["slope"], sel["elev"], sel["code"], sel["name"]]]
            fig.add_trace(
                _ScatterMap(
                    lat=[sel["lat"]],
                    lon=[sel["lon"]],
                    mode="markers",
                    marker=dict(size=32, color="rgba(200, 220, 112, 0.28)"),
                    customdata=sel_custom,
                    hoverinfo="skip",
                )
            )
            fig.add_trace(
                _ScatterMap(
                    lat=[sel["lat"]],
                    lon=[sel["lon"]],
                    mode="markers",
                    marker=dict(size=21, color="rgba(200, 220, 112, 0.78)"),
                    customdata=sel_custom,
                    hoverinfo="skip",
                )
            )
            fig.add_trace(
                _ScatterMap(
                    lat=[sel["lat"]],
                    lon=[sel["lon"]],
                    mode="markers",
                    marker=dict(size=13, color=RISK_COLOR[sel["level"]]),
                    customdata=sel_custom,
                    hoverinfo="skip",
                )
            )

    layers = []
    style = "white-bg"
    shade_opacity = 0.0
    if map_style == "Bản đồ":
        style, shade_opacity = "carto-darkmatter", 0.12
    elif map_style == "Vệ tinh":
        layers.append(
            dict(
                sourcetype="raster",
                source=[_ESRI],
                below="traces",
                opacity=1,
                sourceattribution="Esri, Maxar, Earthstar Geographics",
            )
        )
    elif map_style == "Địa hình":
        layers.append(
            dict(
                sourcetype="raster",
                source=[_OTM],
                below="traces",
                opacity=1,
                sourceattribution="© OpenTopoMap (CC-BY-SA), © OpenStreetMap",
            )
        )
    else:
        style, shade_opacity = "carto-positron", 0.18

    if shade_opacity > 0:
        layers.append(
            dict(
                sourcetype="image",
                source=hillshade_uri(base),
                below="traces",
                opacity=shade_opacity,
                coordinates=[[west, north], [east, north], [east, south], [west, south]],
            )
        )

    if show_risk_grid and risk_field is not None:
        layers.append(
            dict(
                sourcetype="image",
                source=risk_heat_uri(base, risk_field, thr),
                below="traces",
                opacity=0.68,
                coordinates=[[west, north], [east, north], [east, south], [west, south]],
            )
        )

    lay = base_layout(height)
    lay["margin"] = dict(l=0, r=0, t=0, b=0)
    fig.update_layout(**lay, showlegend=False, clickmode="event+select")
    map_cfg = dict(
        style=style,
        zoom=zoom,
        layers=layers,
        center=dict(
            lat=float((south + north) / 2 - 0.012),
            lon=float((west + east) / 2),
        ),
    )
    fig.update_layout(**{_MAP_LAYOUT_KEY: map_cfg})
    return fig


# ----------------------------------------------------------------------------
# Địa hình 3D (Tràn rộng toàn màn hình, làm mềm chân biên địa hình hòa vào nền tối)
# ----------------------------------------------------------------------------
def render_3d_terrain(
    base,
    risk,
    df,
    thr,
    show_hist=True,
    show_areas=True,
    height=1080,
    selected_area: str | None = None,
):
    lat, lon = np.asarray(base["lat"], float), np.asarray(base["lon"], float)
    elev_raw = _smooth(np.asarray(base["elev"], float), 4)
    risk_raw = _smooth(np.asarray(risk, float), 3) if np.shape(risk) == elev_raw.shape else np.asarray(risk, float)

    # Làm mềm nhẹ vành đai ngoài cùng của lưới DEM để chân địa hình hòa tự nhiên vào nền tối, không tạo cảm giác khối hộp cứng
    ny, nx = elev_raw.shape
    wy = np.sin(np.linspace(0, np.pi, ny)) ** 0.28
    wx = np.sin(np.linspace(0, np.pi, nx)) ** 0.28
    feather = np.outer(wy, wx)
    base_floor = float(elev_raw.min()) * 0.65
    elev = base_floor + (elev_raw - base_floor) * (0.35 + 0.65 * feather)
    risk_s = risk_raw * (0.25 + 0.75 * feather)

    fig = go.Figure(
        go.Surface(
            x=lon,
            y=lat,
            z=elev,
            surfacecolor=risk_s,
            cmin=0,
            cmax=1,
            colorscale=_terrain_scale(thr),
            showscale=False,
            lighting=dict(ambient=0.65, diffuse=0.84, roughness=0.72, specular=0.06, fresnel=0.12),
            contours=dict(
                z=dict(
                    show=True,
                    start=float(base_floor + 80),
                    end=float(np.ceil(elev.max() / 100) * 100),
                    size=240,
                    color="rgba(255,255,255,0.08)",
                    width=1,
                )
            ),
            hovertemplate=(
                "Kinh độ %{x:.3f}°Đ<br>Vĩ độ %{y:.3f}°B<br>Độ cao %{z:.0f} m<br>"
                "Điểm nguy cơ %{surfacecolor:.2f}<extra></extra>"
            ),
        )
    )

    if show_hist:
        ev = base["events"]
        locs, raw_names = _resolve_event_locations(ev, df)

        fig.add_trace(
            go.Scatter3d(
                x=ev["lon"],
                y=ev["lat"],
                z=_sample(base, elev, ev["lat"], ev["lon"]) + 24,
                mode="markers",
                name="hist-events-3d",
                marker=dict(size=4.5, color="rgba(235,238,245,0.85)", opacity=0.92),
                customdata=np.column_stack([
                    raw_names,
                    ev["id"],
                    locs,
                    ev["cause"],
                    ev["date"],
                    ev["elev"].round().astype(int),
                ]),
                hovertemplate=(
                    "<b>Sạt lở lịch sử [%{customdata[1]}]</b><br>"
                    "Địa điểm: %{customdata[2]}<br>"
                    "Nguyên nhân: %{customdata[3]}<br>"
                    "Ngày xảy ra: %{customdata[4]}<br>"
                    "Độ cao: %{customdata[5]} m<extra></extra>"
                ),
            )
        )

    if show_areas:
        zs = _sample(base, elev, df["lat"], df["lon"]) + 40
        fig.add_trace(
            go.Scatter3d(
                x=df["lon"],
                y=df["lat"],
                z=zs,
                mode="markers+text",
                name="area-markers-3d",
                text=df["name"],
                textposition="top center",
                textfont=dict(size=10.5, color="rgba(241,245,249,0.92)", family="Be Vietnam Pro, sans-serif"),
                marker=dict(
                    size=6,
                    color=[RISK_COLOR[l] for l in df["level"]],
                    line=dict(color="rgba(255,255,255,0.85)", width=1.2),
                ),
                customdata=np.column_stack([
                    df["name"],
                    df["code"],
                    df["score"],
                    df["rain"],
                    df["slope"],
                    df["elev"],
                    df["cover"],
                    df["level"],
                ]),
                hovertemplate=(
                    "<b>%{customdata[0]}</b> [%{customdata[1]}]<br>"
                    "Mức nguy cơ: <b>%{customdata[7]}</b><br>"
                    "Điểm nguy cơ: %{customdata[2]:.3f}<br>"
                    "Mưa 24 giờ: %{customdata[3]:.1f} mm<br>"
                    "Độ dốc: %{customdata[4]:.1f}°<br>"
                    "Độ cao: %{customdata[5]:.0f} m<br>"
                    "Lớp phủ: %{customdata[6]}<extra></extra>"
                ),
            )
        )

        hx, hy, hz = [], [], []
        head_x, head_y, head_z, head_names = [], [], [], []
        for r, z0 in zip(df.itertuples(), zs):
            if r.level == "Cao":
                hx += [r.lon, r.lon, None]
                hy += [r.lat, r.lat, None]
                hz += [z0, z0 + 480, None]
                head_x.append(r.lon)
                head_y.append(r.lat)
                head_z.append(z0 + 480)
                head_names.append([r.name])
        if hx:
            fig.add_trace(
                go.Scatter3d(
                    x=hx,
                    y=hy,
                    z=hz,
                    mode="lines",
                    line=dict(color="#e85d56", width=4.5),
                    hoverinfo="skip",
                )
            )
            fig.add_trace(
                go.Scatter3d(
                    x=head_x,
                    y=head_y,
                    z=head_z,
                    mode="markers",
                    customdata=head_names,
                    marker=dict(size=6.5, color="#e85d56", line=dict(color="#ffffff", width=1.2)),
                    hoverinfo="skip",
                )
            )

        if selected_area and selected_area in df["name"].values:
            sel = df[df["name"] == selected_area].iloc[0]
            sel_z = float(_sample(base, elev, [sel["lat"]], [sel["lon"]])[0]) + 40
            fig.add_trace(
                go.Scatter3d(
                    x=[sel["lon"], sel["lon"]],
                    y=[sel["lat"], sel["lat"]],
                    z=[sel_z, sel_z + 600],
                    mode="lines+markers",
                    customdata=[[sel["name"]], [sel["name"]]],
                    line=dict(color="#c8dc70", width=6),
                    marker=dict(size=[5.5, 10], color=["#c8dc70", "#ffffff"]),
                    hoverinfo="skip",
                )
            )

    layout_args = base_layout(height)
    layout_args["margin"] = dict(l=0, r=0, t=0, b=0)
    fig.update_layout(
        **layout_args,
        showlegend=False,
        clickmode="event+select",
        dragmode="orbit",
        scene=dict(
            domain=dict(x=[0.0, 1.0], y=[0.0, 1.0]),
            xaxis=dict(visible=False, showgrid=False, zeroline=False, showbackground=False),
            yaxis=dict(visible=False, showgrid=False, zeroline=False, showbackground=False),
            zaxis=dict(visible=False, showgrid=False, zeroline=False, showbackground=False),
            aspectmode="manual",
            aspectratio=dict(x=1.65, y=1.65, z=0.42),
            camera=dict(eye=dict(x=0.96, y=-1.14, z=0.72), center=dict(x=0, y=-0.02, z=-0.06)),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig