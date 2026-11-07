import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(
    page_title="Trung tâm giám sát nguy cơ sạt lở đất",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.session_state["_root_navigation"] = True

page = st.navigation(
    [
        st.Page("app/main.py", title="Tổng quan", icon=":material/landscape:", default=True),
        st.Page("app/pages/2_AI_Evaluation.py", title="Đánh giá AI", icon=":material/analytics:"),
    ],
    position="top",
)
page.run()

if __name__ == "__main__" and not getattr(st, "runtime", None) or not st.runtime.exists():
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", str(Path(__file__).resolve())]
    sys.exit(stcli.main())
