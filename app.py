import streamlit as st

from services.database import logout


st.set_page_config(
    page_title="우리집 자산관리",
    page_icon="💰",
    layout="wide",
)


# -------------------------------------------------
# 로그인 상태 초기화
# -------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# -------------------------------------------------
# 로그인하지 않은 경우
# -------------------------------------------------

if not st.session_state.logged_in:

    login_page = st.Page(
        "views/login.py",
        title="로그인",
        icon="🔐",
    )

    navigation = st.navigation(
        [login_page]
    )

    navigation.run()

    st.stop()


# -------------------------------------------------
# 로그인한 경우
# -------------------------------------------------

pages = {
    "자산관리": [

        st.Page(
            "views/dashboard.py",
            title="대시보드",
            icon="📊",
            default=True,
        ),

        st.Page(
            "views/assets.py",
            title="자산",
            icon="💰",
        ),

        st.Page(
            "views/debts.py",
            title="부채",
            icon="💳",
        ),

        st.Page(
            "views/transactions.py",
            title="거래내역",
            icon="🧾",
        ),

    ]
}


navigation = st.navigation(
    pages
)


# -------------------------------------------------
# 사이드바 사용자 정보
# -------------------------------------------------

with st.sidebar:

    st.divider()

    st.write(
        f"👤 {st.session_state.get('user_email', '')}"
    )

    if st.button(
        "로그아웃",
        use_container_width=True,
    ):

        logout()

        st.session_state.logged_in = False
        st.session_state.user_email = ""

        st.rerun()


navigation.run()