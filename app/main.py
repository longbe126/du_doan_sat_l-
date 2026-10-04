"""
Trung tâm giám sát nguy cơ sạt lở đất - giao diện Streamlit kiểu phòng điều hành.
Chạy:  streamlit run app/main.py
Không có mạng:  LANDSLIDE_OFFLINE=1 streamlit run app/main.py   (hoặc chọn nền "Ngoại tuyến" ở thanh bên)
"""
from __future__ import annotations

import os
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import streamlit as st

from core.data_engine import build_base, compute, NC
from components.theme import C, RISK_COLOR, HOURS, vn, hh, level_of
from components.map_view import render_2d_workspace, render_3d_terrain, BASEMAPS
from components import charts

st.set_page_config(
    page_title="Trung tâm giám sát nguy cơ sạt lở đất",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_MODE = "Dữ liệu mô phỏng"   # đổi thành nhãn khác khi ghép với dữ liệu thật


# ----------------------------------------------------------------------------
# Giao diện: CSS
# ----------------------------------------------------------------------------
def contour_svg() -> str:
    def blob(cx, cy, radius, phase, squash):
        pts = []
        for k in range(73):
            t = 2 * np.pi * k / 72
            r = radius * (1 + 0.10 * np.sin(3 * t + phase) + 0.06 * np.sin(5 * t + 2 * phase))
            pts.append(f"{cx + r * np.cos(t):.1f},{cy + r * squash * np.sin(t):.1f}")
        return "M" + " L".join(pts) + "Z"

    paths = [blob(520, 40, r, 0.3 + i * 0.07, 0.5) for i, r in enumerate(range(16, 220, 16))]
    paths += [blob(140, 60, r, 1.2 + i * 0.09, 0.5) for i, r in enumerate(range(14, 120, 14))]
    body = "".join(f"<path d='{p}'/>" for p in paths)
    return ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 640 90' preserveAspectRatio='xMidYMid slice'>"
            f"<g fill='none' stroke='white' stroke-opacity='0.06' stroke-width='1'>{body}</g></svg>")


ROOT_VARS = (":root{" + "".join(f"--{k}:{v};" for k, v in C.items())
             + f"--contour:url(\"data:image/svg+xml;utf8,{quote(contour_svg())}\");}}")

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

