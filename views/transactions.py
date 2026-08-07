import pandas as pd
import streamlit as st

from services.database import (
    get_transactions,
    add_transaction,
    update_transaction,
    delete_transaction,
)


st.title("🧾 거래내역")


# -------------------------
# 거래 추가
# -------------------------

st.subheader("➕ 거래 추가")

with st.form("transaction_form"):

    transaction_date = st.date_input(
        "날짜"
    )

    transaction_type = st.selectbox(
        "구분",
        [
            "수입",
            "지출",
        ],
    )

    income_categories = [
        "월급",
        "상여금",
        "부수입",
        "이자",
        "배당금",
        "환급",
        "기타수입",
    ]

    expense_categories = [
        "식비",
        "카페",
        "생활비",
        "교통",
        "쇼핑",
        "여행",
        "의료",
        "보험",
        "통신",
        "교육",
        "대출상환",
        "주거",
        "경조사",
        "취미",
        "기타지출",
    ]

    if transaction_type == "수입":
        category_options = income_categories
    else:
        category_options = expense_categories

    category = st.selectbox(
        "카테고리",
        category_options,
    )

    owner = st.selectbox(
        "사용자",
        [
            "나",
            "남편",
            "공동",
        ],
    )

    amount = st.number_input(
        "금액",
        min_value=0,
        step=1000,
    )

    memo = st.text_input(
        "메모"
    )

    submitted = st.form_submit_button(
        "저장",
        use_container_width=True,
    )

    if submitted:

        if amount <= 0:
            st.error("금액을 입력해주세요.")

        else:
            add_transaction(
                transaction_date=transaction_date,
                transaction_type=transaction_type,
                category=category,
                owner=owner,
                amount=amount,
                memo=memo,
            )

            st.success("거래내역이 저장되었습니다.")
            st.rerun()


# -------------------------
# 거래 목록
# -------------------------

st.divider()
st.subheader("📋 거래내역")

transactions = get_transactions()

if not transactions:
    st.info("아직 거래내역이 없습니다.")

else:

    df = pd.DataFrame(transactions)

    df["amount"] = (
        df["amount"]
        .astype(float)
        .astype(int)
    )

    df["금액"] = df["amount"].apply(
        lambda x: f"{int(float(x)):,}원"
    )
    
    st.dataframe(
        df[
            [
                "transaction_date",
                "transaction_type",
                "category",
                "owner",
                "금액",
                "memo",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.subheader("✏️ 거래 수정 / 삭제")

transactions = get_transactions()

if transactions:

    transaction_map = {
        f'{t["transaction_date"]} / {t["transaction_type"]} / {t["category"]} / {int(float(t["amount"])):,}원': t
        for t in transactions
    }

    selected_label = st.selectbox(
        "수정할 거래 선택",
        list(transaction_map.keys()),
    )

    selected_transaction = transaction_map[selected_label]

    transaction_types = ["수입", "지출"]

    income_categories = [
        "월급",
        "상여금",
        "부수입",
        "이자",
        "배당금",
        "환급",
        "기타수입",
    ]

    expense_categories = [
        "식비",
        "카페",
        "생활비",
        "교통",
        "쇼핑",
        "여행",
        "의료",
        "보험",
        "통신",
        "교육",
        "대출상환",
        "주거",
        "경조사",
        "취미",
        "기타지출",
    ]

    owners = ["나", "남편", "공동"]

    with st.form("edit_transaction_form"):

        edit_date = st.date_input(
            "날짜",
            value=__import__("datetime").date.fromisoformat(
                selected_transaction["transaction_date"]
            ),
        )

        edit_type = st.selectbox(
            "구분",
            transaction_types,
            index=transaction_types.index(
                selected_transaction["transaction_type"]
            ),
        )

        if edit_type == "수입":
            edit_category_options = income_categories
        else:
            edit_category_options = expense_categories

        current_category = selected_transaction["category"]

        if current_category in edit_category_options:
            category_index = edit_category_options.index(current_category)
        else:
            category_index = 0

        edit_category = st.selectbox(
            "카테고리",
            edit_category_options,
            index=category_index,
        )

        edit_owner = st.selectbox(
            "사용자",
            owners,
            index=owners.index(
                selected_transaction["owner"]
            )
            if selected_transaction["owner"] in owners
            else 0,
        )

        edit_amount = st.number_input(
            "금액",
            min_value=0,
            value=int(float(selected_transaction["amount"])),
            step=1000,
        )

        edit_memo = st.text_input(
            "메모",
            value=selected_transaction["memo"] or "",
        )

        update_submitted = st.form_submit_button(
            "수정 저장",
            use_container_width=True,
        )

        if update_submitted:

            update_transaction(
                transaction_id=selected_transaction["id"],
                transaction_date=edit_date,
                transaction_type=edit_type,
                category=edit_category,
                owner=edit_owner,
                amount=edit_amount,
                memo=edit_memo,
            )

            st.success("거래내역이 수정되었습니다.")
            st.rerun()


    if "transaction_delete_confirm" not in st.session_state:
        st.session_state.transaction_delete_confirm = False


    if not st.session_state.transaction_delete_confirm:

        if st.button("🗑️ 선택한 거래 삭제"):
            st.session_state.transaction_delete_confirm = True
            st.rerun()

    else:

        st.warning(
            f'정말 "{selected_transaction["category"]} / '
            f'{int(float(selected_transaction["amount"])):,}원" 거래를 삭제하시겠습니까?'
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "예, 삭제합니다",
                type="primary",
                use_container_width=True,
            ):

                delete_transaction(
                    selected_transaction["id"]
                )

                st.session_state.transaction_delete_confirm = False

                st.success("삭제되었습니다.")
                st.rerun()

        with col2:
            if st.button(
                "아니오, 취소",
                use_container_width=True,
            ):

                st.session_state.transaction_delete_confirm = False
                st.rerun()

else:
    st.info("수정하거나 삭제할 거래내역이 없습니다.")