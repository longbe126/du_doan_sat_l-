"""Trung tâm giám sát nguy cơ sạt lở đất.
Giao diện: mô hình 3D toàn màn hình ở giữa, thẻ kính nổi hai bên, thanh thời gian dạng viên ở đáy.
Mọi con số lấy từ mô hình đã huấn luyện (không gán cứng)."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in [str(ROOT / "app"), str(ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np
import streamlit as st

from core.data_engine import build_base, compute, NC
from core.model_loader import load_best_model
from components.theme import HOURS, vn, hh
from components.map_view import render_2d_workspace, render_3d_terrain, BASEMAPS

if not st.session_state.get("_root_navigation", False):
    st.set_page_config(page_title="Trung tâm giám sát nguy cơ sạt lở đất", page_icon="⛰️",
                       layout="wide", initial_sidebar_state="collapsed")

DATA_MODE = "Dữ liệu mô phỏng"
HI, MI, LO, AC = "#ff5a52", "#f5b942", "#4ade80", "#d4e88a"
MODEL_VI = {"logistic_regression": "Hồi quy logistic", "random_forest": "Rừng ngẫu nhiên", "xgboost": "XGBoost"}
CSS = r'''
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@200;300;400;500;600&display=swap');
html{font-size:calc(100vh*0.014815)!important}
html,body,.stApp,[data-testid="stMain"],[data-testid="stAppViewContainer"]{overflow:hidden!important}
.stApp{background:#07080b;color:#e8e9ec;line-height:1.25}
.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stMarkdownContainer"] div{line-height:1.25}
.stApp [data-testid="stMarkdownContainer"] p{margin:0}
.stApp,.stApp p,.stApp label,.stApp button,.stApp input,.stApp li,.stApp [data-baseweb]{font-family:'Be Vietnam Pro',system-ui,sans-serif}
[data-testid="stHeader"]{background:transparent!important;height:auto!important;z-index:60}
[data-testid="stToolbarActions"],[data-testid="stMainMenu"],.stAppDeployButton,[data-testid="stDecoration"],[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],footer{display:none!important}
.block-container{max-width:100%!important;padding:0!important;pointer-events:none}
[data-testid="stElementContainer"]{margin:0!important}
iframe[height="0"]{display:none}
.st-key-stage{position:fixed!important;inset:0;z-index:0;pointer-events:auto;padding:0!important;gap:0!important;overflow:hidden}
.st-key-colL,.st-key-colR{position:fixed!important;top:62px;display:flex;flex-direction:column;gap:8px!important;z-index:5;pointer-events:none}
.st-key-colL{left:18px;width:396px}.st-key-colR{right:18px;width:432px}
.st-key-colL{gap:10px!important}
.st-key-g_prof{margin-bottom:12px!important}
.st-key-colL,.st-key-colR{height:calc(100vh - 82px);overflow-y:auto!important;overflow-x:hidden!important;padding-right:2px;scrollbar-width:none}
.st-key-colL::-webkit-scrollbar,.st-key-colR::-webkit-scrollbar{display:none}
.g,.mc,.mini,[class*="st-key-g_"]{pointer-events:auto;background:rgba(34,36,40,.58)!important;backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.08)!important;border-radius:22px!important}
[class*="st-key-g_"]{padding:0!important;gap:0!important;overflow:hidden}
.st-key-g_ctrl,.st-key-g_zb{background:none!important;border:0!important;backdrop-filter:none!important;overflow:visible}
.st-key-g_ctrl{position:fixed!important;top:12px;right:18px;z-index:50;width:auto!important}
.st-key-g_ctrl button{background:rgba(34,36,40,.58);border:1px solid rgba(255,255,255,.08);border-radius:999px;color:#e8e9ec;padding:4px 16px}
.st-key-g_zb{position:fixed!important;right:480px;bottom:128px;z-index:20;width:170px;height:38px;display:flex!important;align-items:center!important;margin-left:0!important}
.st-key-g_mapmode{position:fixed!important;right:658px;bottom:128px;width:96px;height:38px;z-index:20;padding:0!important;box-sizing:border-box;border-radius:11px!important;background:transparent!important;border:0!important;box-shadow:none!important;overflow:visible!important}
.st-key-g_mapmode [data-testid="stHorizontalBlock"]{width:96px!important;margin:0!important;gap:0!important}
.st-key-g_zb [data-testid="stElementContainer"]{margin:0!important;padding:0!important}
.st-key-g_zb [data-testid="stElementContainer"]>div{width:100%!important}
.st-key-g_mapmode button{width:96px!important;height:38px!important;min-height:38px!important;line-height:38px!important;padding:0 8px!important;border-radius:11px!important;white-space:nowrap!important;font-size:.72rem!important;background:rgba(255,255,255,.055)!important;border:1px solid rgba(255,255,255,.08)!important}
.st-key-g_mapmode [data-testid="stPopoverBody"]{min-width:96px!important;width:96px!important;background:#17191d!important;border:1px solid rgba(255,255,255,.10)!important;border-radius:11px!important;padding:4px!important;box-shadow:0 12px 28px rgba(0,0,0,.35)!important}
.st-key-g_mapmode [data-testid="stPopoverBody"] button{height:32px!important;min-height:32px!important;line-height:32px!important;width:86px!important;margin:1px 0!important;font-size:.72rem!important}
.st-key-g_zb [data-testid="stHorizontalBlock"]{height:38px!important;align-items:center!important;gap:8px!important}
.st-key-g_zb button{height:38px!important;min-height:38px!important;border-radius:11px!important;padding:0 8px!important;white-space:nowrap}
.st-key-g_time{width:auto!important;position:fixed!important;bottom:22px;left:440px;right:480px;height:96px;border-radius:30px!important;padding:0 22px!important;z-index:20;justify-content:center}
.st-key-g_time [data-testid="stSlider"]{padding:0}
[data-testid="stTickBar"],[data-testid="stSliderThumbValue"]{display:none}
[data-testid="stBaseButton-primary"]{background:#d4e88a!important;color:#1b2208!important;border:0!important;border-radius:999px;font-weight:600}
[data-testid="stBaseButton-secondary"]{background:rgba(34,36,40,.58);border:1px solid rgba(255,255,255,.08);color:#e8e9ec;border-radius:12px}
.st-key-g_time button{width:100%}
.ph{display:flex;justify-content:space-between;padding:11px 16px;border-bottom:1px solid rgba(255,255,255,.07);font-size:.95rem}.ph small{color:#8b8f98;font-size:.76rem;align-self:center}
.kv div{display:flex;justify-content:space-between;padding:6px 16px;font-size:.84rem;border-bottom:1px solid rgba(255,255,255,.05)}.kv .k{color:#8b8f98}.kv div:last-child{border:0}
.st-key-g_prof [data-testid="stSelectbox"]{padding:10px 14px 6px}
.st-key-g_prof [data-baseweb="select"]>div{background:rgba(255,255,255,.05);border:0;border-radius:12px;min-height:36px;font-size:.88rem}
.brand{padding:0 4px 2px;height:42px}
.st-key-g_prof{margin-top:20px}.brand b{display:block;font-weight:500;font-size:1.05rem;color:#e8e9ec}.brand span{display:block;color:#8b8f98;font-size:.78rem;margin-top:2px}
.st-key-g_prof,.st-key-colL .g,.st-key-colL .two,.st-key-colR .mg,.st-key-colR .g{margin-bottom:0!important}
.kv div{min-height:32px;box-sizing:border-box;align-items:center}
.st-key-colL .two,.st-key-colL>*,.st-key-colR>*{flex:none}
.st-key-colL>div:not(:last-child){margin-bottom:2px!important}
.st-key-colL .two{margin-top:2px!important;margin-bottom:2px!important}
.st4{grid-template-columns:repeat(4,minmax(0,1fr));align-items:start}
.st4 div{min-width:0;overflow-wrap:anywhere}
.two{display:grid!important;grid-template-columns:1fr 1fr!important;column-gap:12px!important;row-gap:0!important;clear:both;margin:0!important}.mini{height:82px!important;box-sizing:border-box;padding:12px 14px;border-radius:16px!important}.mini .t{display:flex;justify-content:space-between;font-size:.85rem;color:#d6d8dc}.mini .n{font-size:1.9rem;font-weight:200;margin-top:2px;line-height:1.2}.mini .d{font-size:.72rem;color:#8b8f98}
.ev{display:grid;grid-template-columns:42px 3px 1fr;gap:10px;padding:6px 16px;font-size:.8rem;border-bottom:1px solid rgba(255,255,255,.05)}.ev:last-child{border:0}.ev i{border-radius:2px}.tm{color:#8b8f98;font-size:.74rem}.sub{color:#8b8f98;font-size:.72rem}
.st-key-g_cat [role="radiogroup"]{gap:6px!important;padding:8px 10px}
.st-key-g_cat label{padding:5px 16px;border-radius:999px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);margin:0}
.st-key-g_cat label>div:first-child{display:none}.st-key-g_cat label p{font-size:.82rem}
.st-key-g_cat label:has(input:checked){background:#d4e88a;border-color:#d4e88a}.st-key-g_cat label:has(input:checked) p{color:#1b2208;font-weight:500}
.mg{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));grid-auto-rows:1fr;gap:9px;pointer-events:none}.mc{height:100%;box-sizing:border-box;padding:10px 13px 8px}
.mt{font-size:.78rem;display:flex;align-items:center;gap:8px;color:#d6d8dc;white-space:nowrap}.mt i{width:3px;height:13px;border-radius:2px}.mv{margin:6px 0 4px}.n{font-size:1.9rem;font-weight:200;line-height:1;font-variant-numeric:tabular-nums}.n.t{font-size:1.15rem;font-weight:300}.u{font-size:.76rem;color:#8b8f98;margin-left:4px}
.dp{display:inline-block;border-radius:999px;padding:1px 9px;font-size:.7rem;background:rgba(255,255,255,.07)}.dp.up{color:#ff6b6b;background:rgba(255,77,77,.13)}.dp.dn{color:#4ade80;background:rgba(74,222,128,.13)}
.sp{width:100%;height:30px;margin-top:6px;background:rgba(255,255,255,.035);border-radius:8px;display:block}.mn{font-size:.68rem;color:#8b8f98;margin-top:5px}
.bar{height:6px;background:rgba(255,255,255,.08);border-radius:3px;overflow:hidden}.bar b{display:block;height:100%}
.rk{width:100%;border-collapse:collapse;font-size:.8rem}.rk td{padding:5px 8px;border-bottom:1px solid rgba(255,255,255,.05)}.rk td:first-child{padding-left:16px}.rk .num{text-align:right;font-weight:500}.rk .dl{text-align:right;font-size:.7rem;color:#8b8f98;padding-right:16px}.rk .dl.up{color:#ff6b6b}
.mb{display:grid;grid-template-columns:110px 1fr 44px;gap:10px;align-items:center;padding:4px 16px;font-size:.78rem}.mb span:first-child{color:#8b8f98}.num{text-align:right}
.st4{display:grid;grid-template-columns:repeat(4,1fr);padding:10px 16px 6px;column-gap:12px;row-gap:6px}.st4 div{font-size:.68rem;color:#8b8f98;min-width:0}.st4 b{display:block;font-size:1.25rem;font-weight:300;color:#e8e9ec}
.stk{display:flex;height:10px;margin:12px 16px 8px;border-radius:5px;overflow:hidden}.lg2{display:flex;justify-content:space-between;padding:0 16px 12px;font-size:.72rem;color:#b9bcc3}.lg2 i,.lgd i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px}
.status{position:fixed;top:14px;left:50%;transform:translateX(-50%);z-index:6;display:inline-flex;gap:12px;align-items:center;padding:8px 18px;border-radius:999px!important;font-size:.84rem;white-space:nowrap}.status span{color:#8b8f98}.status b{font-weight:500}
.pop{position:fixed;left:460px;bottom:132px;width:330px;padding:14px 16px;z-index:7;background:rgba(18,20,23,.94)!important;border-color:rgba(255,255,255,.12)!important;box-shadow:0 18px 44px rgba(0,0,0,.38)}
.pop h4{font-weight:500;font-size:.98rem;display:flex;justify-content:space-between;align-items:center;margin:0 0 10px}.pop h4 em{font-style:normal;border-radius:999px;padding:3px 9px;font-size:.68rem}
.pop .ops{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:10px}
.pop .op{padding:8px 9px;border-radius:10px;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.055)}
.pop .op span{display:block;color:#8b8f98;font-size:.68rem}.pop .op b{display:block;margin-top:3px;font-size:.92rem;font-weight:500;font-variant-numeric:tabular-nums}
.pop .r{display:flex;justify-content:space-between;padding:6px 0;font-size:.78rem;border-top:1px solid rgba(255,255,255,.07)}.pop .r span:first-child{color:#8b8f98}
.pop .notice{margin-top:8px;padding:8px 10px;border-radius:9px;font-size:.72rem;line-height:1.45;background:rgba(255,255,255,.045)}
.lgd{position:fixed;left:440px;bottom:130px;padding:10px 16px;font-size:.76rem;color:#b9bcc3;display:flex;gap:18px;border-radius:999px!important;z-index:6;white-space:nowrap}
.clk{line-height:1.2}.clk b{font-size:1.2rem;font-weight:300;display:block}.clk span{color:#8b8f98;font-size:.7rem}
.ar{width:100%;height:40px;border-radius:8px;display:block}.mini2{font-size:.72rem;color:#8b8f98;text-align:right}.mini2 b{display:block;font-size:1.05rem;font-weight:300;color:#e8e9ec}
'''
CSS = re.sub(r'(?<![\d.])(\d+(?:\.\d+)?)px', lambda m: m.group(0) if m.group(1) == '1' else f'{float(m.group(1)) / 16:g}rem', CSS)


def ramp(h: int) -> float:
    return 0.30 + 0.70 * (h / HOURS) ** 1.3


@st.cache_resource(show_spinner=False)
def _model():
    return load_best_model()


@st.cache_resource(show_spinner=False)
def _base():
    return build_base()


base = _base()
meta = base.get("metadata", {})
model_obj, model_name, report = _model()
default_basemap = "Bản đồ"


@st.cache_data(show_spinner=False)
def series(scale: float, t0: float, t1: float):
    S, R, CN = [], [], []
    for h in range(HOURS + 1):
        _, cells, d = compute(base, scale * ramp(h), (t0, t1), model_obj)
        c = np.asarray(cells)
        S.append(d["score"].to_numpy())
        R.append(d["rain"].to_numpy())
        CN.append([int((c < t0).sum()), int(((c >= t0) & (c < t1)).sum()), int((c >= t1).sum())])
    return np.array(S), np.array(R), np.array(CN)


def spark(vals, vmax, t, ref=None, col=AC):
    idx = np.unique(np.linspace(0, t, 6).round().astype(int))
    ys = [48 - 40 * min(max(float(vals[i]) / vmax, 0), 1) for i in idx]
    xs = np.linspace(12, 188, len(idx)) if len(idx) > 1 else [188]
    line = (f'<line x1="0" x2="200" y1="{48 - 40 * ref / vmax:.1f}" y2="{48 - 40 * ref / vmax:.1f}" '
            'stroke="rgba(255,255,255,.35)"/>') if ref else ""
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="#fff"/>' for x, y in zip(xs[:-1], ys[:-1]))
    last = (f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="3.4" fill="{col}"/>'
            f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="8" fill="none" stroke="{col}" stroke-width="1.2"/>')
    return f'<svg class="sp" viewBox="0 0 200 56">{line}{dots}{last}</svg>'


def card(title, val, unit, col, dl=None, fmt=vn, sp="", note="", small=False):
    pill = ""
    if dl is not None:
        c = "up" if dl > 0.0005 else ("dn" if dl < -0.0005 else "")
        pill = f'<div><span class="dp {c}">{"+" if dl > 0.0005 else ""}{fmt(dl)}</span></div>'
    return (f'<div class="mc"><div class="mt"><i style="background:{col}"></i>{title}</div>'
            f'<div class="mv"><span class="n{" t" if small else ""}">{val}</span><span class="u">{unit}</span></div>'
            f'{pill}{sp}<div class="mn">{note}</div></div>')


def monitor():
    ss = st.session_state
    for k_, v_ in dict(t_step=HOURS, play=False, view="3D", cat="Nguy cơ", scale=1.0,
                       rain_alert=100, show_grid=True,
                       show_areas=True, show_hist=True, zoom=1.0).items():
        ss.setdefault(k_, v_)
    ss.setdefault("basemap", default_basemap)
    if ss.get("_area_selection_version") != 3:
        ss.area_pick = None
        ss._area_selection_version = 3
    if ss.play:
        ss.t_step = (ss.t_step + 1) % (HOURS + 1)
    t = int(ss.t_step)
    prev = max(t - 1, 0)
    scale, RA = ss.scale, ss.rain_alert
    raw_thr = ss.get("thr", (0.40, 0.70))
    if isinstance(raw_thr, (tuple, list, np.ndarray)) and len(raw_thr) == 2:
        lo, hi = sorted((float(raw_thr[0]), float(raw_thr[1])))
        lo = min(max(lo, 0.05), 0.90)
        hi = max(lo + 0.05, min(hi, 0.95))
    else:
        lo, hi = 0.40, 0.70
    thr = (lo, hi)

    S, R, CN = series(scale, thr[0], thr[1])
    risk, cells, df = compute(base, scale * ramp(t), thr, model_obj)
    cells = np.asarray(cells)
    names = df["name"].tolist()
    n = len(names)
    selected_area = ss.get("area_pick")
    k = names.index(selected_area) if selected_area in names else int(np.argmax(df["score"].to_numpy()))
    z = df.iloc[k]
    lvl = lambda v: "Cao" if v >= thr[1] else ("Trung bình" if v >= thr[0] else "Thấp")
    lcol = lambda v: HI if v >= thr[1] else (MI if v >= thr[0] else LO)
    cut = np.array(thr)
    lv_all = (S[:, :, None] >= cut[None, None, :]).sum(axis=2)
    nh, nm = (lv_all == 2).sum(axis=1), (lv_all == 1).sum(axis=1)
    n_high, n_mid = int(nh[t]), int(nm[t])
    status, scol = (("Cảnh báo", HI) if n_high else (("Theo dõi", MI) if n_mid else ("Bình thường", LO)))
    glow = {"Cảnh báo": "239,68,68", "Theo dõi": "245,158,11", "Bình thường": "16,185,129"}[status]
    st.markdown(f"<style>.stApp{{background:radial-gradient(ellipse 85% 42% at 50% 112%, rgba({glow},.5), "
                f"transparent 72%), #07080b}}</style>", unsafe_allow_html=True)

    # ---- nền: mô hình 3D hoặc bản đồ chiếm cả màn hình
    with st.container(key="stage"):
        if ss.view == "3D":
            fig = render_3d_terrain(base, risk, df, thr, show_hist=ss.show_hist, show_areas=ss.show_areas,
                                    height=940, selected_area=ss.area_pick)
            zm = ss.zoom
            fig.update_layout(scene=dict(camera=dict(eye=dict(x=1.35 * zm, y=-1.5 * zm, z=1.0 * zm),
                                                     center=dict(x=0, y=0, z=-0.2))))
        else:
            fig = render_2d_workspace(base, cells, df, thr, map_style=ss.basemap, show_risk_grid=ss.show_grid,
                                      show_hist=ss.show_hist, show_areas=ss.show_areas, height=940,
                                      selected_area=ss.area_pick)
        chart_selection = st.plotly_chart(
            fig,
            config={"displayModeBar": False, "scrollZoom": True},
            key="f_stage",
            on_select="rerun",
            selection_mode="points",
        )
        clicked_points = getattr(getattr(chart_selection, "selection", None), "points", [])
        if clicked_points:
            clicked = clicked_points[0]
            customdata = clicked.get("customdata")
            if isinstance(customdata, (list, tuple)) and customdata:
                clicked_area = str(customdata[5] if ss.view != "3D" else customdata[0])
            else:
                clicked_area = str(customdata) if customdata else ""
            if clicked_area not in names:
                point_index = clicked.get("point_index")
                if point_index is not None and 0 <= int(point_index) < len(names):
                    clicked_area = names[int(point_index)]
            if clicked_area in names and ss.area_pick != clicked_area:
                ss.area_pick = clicked_area
                st.rerun(scope="fragment")

    # ---- nhật ký sự kiện
    events = []
    for kk in range(n):
        for h in range(1, t + 1):
            if lv_all[h, kk] != lv_all[h - 1, kk]:
                nw = ["Thấp", "Trung bình", "Cao"][lv_all[h, kk]]
                events.append((h, kk, f"{'lên' if lv_all[h, kk] > lv_all[h - 1, kk] else 'xuống'} mức {nw}",
                               f"Điểm nguy cơ {vn(S[h, kk])}", [LO, MI, HI][lv_all[h, kk]]))
        cr = np.where(R[:t + 1, kk] >= RA)[0]
        if len(cr):
            h = int(cr[0])
            events.append((h, kk, "vượt ngưỡng mưa chú ý", f"Mưa 24 giờ {R[h, kk]:.0f} mm, ngưỡng {RA} mm", "#38bdf8"))
    events.sort(key=lambda e: (-e[0], e[1]))
    ev = base["events"]
    if selected_area in names:
        near = ev[(ev["lat"].between(z["lat"] - 0.08, z["lat"] + 0.08)) &
                  (ev["lon"].between(z["lon"] - 0.08, z["lon"] + 0.08))].sort_values("date", ascending=False)
    else:
        near = ev.sort_values("date", ascending=False)

    # ---- thẻ chỉ số theo nhóm
    gm = float(S[t].max())
    rmax = max(float(R.max()), float(RA))
    ii = lambda x: f"{int(x)}"
    pc = lambda col: f'cao hơn {100 * float((df[col] < z[col]).mean()):.0f}% số khu vực'
    if ss.cat == "Nguy cơ":
        cs = [card("Điểm khu vực", vn(z["score"]), "/ 1", lcol(z["score"]), S[t, k] - S[prev, k], vn,
                   spark(S[:, k], 1, t, thr[1], lcol(z["score"])), f'Mức {lvl(z["score"])}, ngưỡng cao từ {vn(thr[1])}'),
              card("Cao nhất toàn vùng", vn(gm), "/ 1", lcol(gm), gm - float(S[prev].max()), vn,
                   spark(S.max(axis=1), 1, t, thr[1], AC), names[int(np.argmax(S[t]))]),
              card("Khu vực mức cao", n_high, f"/ {n}", HI, n_high - int(nh[prev]), ii, spark(nh, n, t, None, HI),
                   f"Theo dõi: {n_mid} khu vực"),
              card("Ô lưới mức cao", int(CN[t, 2]), f"/ {NC * NC}", HI, CN[t, 2] - CN[prev, 2], ii,
                   spark(CN[:, 2], NC * NC, t, None, HI), f"Trung bình: {int(CN[t, 1])} ô"),
              card("Mưa 24 giờ khu vực", f'{R[t, k]:.0f}', "mm", AC, R[t, k] - R[prev, k], ii,
                   spark(R[:, k], rmax, t, RA), f"Ngưỡng chú ý {RA} mm"),
              card("Mưa lớn nhất vùng", f'{R[t].max():.0f}', "mm", AC, R[t].max() - R[prev].max(), ii,
                   spark(R.max(axis=1), rmax, t, RA), names[int(np.argmax(R[t]))]),
              card("Vượt ngưỡng mưa", int((R[t] >= RA).sum()), f"/ {n}", MI,
                   int((R[t] >= RA).sum()) - int((R[prev] >= RA).sum()), ii,
                   spark((R >= RA).sum(axis=1), n, t, None, MI), "khu vực"),
              card("Độ dốc khu vực", f'{z["slope"]:.1f}', "°", MI, None, vn, "", pc("slope"))]
    elif ss.cat == "Mưa":
        cs = [card("Mưa 24 giờ khu vực", f'{R[t, k]:.0f}', "mm", AC, R[t, k] - R[prev, k], ii, spark(R[:, k], rmax, t, RA),
                   f"Ngưỡng chú ý {RA} mm"),
              card("Mưa lớn nhất vùng", f'{R[t].max():.0f}', "mm", AC, R[t].max() - R[prev].max(), ii,
                   spark(R.max(axis=1), rmax, t, RA), names[int(np.argmax(R[t]))]),
              card("Mưa trung bình vùng", f'{R[t].mean():.0f}', "mm", AC, R[t].mean() - R[prev].mean(), ii,
                   spark(R.mean(axis=1), rmax, t, RA), "trung bình 12 khu vực"),
              card("Mưa nhỏ nhất vùng", f'{R[t].min():.0f}', "mm", AC, R[t].min() - R[prev].min(), ii,
                   spark(R.min(axis=1), rmax, t, RA), names[int(np.argmin(R[t]))]),
              card("Vượt ngưỡng mưa", int((R[t] >= RA).sum()), f"/ {n}", MI,
                   int((R[t] >= RA).sum()) - int((R[prev] >= RA).sum()), ii,
                   spark((R >= RA).sum(axis=1), n, t, None, MI), "khu vực"),
              card("Hệ số kịch bản", vn(scale, 1), "×", AC, None, vn, "", "Mưa tăng dần từ 30% đến 100% mức đã chọn")]
    else:
        cs = [card("Độ cao khu vực", f'{z["elev"]:.0f}', "m", AC, None, vn, "", pc("elev")),
              card("Độ dốc khu vực", f'{z["slope"]:.1f}', "°", MI, None, vn, "", pc("slope")),
              card("Lớp phủ", z["cover"], "", LO, None, vn, "", "ESA WorldCover", True),
              card("Vị trí", f'{vn(z["lat"])}°B', "", AC, None, vn, "", f'{vn(z["lon"])}°Đ · mã {z["code"]}', True),
              card("Độ cao lớn nhất vùng", f'{df["elev"].max():.0f}', "m", AC, None, vn, "", df.loc[df["elev"].idxmax(), "name"]),
              card("Độ dốc lớn nhất vùng", f'{df["slope"].max():.1f}', "°", MI, None, vn, "", df.loc[df["slope"].idxmax(), "name"])]

    # ---- cột trái
    with st.container(key="colL"):
        st.markdown('<div class="brand"><b>Trung tâm giám sát nguy cơ sạt lở đất</b>'
                    '<span>Nam Trà My và Phước Sơn, Quảng Nam</span></div>', unsafe_allow_html=True)
        with st.container(key="g_prof"):
            st.markdown(f'<div class="ph">Hồ sơ khu vực<small>giờ {hh(t)}</small></div>', unsafe_allow_html=True)
            selected_index = names.index(ss.area_pick) if ss.get("area_pick") in names else None
            st.selectbox("Khu vực", names, index=selected_index, placeholder="Chọn điểm trên bản đồ",
                         key="area_pick", label_visibility="collapsed")
            if ss.get("area_pick") is None:
                high_names = df.nlargest(3, "score")
                high_max = float(df["score"].max())
                focus_name = str(high_names.iloc[0]["name"])
                focus_level = lvl(high_max)
                st.markdown(
                    '<div class="kv">'
                    f'<div><span class="k">Chế độ quan sát</span><span>Tổng quan khu vực</span></div>'
                    f'<div><span class="k">Điểm giám sát</span><span>{len(df)} khu vực</span></div>'
                    f'<div><span class="k">Mức cao nhất</span><span style="color:{lcol(high_max)}">■ {focus_level}</span></div>'
                    f'<div><span class="k">Khu vực chú ý</span><span>{focus_name}</span></div>'
                    f'<div><span class="k">Điểm nguy cơ cao nhất</span><span>{vn(high_max)}</span></div>'
                    f'<div><span class="k">Mưa giờ cao nhất</span><span>{float(R[t].max()):.0f} mm</span></div>'
                    '</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="kv">'
                    f'<div><span class="k">Mức hiện tại</span><span style="color:{lcol(z["score"])}">■ {lvl(z["score"])}</span></div>'
                    f'<div><span class="k">Mã khu vực</span><span>{z["code"]}</span></div>'
                    f'<div><span class="k">Vị trí</span><span>{vn(z["lat"])}°B, {vn(z["lon"])}°Đ</span></div>'
                    f'<div><span class="k">Độ cao</span><span>{z["elev"]:.0f} m</span></div>'
                    f'<div><span class="k">Độ dốc</span><span>{z["slope"]:.1f}°</span></div>'
                    f'<div><span class="k">Mưa 24 giờ</span><span>{R[t, k]:.1f} mm</span></div>'
                    f'<div><span class="k">Lớp phủ</span><span>{z["cover"]}</span></div></div>',
                    unsafe_allow_html=True)
        last_ev = f"gần nhất {near.iloc[0]['date']}" if len(near) else "chưa ghi nhận"
        st.markdown('<div class="two">'
                    f'<div class="mini"><div class="t">Sạt lở lịch sử<span>↗</span></div><div class="n">{len(near)}</div><div class="d">{last_ev}</div></div>'
                    f'<div class="mini"><div class="t">Sự kiện<span>↗</span></div><div class="n">{len(events)}</div><div class="d">đến {hh(t)}</div></div>'
                    '</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="g"><div class="ph">Trạm quan sát khu vực<small>dữ liệu mô phỏng</small></div>'
            '<div class="st4">'
            f'<div><b>{len(df)}</b>Điểm giám sát</div>'
            f'<div><b>{R[t].mean():.0f}</b>Mưa TB toàn vùng (mm)</div>'
            f'<div><b>{float(df["slope"].mean()):.1f}°</b>Độ dốc TB</div>'
            f'<div><b>{int((R[t] >= RA).sum())}</b>Khu vực có cảnh báo mưa</div>'
            '</div><div style="height:6px"></div></div>', unsafe_allow_html=True)
        alert_rows = [(names[i], float(R[t, i])) for i in np.where(R[t] >= RA)[0]]
        alert_rows.sort(key=lambda item: item[1], reverse=True)
        if alert_rows:
            alert_html = "".join(
                f'<div class="ev"><span class="tm">{hh(t)}</span><i style="background:{HI}"></i>'
                f'<div><b>{name}</b> Cảnh báo mưa<div class="sub">{rain:.0f} mm · ngưỡng {RA:.0f} mm</div></div></div>'
                for name, rain in alert_rows[:5]
            )
        else:
            alert_html = f'<div class="ev"><span></span><i style="background:{LO}"></i><div><b>Toàn khu vực bình thường</b><div class="sub">Không khu vực nào vượt ngưỡng mưa chú ý</div></div></div>'
        st.markdown(f'<div class="g"><div class="ph">Cảnh báo vận hành<small>{len(alert_rows)} khu vực</small></div>{alert_html}</div>', unsafe_allow_html=True)
        log = "".join(f'<div class="ev"><span class="tm">{hh(h)}</span><i style="background:{c}"></i>'
                      f'<div><b>{names[kk]}</b> {tx}<div class="sub">{sb}</div></div></div>' for h, kk, tx, sb, c in events[:5]) \
            or '<div class="ev"><span></span><span></span><div class="sub">Chưa có sự kiện. Bấm Phát để xem diễn biến.</div></div>'
        st.markdown(f'<div class="g"><div class="ph">Nhật ký sự kiện<small>mới nhất</small></div>{log}</div>', unsafe_allow_html=True)
    # ---- cột phải
    with st.container(key="colR"):
        with st.container(key="g_cat"):
            st.radio("Nhóm chỉ số", ["Nguy cơ", "Mưa", "Địa hình"], horizontal=True, key="cat", label_visibility="collapsed")
        st.markdown('<div class="mg">' + "".join(cs) + '</div>', unsafe_allow_html=True)
        lo_, mi_, hi_ = (int(x) for x in CN[t])
        tot = NC * NC
        st.markdown(
            f'<div class="g" style="margin-top:14px"><div class="ph">Phân bố {tot} ô lưới<small>giờ {hh(t)}</small></div>'
            f'<div class="stk"><b style="width:{100 * lo_ / tot:.1f}%;background:{LO}"></b><b style="width:{100 * mi_ / tot:.1f}%;background:{MI}"></b>'
            f'<b style="width:{100 * hi_ / tot:.1f}%;background:{HI}"></b></div>'
            f'<div class="lg2"><span><i style="background:{LO}"></i>Thấp {lo_}</span><span><i style="background:{MI}"></i>Trung bình {mi_}</span>'
            f'<span><i style="background:{HI}"></i>Cao {hi_}</span></div></div>', unsafe_allow_html=True)
        rows = ""
        for i in np.argsort(-S[t])[:3]:
            sc, dl = float(S[t, i]), float(S[t, i] - S[prev, i])
            sg = "+" if dl > 0.0005 else ""
            rows += (f'<tr><td>{names[i]}</td><td style="width:34%"><div class="bar"><b style="width:{100 * sc:.0f}%;background:{lcol(sc)}"></b></div></td>'
                     f'<td class="num">{vn(sc)}</td><td class="dl {"up" if dl > 0.0005 else ""}">{sg}{vn(dl)}</td></tr>')
        st.markdown(f'<div class="g"><div class="ph">Top 3 nguy cơ cao nhất<small>so với giờ trước</small></div><table class="rk">{rows}</table></div>',
                    unsafe_allow_html=True)

    # ---- thanh trên cùng, thẻ nổi, chú giải
    st.markdown(f'<div class="g status"><i style="width:9px;height:9px;border-radius:2px;background:{scol}"></i><b>{status}</b>'
                f'<span>{hh(t)} · giờ thứ {t}</span><span>{DATA_MODE}</span>'
                f'<span>Mô hình {MODEL_VI.get(model_name, model_name)}</span></div>',
                unsafe_allow_html=True)
    trend = float(S[t, k] - S[prev, k])
    if ss.get("area_pick") in names:
        rain_value = float(R[t, k])
        if z["score"] >= thr[1] and rain_value >= RA:
            operation_status, operation_color, operation_note = "Cảnh báo khẩn", HI, "Nguy cơ và lượng mưa đang cao. Ưu tiên kiểm tra tuyến đường và cộng đồng tại khu vực."
        elif z["score"] >= thr[0] or rain_value >= RA:
            operation_status, operation_color, operation_note = "Theo dõi chặt", MI, "Một hoặc nhiều điều kiện vượt ngưỡng. Tăng tần suất quan sát và theo dõi mưa tiếp theo."
        else:
            operation_status, operation_color, operation_note = "Ổn định", LO, "Các chỉ số đang trong ngưỡng theo dõi thường xuyên."
        st.markdown(
            f'<div class="g pop"><h4><span>{z["name"]}</span><em style="color:{operation_color};border:1px solid {operation_color}55;background:{operation_color}18">{operation_status}</em></h4>'
            '<div class="ops">'
            f'<div class="op"><span>Mưa 24 giờ</span><b>{rain_value:.0f} mm</b></div>'
            f'<div class="op"><span>Điểm nguy cơ</span><b style="color:{lcol(z["score"])}">{vn(z["score"])}</b></div>'
            f'<div class="op"><span>Độ dốc địa hình</span><b>{z["slope"]:.1f}°</b></div>'
            f'<div class="op"><span>Độ cao khu vực</span><b>{z["elev"]:.0f} m</b></div></div>'
            f'<div class="r"><span>Ngưỡng mưa cảnh báo</span><span>{RA:.0f} mm</span></div>'
            f'<div class="r"><span>Xu hướng</span><span style="color:{"#ff6b6b" if trend > 0.0005 else "#8b8f98"}">'
            f'{"Tăng" if trend > 0.0005 else ("Giảm" if trend < -0.0005 else "Ổn định")} {"+" if trend > 0.0005 else ""}{vn(trend)}</span></div>'
            f'<div class="notice">{operation_note}</div></div>'
            ,
            unsafe_allow_html=True)
    st.markdown(
        f'<div class="g lgd"><span><i style="background:{LO}"></i>Thấp, dưới {vn(thr[0])}</span><span><i style="background:{MI}"></i>Trung bình, {vn(thr[0])} đến {vn(thr[1])}</span>'
        f'<span><i style="background:{HI}"></i>Cao, từ {vn(thr[1])}</span><span><i style="background:#c9d6df;border-radius:50%"></i>Sạt lở lịch sử (mô phỏng)</span></div>',
        unsafe_allow_html=True)

    # ---- nút điều chỉnh kịch bản
    with st.container(key="g_ctrl"):
        with st.popover("Điều chỉnh kịch bản ▾"):
            st.slider("Hệ số mưa", 0.5, 2.0, step=0.1, key="scale")
            st.slider("Ngưỡng phân mức", 0.05, 0.95, value=(0.40, 0.70), step=0.05, key="thr")
            st.number_input("Ngưỡng mưa chú ý (mm trong 24 giờ)", 30, 400, step=10, key="rain_alert")
            st.checkbox("Ô lưới nguy cơ", key="show_grid")
            st.checkbox("Khu vực giám sát", key="show_areas")
            st.checkbox("Sạt lở lịch sử (mô phỏng)", key="show_hist")

    if ss.view != "3D":
        with st.container(key="g_mapmode"):
            with st.popover("Hiển thị ▾"):
                for base_option in BASEMAPS:
                    if st.button(base_option, key=f"basemap_{base_option}", width="stretch",
                                 type="primary" if ss.basemap == base_option else "secondary"):
                        ss.basemap = base_option
                        st.rerun(scope="fragment")

    # ---- nút phóng to, thu nhỏ, chế độ xem
    with st.container(key="g_zb"):
        b1, b2 = st.columns([1, 1.3], gap="small")
        if b1.button("3D", key="v3d", type="primary" if ss.view == "3D" else "secondary"):
            ss.view = "3D"
            st.rerun(scope="fragment")
        if b2.button("Bản đồ", key="v2d", type="primary" if ss.view != "3D" else "secondary"):
            ss.view = "Bản đồ"
            st.rerun(scope="fragment")

    # ---- thanh thời gian dạng viên ở đáy
    W, H = 430, 40
    xs = np.linspace(0, W, HOURS + 1)

    def poly(lower, upper, col):
        top = " ".join(f"{x:.1f},{H - H * u / tot:.1f}" for x, u in zip(xs, upper))
        bot = " ".join(f"{x:.1f},{H - H * l_ / tot:.1f}" for x, l_ in zip(xs[::-1], lower[::-1]))
        return f'<polygon points="{top} {bot}" fill="{col}" opacity=".85"/>'

    a1, a2 = CN[:, 0], CN[:, 0] + CN[:, 1]
    cx = W * t / HOURS
    area = (f'<svg viewBox="0 0 {W} {H}" class="ar" preserveAspectRatio="none">{poly(np.zeros(HOURS + 1), a1, LO)}'
            f'{poly(a1, a2, MI)}{poly(a2, np.full(HOURS + 1, tot), HI)}'
            f'<line x1="{cx:.1f}" x2="{cx:.1f}" y1="0" y2="{H}" stroke="#fff" stroke-width="2"/></svg>')
    with st.container(key="g_time"):
        ta, tb, tc, td = st.columns([1.1, 1.1, 5, 1.3], gap="small", vertical_alignment="center")
        with ta:
            if st.button("Dừng" if ss.play else "Phát", key="btn_play", type="primary"):
                ss.play = not ss.play
                st.rerun()
        with tb:
            st.markdown(f'<div class="clk"><b>{hh(t)}</b><span>giờ thứ {t} / {HOURS}</span></div>', unsafe_allow_html=True)
        with tc:
            st.markdown(area, unsafe_allow_html=True)
            st.slider("Giờ của kịch bản", 0, HOURS, key="t_step", format="%d giờ", label_visibility="collapsed")
        with td:
            st.markdown(f'<div class="mini2"><b>{hi_} ô</b>mức cao hiện tại</div>', unsafe_allow_html=True)


# chặn trình duyệt tự dịch trang (làm sai chữ tiếng Việt)
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

run = st.fragment(run_every=1.5 if st.session_state.get("play") else None)(monitor)
run()
