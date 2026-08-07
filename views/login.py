import streamlit as st

from services.database import login


st.title("🔐 우리집 자산관리")

st.write("로그인해주세요.")


with st.form("login_form"):

    email = st.text_input(
        "이메일"
    )

    password = st.text_input(
        "비밀번호",
        type="password",
    )

    submitted = st.form_submit_button(
        "로그인",
        use_container_width=True,
    )


    if submitted:

        if not email or not password:

            st.error(
                "이메일과 비밀번호를 입력해주세요."
            )

        else:

            try:

                response = login(
                    email,
                    password,
                )

                if response.user:

                    st.session_state.logged_in = True
                    st.session_state.user_email = (
                        response.user.email
                    )

                    st.success(
                        "로그인되었습니다."
                    )

                    st.rerun()

            except Exception:

                st.error(
                    "이메일 또는 비밀번호가 올바르지 않습니다."
                )