.stApp, .stApp [data-baseweb], .stApp [data-baseweb] div, .stApp label p,
.stApp [data-testid="stMarkdownContainer"] { font-family: 'Be Vietnam Pro', system-ui, sans-serif; }
.stApp { background: var(--bg); color: var(--text); }
[data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu { display: none !important; }
[data-testid="stHeader"] { background: transparent; height: 0; }
.block-container { max-width: 100%; padding: .6rem 1.1rem 2rem; }
[data-testid="stVerticalBlock"] { gap: .6rem; }
.mono { font-family: 'JetBrains Mono', ui-monospace, Consolas, monospace; font-variant-numeric: tabular-nums; }

[data-testid="stSidebar"] { background: var(--panel2); border-right: 1px solid var(--line); width: 272px !important; }
[data-testid="stSidebarContent"] { padding-top: 1rem; }
.side-h { font-weight: 600; font-size: .9rem; margin: .5rem 0 .15rem; }
.side-note { color: var(--muted); font-size: .78rem; line-height: 1.55; }
.side-rule { border-top: 1px solid var(--line); margin: 1rem 0 .4rem; }

.top { background: var(--panel2) var(--contour) center / cover no-repeat; border: 1px solid var(--line);
       border-radius: 4px; padding: 10px 18px; display: flex; align-items: center; gap: 28px; flex-wrap: wrap; }
.brand { display: flex; align-items: center; gap: 12px; }
.mark { width: 32px; height: 32px; background: var(--accent); border-radius: 6px; position: relative; flex: none; }
.mark::after { content: ""; position: absolute; inset: 8px 6px; background: var(--panel2);
               clip-path: polygon(0 100%, 35% 18%, 55% 60%, 70% 38%, 100% 100%); }
.bt { font-weight: 700; font-size: 1.12rem; letter-spacing: -.005em; }
.bs { color: var(--muted); font-size: .8rem; margin-top: 1px; }
.tchips { display: flex; gap: 22px; flex: 1; flex-wrap: wrap; }
.tc { color: var(--muted); font-size: .84rem; display: flex; align-items: center; gap: 8px; }
.tc b { color: var(--text); font-weight: 600; }
.dot { width: 9px; height: 9px; border-radius: 2px; display: inline-block; flex: none; }
.tr { display: flex; align-items: center; gap: 16px; }
.badge { border: 1px solid var(--line2); color: var(--accent); border-radius: 3px; padding: 2px 9px; font-size: .78rem; font-weight: 600; }
.clock { text-align: right; line-height: 1.4; font-size: .82rem; color: var(--muted); }
.clock b { font-size: 1rem; font-weight: 600; color: var(--text); }

[class*="st-key-p_"] { background: var(--panel); border: 1px solid var(--line); border-radius: 4px; padding: 0 0 16px !important; gap: .4rem; }
[class*="st-key-p_"] > [data-testid="stElementContainer"], [class*="st-key-p_"] > div[data-testid] { padding-left: 14px; padding-right: 14px; }
.ph { background: var(--panel2); border-bottom: 1px solid var(--line); padding: 8px 14px; margin: 0 -14px 4px;
      display: flex; justify-content: space-between; align-items: baseline; font-weight: 600; font-size: .9rem; }
.ph small { color: var(--muted); font-weight: 400; font-size: .76rem; }
.legend { display: flex; gap: 16px; flex-wrap: wrap; font-size: .78rem; color: var(--muted); }
.legend i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; margin-right: 6px; vertical-align: -1px; }
.legend i.ev { border-radius: 50%; width: 7px; height: 7px; background: #c9d6df; }

.stRadio [role="radiogroup"] { gap: 6px; }
.stRadio label { background: var(--panel2); border: 1px solid var(--line); border-radius: 3px; padding: 3px 12px; }
.stRadio label:has(input:checked) { border-color: var(--accent); color: var(--accent); }
.stRadio label > div:first-child { display: none; }
.stButton button { background: var(--panel2); border: 1px solid var(--line2); color: var(--text); border-radius: 3px; width: 100%; }
.stButton button:hover { border-color: var(--accent); color: var(--accent); }

.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.stat { background: var(--panel2); border: 1px solid var(--line); border-radius: 3px; padding: 8px 10px 9px; }
.stat .l { font-size: .74rem; color: var(--muted); display: flex; align-items: center; gap: 6px; }
.stat .n { font-size: 1.7rem; font-weight: 600; line-height: 1.15; }
.stat .d { font-size: .74rem; color: var(--muted); }
.up { color: var(--high); } .dn { color: var(--low); }
.gname { text-align: center; color: var(--muted); font-size: .8rem; margin-top: -6px; }
.gname b { color: var(--text); }

.log { }
.ev { display: grid; grid-template-columns: 44px 3px 1fr; gap: 10px; padding: 7px 0; border-bottom: 1px solid var(--line); font-size: .84rem; }
.ev:last-child { border-bottom: 0; }
.ev .tm { color: var(--muted); font-size: .78rem; padding-top: 1px; }
.ev .sv { border-radius: 2px; }
.ev .sub { color: var(--muted); font-size: .76rem; margin-top: 1px; }
.empty { color: var(--muted); font-size: .86rem; padding: 10px 0; line-height: 1.6; }

.kv div { display: flex; justify-content: space-between; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--line); font-size: .86rem; }
.kv div:last-child { border-bottom: 0; }
.kv .k { color: var(--muted); }
.kv .big { font-size: 1.45rem; font-weight: 600; line-height: 1.1; }
.lv { font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
.lv i { width: 8px; height: 8px; border-radius: 2px; display: inline-block; }
.rk { width: 100%; border-collapse: collapse; font-size: .83rem; }
.rk td { padding: 5px 4px; border-bottom: 1px solid var(--line); vertical-align: middle; }
.rk tr:last-child td { border-bottom: 0; }
.rk .bar { height: 6px; background: #17283a; border-radius: 1px; min-width: 70px; }
.rk .bar b { display: block; height: 100%; border-radius: 1px; }
.rk .num { text-align: right; font-weight: 600; }
.rk .dl { text-align: right; font-size: .74rem; width: 48px; }
.pc { margin: 8px 0 2px; font-size: .83rem; }
.pc .row { display: flex; justify-content: space-between; margin-bottom: 3px; }
.pc .row span:first-child { color: var(--muted); }
.pc .bar { height: 7px; background: #17283a; border-radius: 1px; }
.pc .bar b { display: block; height: 100%; background: var(--accent); border-radius: 1px; }
.pc .hint { color: var(--muted); font-size: .72rem; margin: 3px 0 8px; }
.sub-h { font-size: .82rem; font-weight: 600; margin: 12px 0 0; }
.sub-s { font-size: .74rem; color: var(--muted); margin-bottom: 2px; }
.nb { font-size: .8rem; padding: 5px 0; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; gap: 10px; }
.nb:last-child { border-bottom: 0; }
.nb span:first-child { color: var(--accent); }
.foot { color: var(--muted); font-size: .76rem; line-height: 1.6; margin-top: 6px; }
"""

st.markdown(f"<style>{ROOT_VARS}{CSS}</style>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Dữ liệu
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _base():
    return build_base()


def ramp(h: int) -> float:
    """Đường cong tăng của mưa trong kịch bản: giờ 0 bằng 30% mức đã chọn, giờ cuối đúng bằng mức đã chọn."""
    return 0.30 + 0.70 * (h / HOURS) ** 1.3


@st.cache_data(show_spinner=False)
def build_series(scale: float, lo: float, hi: float, _base_data):
    """Điểm nguy cơ, mưa từng khu vực và số ô lưới theo mức, tính cho mọi giờ của kịch bản."""
    S = R = counts = None
    for h in range(HOURS + 1):
        _, cells, d = compute(_base_data, scale * ramp(h), (lo, hi))
        if S is None:
            S, R, counts = np.zeros((HOURS + 1, len(d))), np.zeros((HOURS + 1, len(d))), np.zeros((HOURS + 1, 3))
        S[h], R[h] = d["score"].to_numpy(), d["rain"].to_numpy()
        cells = np.asarray(cells)
        counts[h] = [(cells < lo).sum(), ((cells >= lo) & (cells < hi)).sum(), (cells >= hi).sum()]
    return S, R, counts


base = _base()
meta = base.get("metadata", {})
default_basemap = "Ngoại tuyến" if os.environ.get("LANDSLIDE_OFFLINE") == "1" else "Tối"


# ----------------------------------------------------------------------------
# Thanh bên
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="side-h">Kịch bản lượng mưa</div>', unsafe_allow_html=True)
    scale = st.slider("Hệ số mưa", 0.5, 2.0, 1.0, 0.1, label_visibility="collapsed")
    st.markdown('<div class="side-note">Hệ số này nhân với lượng mưa ở giờ cuối của kịch bản. '
                'Dòng thời gian cho mưa tăng dần từ 30% đến 100% mức đã chọn. '
                'Đây là kịch bản giả định, không phải dự báo.</div>', unsafe_allow_html=True)

    st.markdown('<div class="side-rule"></div><div class="side-h">Ngưỡng phân mức</div>', unsafe_allow_html=True)
    thr = st.slider("Ngưỡng trung bình và cao", 0.05, 0.95, (0.40, 0.70), 0.05, label_visibility="collapsed")
    rain_alert = st.number_input("Ngưỡng mưa chú ý (mm mỗi 24 giờ)", 30, 400, 100, 10)

    st.markdown('<div class="side-rule"></div><div class="side-h">Nền bản đồ</div>', unsafe_allow_html=True)
    basemap = st.selectbox("Nền bản đồ", BASEMAPS, index=BASEMAPS.index(default_basemap), label_visibility="collapsed")

    st.markdown('<div class="side-rule"></div><div class="side-h">Lớp hiển thị</div>', unsafe_allow_html=True)
    show_grid = st.checkbox("Ô lưới nguy cơ", True)
    show_areas = st.checkbox("Khu vực giám sát", True)
    show_hist = st.checkbox("Sạt lở đã ghi nhận", True)

    st.markdown('<div class="side-rule"></div><div class="side-note">Điểm nguy cơ là đầu ra của mô hình, '
                'chưa phải xác suất sạt lở đã hiệu chuẩn.</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Thân trang (chạy trong fragment để dòng thời gian tự phát được)
# ----------------------------------------------------------------------------
def monitor():
    ss = st.session_state
    ss.setdefault("t_step", HOURS)
    ss.setdefault("play", False)
    ss.setdefault("view", "Chia đôi")
    if ss.play:
        ss.t_step = (ss.t_step + 1) % (HOURS + 1)
    t = int(ss.t_step)

    S, R, counts = build_series(scale, thr[0], thr[1], base)
    risk, cells, df = compute(base, scale * ramp(t), thr)
    cells = np.asarray(cells)
    names = df["name"].tolist()
    n = len(names)

    cut = np.array([thr[0], thr[1]])
    lv_all = (S[:, :, None] >= cut[None, None, :]).sum(axis=2)          # 0 thấp, 1 trung bình, 2 cao
    n_high, n_mid = int((lv_all[t] == 2).sum()), int((lv_all[t] == 1).sum())
    n_low = n - n_high - n_mid
    prev = max(t - 1, 0)
    d_high, d_mid = n_high - int((lv_all[prev] == 2).sum()), n_mid - int((lv_all[prev] == 1).sum())
    d_low = n_low - int((lv_all[prev] == 0).sum())

    status, scol = (("Cảnh báo", C["high"]) if n_high else (("Theo dõi", C["mid"]) if n_mid else ("Bình thường", C["low"])))

    # ---- thanh trên cùng
    st.markdown(
        '<div class="top"><div class="brand"><div class="mark"></div><div>'
        '<div class="bt">Trung tâm giám sát nguy cơ sạt lở đất</div>'
        '<div class="bs">Vùng núi Nam Trà My và Phước Sơn, tỉnh Quảng Nam</div></div></div>'
        '<div class="tchips">'
        f'<span class="tc"><i class="dot" style="background:{scol}"></i>Trạng thái vùng <b>{status}</b></span>'
        f'<span class="tc">Khu vực giám sát <b class="mono">{n}</b></span>'
        f'<span class="tc">Ô lưới <b class="mono">{NC * NC}</b></span>'
        f'<span class="tc">Mưa 24 giờ lớn nhất <b class="mono">{df["rain"].max():.0f} mm</b></span></div>'
        f'<div class="tr"><span class="badge">{DATA_MODE}</span>'
        f'<div class="clock">Dữ liệu <b class="mono">{meta.get("last_updated", "")}</b><br>'
        f'Mô hình <b class="mono">{meta.get("model_run", "")}</b></div>'
        f'<div class="clock"><b class="mono">{hh(t)}</b><br>giờ thứ <span class="mono">{t}</span> của kịch bản</div></div></div>',
        unsafe_allow_html=True)

    # ---- hàng chính: bản đồ và 3D | chỉ số và nhật ký
    left, right = st.columns([3.6, 1.15], gap="small")
    with left:
        with st.container(key="p_view"):
            st.markdown(f'<div class="ph">Phân vùng nguy cơ<small>{n} khu vực, {NC * NC} ô lưới, '
                        f'giờ {hh(t)}</small></div>', unsafe_allow_html=True)
            c1, c2 = st.columns([1.5, 2])
            with c1:
                st.radio("Chế độ xem", ["Chia đôi", "Bản đồ", "Địa hình 3D"], horizontal=True,
                         key="view", label_visibility="collapsed")
            with c2:
                st.markdown(
                    '<div class="legend" style="margin-top:6px">'
                    f'<span><i style="background:{C["low"]}"></i>Thấp, dưới {vn(thr[0])}</span>'
                    f'<span><i style="background:{C["mid"]}"></i>Trung bình, {vn(thr[0])} đến {vn(thr[1])}</span>'
                    f'<span><i style="background:{C["high"]}"></i>Cao, từ {vn(thr[1])}</span>'
                    '<span><i class="ev"></i>Sạt lở đã ghi nhận</span></div>', unsafe_allow_html=True)

            def fig2d(h):
                return render_2d_workspace(base, cells, df, thr, map_style=basemap, show_risk_grid=show_grid,
                                           show_hist=show_hist, show_areas=show_areas, height=h)

            def fig3d(h):
                return render_3d_terrain(base, risk, df, thr, show_hist=show_hist, show_areas=show_areas, height=h)

            cfg = {"displaylogo": False, "modeBarButtonsToRemove": ["select2d", "lasso2d", "toImage"]}
            if ss.view == "Chia đôi":
                a, b = st.columns(2, gap="small")
                with a:
                    st.plotly_chart(fig2d(600), config=cfg, key="f_map")
                with b:
                    st.plotly_chart(fig3d(600), config=cfg, key="f_3d")
            elif ss.view == "Bản đồ":
                st.plotly_chart(fig2d(600), config=cfg, key="f_map")
            else:
                st.plotly_chart(fig3d(600), config=cfg, key="f_3d")

    with right:
        top_k = int(np.argmax(S[t]))
        gmax = float(S[t].max())
        with st.container(key="p_gauge"):
            st.markdown('<div class="ph">Điểm nguy cơ cao nhất<small>toàn vùng</small></div>', unsafe_allow_html=True)
            st.plotly_chart(charts.fig_gauge(gmax, level_of(gmax, thr), thr), config={"displayModeBar": False},
                            key="f_gauge")
            delta = gmax - float(S[prev].max())
            cls = "up" if delta > 0.0005 else ("dn" if delta < -0.0005 else "")
            st.markdown(f'<div class="gname"><b>{names[top_k]}</b> '
                        f'<span class="mono {cls}">{"+" if delta > 0.0005 else ""}{vn(delta)}</span> so với giờ trước</div>',
                        unsafe_allow_html=True)

            def stat(lab, col, val, dl, bad_up=True):
                good = (dl < 0) if bad_up else (dl > 0)
                c = "" if dl == 0 else ("dn" if good else "up")
                return (f'<div class="stat"><div class="l"><i class="dot" style="background:{col}"></i>{lab}</div>'
                        f'<div class="n mono">{val}</div><div class="d mono {c}">{"+" if dl > 0 else ""}{dl}</div></div>')

            st.markdown('<div class="stats" style="margin-top:10px">'
                        + stat("Cao", C["high"], n_high, d_high)
                        + stat("Theo dõi", C["mid"], n_mid, d_mid)
                        + stat("Bình thường", C["low"], n_low, d_low, bad_up=False)
                        + "</div>", unsafe_allow_html=True)

        # nhật ký sự kiện: suy ra từ chuỗi điểm số của kịch bản, chỉ hiện các sự kiện đã xảy ra đến giờ đang xem
        events = []
        for k in range(n):
            for h in range(1, t + 1):
                if lv_all[h, k] != lv_all[h - 1, k]:
                    new = ["Thấp", "Trung bình", "Cao"][lv_all[h, k]]
                    up = lv_all[h, k] > lv_all[h - 1, k]
                    events.append((h, k, f"{'lên' if up else 'xuống'} mức {new}",
                                   f"Điểm nguy cơ {vn(S[h, k])}", RISK_COLOR[new]))
            cross = np.where(R[:t + 1, k] >= rain_alert)[0]
            if len(cross):
                h = int(cross[0])
                events.append((h, k, "vượt ngưỡng mưa chú ý",
                               f"Mưa 24 giờ {R[h, k]:.0f} mm, ngưỡng {rain_alert} mm", C["accent"]))
        events.sort(key=lambda e: (-e[0], e[1]))
        with st.container(key="p_log"):
            st.markdown(f'<div class="ph">Nhật ký sự kiện<small>{len(events)} sự kiện đến {hh(t)}</small></div>',
                        unsafe_allow_html=True)
            if events:
                rows = "".join(
                    f'<div class="ev"><span class="tm mono">{hh(h)}</span><i class="sv" style="background:{col}"></i>'
                    f'<div><b>{names[k]}</b> {txt}<div class="sub">{sub}</div></div></div>'
                    for h, k, txt, sub, col in events[:6])
                st.markdown(f'<div class="log">{rows}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty">Chưa có sự kiện nào. Kéo dòng thời gian bên dưới hoặc bấm Phát '
                            'để xem diễn biến của kịch bản mưa.</div>', unsafe_allow_html=True)

    # ---- dòng thời gian
    with st.container(key="p_time"):
        st.markdown('<div class="ph">Dòng thời gian kịch bản 24 giờ'
                    '<small>số ô lưới theo mức nguy cơ, đường xanh là giờ đang xem</small></div>',
                    unsafe_allow_html=True)
        ta, tb = st.columns([0.5, 6], gap="medium")
        with ta:
            if st.button("Dừng" if ss.play else "Phát", key="btn_play"):
                ss.play = not ss.play
                st.rerun()
            st.markdown(f'<div class="mono" style="font-size:1.5rem;font-weight:600;margin-top:4px">{hh(t)}</div>',
                        unsafe_allow_html=True)
        with tb:
            st.plotly_chart(charts.fig_timeline(counts, t, NC * NC), config={"displayModeBar": False}, key="f_time")
            st.slider("Giờ của kịch bản", 0, HOURS, key="t_step", format="%d giờ", label_visibility="collapsed")

    # ---- hàng chi tiết
    if "area_pick" not in ss:
        ss.area_pick = names[int(np.argmax(S[-1]))]
    d1, d2, d3, d4 = st.columns([1.05, 1.15, 1.25, 1.05], gap="small")
    with d1:
        with st.container(key="p_tele"):
            st.markdown('<div class="ph">Thông số khu vực<small>tại giờ đang xem</small></div>', unsafe_allow_html=True)
            pick = st.selectbox("Khu vực", names, key="area_pick", label_visibility="collapsed")
            k = names.index(pick)
            z = df.iloc[k]
            st.markdown(
                '<div class="kv">'
                f'<div><span class="k">Điểm nguy cơ</span><span class="big mono">{vn(z["score"])}</span></div>'
                f'<div><span class="k">Mức hiện tại</span><span class="lv"><i style="background:{RISK_COLOR[z["level"]]}"></i>{z["level"]}</span></div>'
                f'<div><span class="k">Mã khu vực</span><span class="mono">{z["code"]}</span></div>'
                f'<div><span class="k">Vị trí</span><span class="mono">{vn(z["lat"])}°B, {vn(z["lon"])}°Đ</span></div>'
                f'<div><span class="k">Độ cao</span><span class="mono">{z["elev"]:.0f} m</span></div>'
                f'<div><span class="k">Độ dốc</span><span class="mono">{z["slope"]:.1f}°</span></div>'
                f'<div><span class="k">Mưa 24 giờ</span><span class="mono">{z["rain"]:.1f} mm</span></div>'
                f'<div><span class="k">Lớp phủ</span><span>{z["cover"]}</span></div></div>',
                unsafe_allow_html=True)

            ev = base["events"]
            near = ev[(ev["lat"].between(z["lat"] - 0.08, z["lat"] + 0.08)) &
                      (ev["lon"].between(z["lon"] - 0.08, z["lon"] + 0.08))].sort_values("date", ascending=False).head(4)
            st.markdown('<div class="sub-h" style="margin-top:14px">Sạt lở lịch sử lân cận</div>', unsafe_allow_html=True)
            if len(near):
                st.markdown("".join(f'<div class="nb"><span class="mono">{r.id}</span><span class="mono">{r.date}</span></div>'
                                    for r in near.itertuples()), unsafe_allow_html=True)
            else:
                st.markdown('<div class="sub-s">Không có sự kiện nào được ghi nhận trong vùng lân cận.</div>',
                            unsafe_allow_html=True)
    with d2:
        with st.container(key="p_cmp"):
            st.markdown(f'<div class="ph">So với toàn vùng<small>{pick}</small></div>', unsafe_allow_html=True)

            def pct(col):
                return 100 * float((df[col] < z[col]).mean())

            items = [("Điểm nguy cơ", "score", vn(z["score"])), ("Độ dốc", "slope", f'{z["slope"]:.1f}°'),
                     ("Mưa 24 giờ", "rain", f'{z["rain"]:.0f} mm'), ("Độ cao", "elev", f'{z["elev"]:.0f} m')]
            st.markdown('<div class="pc">' + "".join(
                f'<div class="row"><span>{lab}</span><span class="mono">{val}</span></div>'
                f'<div class="bar"><b style="width:{max(pct(col), 3):.0f}%"></b></div>'
                f'<div class="hint">cao hơn {pct(col):.0f}% số khu vực</div>' for lab, col, val in items) + '</div>',
                unsafe_allow_html=True)
            st.markdown('<div class="sub-h">Diễn biến điểm nguy cơ</div>'
                        '<div class="sub-s">Nét liền đến giờ đang xem, nét chấm là phần kịch bản còn lại.</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(charts.fig_trend(S[:, k], t, thr, z["level"]), config={"displayModeBar": False},
                            key="f_trend")
    with d3:
        with st.container(key="p_rain"):
            st.markdown(f'<div class="ph">Lượng mưa và phân bố<small>{pick}</small></div>', unsafe_allow_html=True)
            st.markdown('<div class="sub-h">Mưa 24 giờ theo kịch bản</div>'
                        '<div class="sub-s">Đơn vị mm, tăng dần theo giờ của kịch bản.</div>', unsafe_allow_html=True)
            st.plotly_chart(charts.fig_rain(R[:, k], t), config={"displayModeBar": False}, key="f_rain")
            st.markdown(f'<div class="sub-h">Phân bố điểm nguy cơ của {NC * NC} ô lưới</div>'
                        '<div class="sub-s">Trục ngang là điểm nguy cơ, trục dọc là số ô lưới.</div>', unsafe_allow_html=True)
            st.plotly_chart(charts.fig_hist(cells, thr), config={"displayModeBar": False}, key="f_hist")
    with d4:
        with st.container(key="p_rank"):
            st.markdown('<div class="ph">Xếp hạng khu vực<small>so với giờ trước</small></div>', unsafe_allow_html=True)
            rows = ""
            for kk in np.argsort(-S[t]):
                sc = float(S[t, kk])
                dl = sc - float(S[prev, kk])
                dcls = "up" if dl > 0.0005 else ("dn" if dl < -0.0005 else "")
                rows += (f'<tr><td>{names[kk]}</td>'
                         f'<td style="width:34%"><div class="bar"><b style="width:{100 * sc:.0f}%;background:{RISK_COLOR[level_of(sc, thr)]}"></b></div></td>'
                         f'<td class="num mono">{vn(sc)}</td>'
                         f'<td class="dl mono {dcls}">{"+" + vn(dl) if dl > 0.0005 else (vn(dl) if dl < -0.0005 else "0,00")}</td></tr>')
            st.markdown(f'<table class="rk">{rows}</table>', unsafe_allow_html=True)

    st.markdown('<div class="foot">Giao diện đang chạy bằng dữ liệu mô phỏng để trình diễn. Dòng thời gian là kịch bản mưa '
                'tăng dần do người dùng đặt, không phải diễn biến đã quan sát hay dự báo. Hệ thống là bản mẫu phục vụ '
                'nghiên cứu, không thay thế hệ thống cảnh báo thiên tai chính thức.</div>', unsafe_allow_html=True)


run = st.fragment(run_every=1.6 if st.session_state.get("play") else None)(monitor)
run()