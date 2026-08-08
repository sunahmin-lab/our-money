import streamlit as st

from services.database import (
    logout,
    get_current_user,
)


# ==================================================
# Streamlit 설정
# ==================================================

st.set_page_config(
    page_title="우리집 자산관리",
    page_icon="💰",
    layout="wide",
)


# ==================================================
# 세션 초기화
# ==================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


# ==================================================
# 저장된 토큰이 있다면 사용자 확인
# ==================================================

if (
    not st.session_state.logged_in
    and
    st.session_state.get(
        "access_token"
    )
):

    user = get_current_user()

    if user:

        st.session_state[
            "logged_in"
        ] = True

        st.session_state[
            "user_email"
        ] = user.email


# ==================================================
# 로그인 전
# ==================================================

if not st.session_state.logged_in:

    login_page = st.Page(
        "views/login.py",
        title="로그인",
        icon="🔐",
    )

    navigation = (
        st.navigation(
            [login_page]
        )
    )

    navigation.run()

    st.stop()


# ==================================================
# 로그인 후 메뉴
# ==================================================

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

        st.Page(
            "views/funds.py",
            title="목적자금",
            icon="🎯",
        ),

        st.Page(
            "views/settings.py",
            title="설정",
            icon="⚙️",
        ),
    ]
}


navigation = st.navigation(
    pages
)


# ==================================================
# 사이드바
# ==================================================

with st.sidebar:

    st.divider()

    st.caption(
        "로그인 사용자"
    )

    st.write(
        f"👤 "
        f"{st.session_state.get('user_email', '')}"
    )


    if st.button(
        "로그아웃",
        use_container_width=True,
    ):

        logout()

        st.rerun()


navigation.run()