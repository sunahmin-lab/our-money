import streamlit as st


def show_help(
    title,
    text,
    example=None,
    warning=None,
):
    with st.expander(f"💡 {title}"):

        st.write(text)

        if example:
            st.caption(example)

        if warning:
            st.warning(warning)