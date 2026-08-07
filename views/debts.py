import streamlit as st
import pandas as pd

from services.database import (
    get_debts,
    add_debt,
    update_debt,
    delete_debt,
)
# -------------------------
# 자산 부채
# -------------------------

st.divider()
st.header("💳 부채 관리")

st.subheader("➕ 부채 추가")

with st.form("debt_form"):

    debt_type = st.selectbox(
        "부채 종류",
        [
            "주택담보대출",
            "전세대출",
            "신용대출",
            "자동차대출",
            "학자금대출",
            "카드대금",
            "기타",
        ],
    )

    debt_name = st.text_input("부채명")

    debt_owner = st.selectbox(
        "부채 소유자",
        [
            "나",
            "남편",
            "공동",
        ],
    )

    balance = st.number_input(
        "현재 남은 원금",
        min_value=0,
        step=10000,
    )

    interest_rate = st.number_input(
        "금리 (%)",
        min_value=0.0,
        step=0.1,
        format="%.2f",
    )

    debt_memo = st.text_input("부채 메모")

    debt_submitted = st.form_submit_button("부채 저장")

    if debt_submitted:

        if not debt_name:
            st.error("부채명을 입력해주세요.")

        else:
            add_debt(
                name=debt_name,
                debt_type=debt_type,
                owner=debt_owner,
                balance=balance,
                interest_rate=interest_rate,
                memo=debt_memo,
            )

            st.success("부채가 저장되었습니다.")
            st.rerun()

st.subheader("💳 현재 부채")

debts = get_debts()

if not debts:
    st.info("등록된 부채가 없습니다.")

else:
    total_debts = sum(
        float(debt["balance"])
        for debt in debts
    )

    st.metric(
        "총 부채",
        f"₩{int(total_debts):,}",
    )

    debt_df = pd.DataFrame(debts)

    display_debt_df = debt_df[
        [
            "debt_type",
            "name",
            "owner",
            "balance",
            "interest_rate",
            "memo",
        ]
    ].copy()

    display_debt_df = display_debt_df.rename(
        columns={
            "debt_type": "부채 종류",
            "name": "부채명",
            "owner": "소유자",
            "balance": "남은 원금",
            "interest_rate": "금리",
            "memo": "메모",
        }
    )

    display_debt_df["남은 원금"] = display_debt_df["남은 원금"].astype(float)
    display_debt_df["금리"] = display_debt_df["금리"].astype(float)

    st.dataframe(
        display_debt_df,
        width="stretch",
        hide_index=True,
        column_config={
            "남은 원금": st.column_config.NumberColumn(
                "남은 원금",
                format="₩ %d",
            ),
            "금리": st.column_config.NumberColumn(
                "금리",
                format="%.2f%%",
            ),
        },
    )

st.divider()
st.subheader("✏️ 부채 수정 / 삭제")

debts = get_debts()

if debts:

    debt_map = {
        f'{debt["name"]} / {debt["owner"]} / {int(float(debt["balance"])):,}원': debt
        for debt in debts
    }

    selected_label = st.selectbox(
        "수정할 부채 선택",
        list(debt_map.keys()),
    )

    selected_debt = debt_map[selected_label]

    debt_types = [
        "주택담보대출",
        "전세대출",
        "신용대출",
        "자동차대출",
        "학자금대출",
        "카드대금",
        "기타",
    ]

    owners = [
        "나",
        "남편",
        "공동",
    ]

    with st.form("edit_debt_form"):

        edit_name = st.text_input(
            "부채명",
            value=selected_debt["name"],
        )

        current_debt_type = selected_debt["debt_type"]

        edit_debt_type = st.selectbox(
            "부채 종류",
            debt_types,
            index=(
                debt_types.index(current_debt_type)
                if current_debt_type in debt_types
                else 0
            ),
        )

        current_owner = selected_debt["owner"]

        edit_owner = st.selectbox(
            "소유자",
            owners,
            index=(
                owners.index(current_owner)
                if current_owner in owners
                else 0
            ),
        )

        edit_balance = st.number_input(
            "현재 남은 원금",
            min_value=0,
            value=int(float(selected_debt["balance"])),
            step=10000,
        )

        edit_interest_rate = st.number_input(
            "금리 (%)",
            min_value=0.0,
            value=float(selected_debt["interest_rate"] or 0),
            step=0.1,
            format="%.2f",
        )

        edit_memo = st.text_input(
            "메모",
            value=selected_debt["memo"] or "",
        )

        update_submitted = st.form_submit_button(
            "수정 저장",
            use_container_width=True,
        )

        if update_submitted:

            update_debt(
                debt_id=selected_debt["id"],
                name=edit_name,
                debt_type=edit_debt_type,
                owner=edit_owner,
                balance=edit_balance,
                interest_rate=edit_interest_rate,
                memo=edit_memo,
            )

            st.success("부채 정보가 수정되었습니다.")
            st.rerun()


    # -------------------------
    # 삭제 확인
    # -------------------------

    if "debt_delete_confirm" not in st.session_state:
        st.session_state.debt_delete_confirm = False


    if not st.session_state.debt_delete_confirm:

        if st.button(
            "🗑️ 선택한 부채 삭제",
            key="delete_debt_button",
        ):
            st.session_state.debt_delete_confirm = True
            st.rerun()

    else:

        st.warning(
            f'정말 "{selected_debt["name"]}" 부채를 삭제하시겠습니까?'
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "예, 삭제합니다",
                type="primary",
                use_container_width=True,
                key="confirm_delete_debt",
            ):

                delete_debt(
                    selected_debt["id"]
                )

                st.session_state.debt_delete_confirm = False

                st.success("부채가 삭제되었습니다.")
                st.rerun()

        with col2:

            if st.button(
                "아니오, 취소",
                use_container_width=True,
                key="cancel_delete_debt",
            ):

                st.session_state.debt_delete_confirm = False
                st.rerun()

else:

    st.info(
        "수정하거나 삭제할 부채가 없습니다."
    )