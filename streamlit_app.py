import streamlit as st

st.set_page_config(
    page_title="Trung tâm giám sát nguy cơ sạt lở đất",
    page_icon="⛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.session_state["_root_navigation"] = True

page = st.navigation(
    [
        st.Page("app/main.py", title="Tổng quan", icon=":material/landscape:", default=True),
        st.Page("app/pages/2_AI_Evaluation.py", title="Đánh giá AI", icon=":material/analytics:"),
    ],
    position="sidebar",
)
page.run()