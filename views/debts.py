import pandas as pd
import streamlit as st

from services.database import (
    get_debts,
    add_debt,
    update_debt,
    delete_debt,
)

from utils.helpers import show_help


st.title("💳 부채 관리")


# ==================================================
# 1. 도움말
# ==================================================

show_help(
    "부채는 어떤 금액을 입력하나요?",
    (
        "현재 실제로 갚아야 하는 원금 잔액을 입력합니다. "
        "대출 한도나 처음 빌린 금액이 아니라 현재 남아 있는 부채를 기준으로 합니다."
    ),
    example=(
        "예: 처음 1억원을 빌렸지만 현재 원금이 8,000만원 남았다면 "
        "부채 잔액은 8,000만원으로 입력합니다."
    ),
)


show_help(
    "마이너스통장은 어떻게 입력하나요?",
    (
        "마이너스통장은 전체 한도가 아니라 현재 실제로 사용한 금액만 "
        "부채로 계산합니다. 한도는 참고용으로 별도 저장합니다."
    ),
    example=(
        "예: 한도 5,000만원 중 800만원 사용 "
        "→ 부채 800만원 / 한도 5,000만원"
    ),
)


# ==================================================
# 2. 부채 종류
# ==================================================

debt_types = [
    "주택담보대출",
    "전세대출",
    "신용대출",
    "마이너스통장",
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


# ==================================================
# 3. 부채 추가
# ==================================================

st.subheader("➕ 부채 추가")


new_debt_type = st.selectbox(
    "부채 종류",
    debt_types,
    key="new_debt_type",
)


with st.form(
    "add_debt_form",
    clear_on_submit=True,
):

    new_debt_name = st.text_input(
        "부채명",
        placeholder="예: 신한은행 마이너스통장",
    )


    new_debt_owner = st.selectbox(
        "소유자",
        owners,
    )


    if new_debt_type == "마이너스통장":

        new_balance = st.number_input(
            "현재 사용액",
            min_value=0,
            value=0,
            step=100000,
        )


        new_limit_amount = st.number_input(
            "한도",
            min_value=0,
            value=0,
            step=1000000,
        )

    else:

        new_balance = st.number_input(
            "현재 부채 잔액",
            min_value=0,
            value=0,
            step=100000,
        )


        new_limit_amount = 0


    new_interest_rate = st.number_input(
        "금리 (%)",
        min_value=0.0,
        value=0.0,
        step=0.1,
        format="%.2f",
    )


    new_debt_memo = st.text_input(
        "메모",
        placeholder="예: 변동금리",
    )


    add_debt_submit = (
        st.form_submit_button(
            "부채 추가",
            use_container_width=True,
        )
    )


if add_debt_submit:

    if not new_debt_name.strip():

        st.error(
            "부채명을 입력해주세요."
        )

    elif (
        new_debt_type == "마이너스통장"
        and new_limit_amount > 0
        and new_balance > new_limit_amount
    ):

        st.error(
            "현재 사용액은 마이너스통장 한도를 초과할 수 없습니다."
        )

    else:

        try:

            add_debt(
                name=new_debt_name,
                debt_type=new_debt_type,
                owner=new_debt_owner,
                balance=new_balance,
                interest_rate=(
                    new_interest_rate
                ),
                memo=new_debt_memo,
                limit_amount=(
                    new_limit_amount
                ),
            )

            st.success(
                "부채를 추가했습니다."
            )

            st.rerun()

        except TypeError:

            st.error(
                "services/database.py의 add_debt 함수가 "
                "limit_amount를 아직 받지 않도록 되어 있습니다. "
                "아래 database.py 수정 코드를 먼저 적용해주세요."
            )

        except Exception as e:

            st.error(
                f"부채를 추가하지 못했습니다: {e}"
            )


# ==================================================
# 4. 부채 조회
# ==================================================

st.divider()

debts = get_debts()


total_debt = sum(
    float(
        debt.get(
            "balance",
            0,
        )
        or 0
    )
    for debt in debts
)


st.subheader("📊 부채 현황")


st.metric(
    "현재 총 부채",
    f"₩{int(total_debt):,}",
)


show_help(
    "마이너스통장 한도도 총 부채에 들어가나요?",
    (
        "아니요. 총 부채에는 마이너스통장의 실제 사용액만 포함됩니다. "
        "사용하지 않은 한도는 빚이 아니기 때문에 총 부채에 포함하지 않습니다."
    ),
)


# ==================================================
# 5. 부채 표
# ==================================================

if debts:

    debt_rows = []


    for debt in debts:

        balance = float(
            debt.get(
                "balance",
                0,
            )
            or 0
        )


        limit_amount = float(
            debt.get(
                "limit_amount",
                0,
            )
            or 0
        )


        usage_rate = None


        if (
            debt.get("debt_type")
            == "마이너스통장"
            and limit_amount > 0
        ):

            usage_rate = (
                balance
                / limit_amount
            ) * 100


        debt_rows.append({
            "부채명":
                debt["name"],

            "종류":
                debt["debt_type"],

            "소유자":
                debt["owner"],

            "현재 잔액":
                balance,

            "한도":
                (
                    limit_amount
                    if limit_amount > 0
                    else None
                ),

            "한도 사용률":
                (
                    usage_rate
                    if usage_rate is not None
                    else None
                ),

            "금리":
                float(
                    debt.get(
                        "interest_rate",
                        0,
                    )
                    or 0
                ),

            "메모":
                debt.get(
                    "memo"
                )
                or "",
        })


    debt_df = pd.DataFrame(
        debt_rows
    )


    st.dataframe(
        debt_df,
        width="stretch",
        hide_index=True,
        column_config={

            "현재 잔액":
                st.column_config.NumberColumn(
                    "현재 잔액",
                    format="₩ %d",
                ),

            "한도":
                st.column_config.NumberColumn(
                    "한도",
                    format="₩ %d",
                ),

            "한도 사용률":
                st.column_config.NumberColumn(
                    "한도 사용률",
                    format="%.1f%%",
                ),

            "금리":
                st.column_config.NumberColumn(
                    "금리",
                    format="%.2f%%",
                ),
        },
    )


else:

    st.info(
        "등록된 부채가 없습니다."
    )

    st.stop()


# ==================================================
# 6. 부채 수정
# ==================================================

st.divider()

st.subheader("✏️ 부채 수정")


debt_options = {
    (
        f'{debt["name"]} · '
        f'{debt["debt_type"]} · '
        f'{debt["owner"]}'
    ):
    debt

    for debt in debts
}


selected_debt_label = (
    st.selectbox(
        "수정할 부채",
        list(
            debt_options.keys()
        ),
        key="edit_debt_select",
    )
)


selected_debt = (
    debt_options[
        selected_debt_label
    ]
)


selected_debt_id = (
    selected_debt["id"]
)


selected_debt_type = (
    selected_debt["debt_type"]
)


# ==================================================
# 수정 폼
# ==================================================

with st.form(
    f"edit_debt_form_{selected_debt_id}"
):

    edit_name = st.text_input(
        "부채명",
        value=(
            selected_debt["name"]
        ),
    )


    try:

        debt_type_index = (
            debt_types.index(
                selected_debt_type
            )
        )

    except ValueError:

        debt_type_index = 0


    edit_debt_type = st.selectbox(
        "부채 종류",
        debt_types,
        index=debt_type_index,
    )


    try:

        owner_index = (
            owners.index(
                selected_debt["owner"]
            )
        )

    except ValueError:

        owner_index = 0


    edit_owner = st.selectbox(
        "소유자",
        owners,
        index=owner_index,
    )


    current_balance = int(
        float(
            selected_debt.get(
                "balance",
                0,
            )
            or 0
        )
    )


    edit_balance = st.number_input(
        (
            "현재 사용액"
            if edit_debt_type
            == "마이너스통장"
            else "현재 부채 잔액"
        ),
        min_value=0,
        value=current_balance,
        step=100000,
    )


    current_limit = int(
        float(
            selected_debt.get(
                "limit_amount",
                0,
            )
            or 0
        )
    )


    if (
        edit_debt_type
        == "마이너스통장"
    ):

        edit_limit_amount = (
            st.number_input(
                "한도",
                min_value=0,
                value=current_limit,
                step=1000000,
            )
        )

    else:

        edit_limit_amount = 0


    edit_interest_rate = (
        st.number_input(
            "금리 (%)",
            min_value=0.0,
            value=float(
                selected_debt.get(
                    "interest_rate",
                    0,
                )
                or 0
            ),
            step=0.1,
            format="%.2f",
        )
    )


    edit_memo = st.text_input(
        "메모",
        value=(
            selected_debt.get(
                "memo"
            )
            or ""
        ),
    )


    edit_submit = (
        st.form_submit_button(
            "수정 저장",
            use_container_width=True,
        )
    )


if edit_submit:

    if not edit_name.strip():

        st.error(
            "부채명을 입력해주세요."
        )

    elif (
        edit_debt_type
        == "마이너스통장"
        and
        edit_limit_amount > 0
        and
        edit_balance
        > edit_limit_amount
    ):

        st.error(
            "현재 사용액은 "
            "마이너스통장 한도를 초과할 수 없습니다."
        )

    else:

        try:

            update_debt(
                debt_id=(
                    selected_debt_id
                ),
                name=edit_name,
                debt_type=(
                    edit_debt_type
                ),
                owner=edit_owner,
                balance=edit_balance,
                interest_rate=(
                    edit_interest_rate
                ),
                memo=edit_memo,
                limit_amount=(
                    edit_limit_amount
                ),
            )

            st.success(
                "부채 정보를 수정했습니다."
            )

            st.rerun()

        except TypeError:

            st.error(
                "services/database.py의 update_debt 함수가 "
                "limit_amount를 아직 받지 않도록 되어 있습니다."
            )

        except Exception as e:

            st.error(
                f"부채 정보를 수정하지 못했습니다: {e}"
            )


# ==================================================
# 7. 마이너스통장 상세
# ==================================================

if (
    selected_debt_type
    == "마이너스통장"
):

    balance = float(
        selected_debt.get(
            "balance",
            0,
        )
        or 0
    )


    limit_amount = float(
        selected_debt.get(
            "limit_amount",
            0,
        )
        or 0
    )


    st.divider()

    st.subheader(
        "📉 마이너스통장 사용 현황"
    )


    if limit_amount > 0:

        usage_rate = (
            balance
            / limit_amount
        ) * 100


        available_limit = max(
            limit_amount
            - balance,
            0,
        )


        col1, col2, col3 = (
            st.columns(3)
        )


        with col1:

            st.metric(
                "현재 사용액",
                f"₩{int(balance):,}",
            )


        with col2:

            st.metric(
                "전체 한도",
                (
                    f"₩"
                    f"{int(limit_amount):,}"
                ),
            )


        with col3:

            st.metric(
                "남은 한도",
                (
                    f"₩"
                    f"{int(available_limit):,}"
                ),
            )


        st.progress(
            min(
                usage_rate / 100,
                1.0,
            )
        )


        st.caption(
            f"한도 사용률 "
            f"{usage_rate:.1f}%"
        )


    else:

        st.info(
            "한도를 입력하면 "
            "한도 사용률과 남은 한도를 확인할 수 있습니다."
        )


# ==================================================
# 8. 부채 삭제
# ==================================================

st.divider()

st.subheader(
    "🗑 부채 삭제"
)


if (
    "debt_delete_target"
    not in st.session_state
):

    st.session_state[
        "debt_delete_target"
    ] = None


if (
    st.session_state[
        "debt_delete_target"
    ]
    != selected_debt_id
):

    st.session_state[
        "debt_delete_confirm"
    ] = False

    st.session_state[
        "debt_delete_target"
    ] = selected_debt_id


if (
    "debt_delete_confirm"
    not in st.session_state
):

    st.session_state[
        "debt_delete_confirm"
    ] = False


if not st.session_state[
    "debt_delete_confirm"
]:

    if st.button(
        "선택한 부채 삭제",
        key=(
            f"delete_debt_button_"
            f"{selected_debt_id}"
        ),
    ):

        st.session_state[
            "debt_delete_confirm"
        ] = True

        st.rerun()


else:

    st.warning(
        f"'{selected_debt['name']}'을 "
        "정말 삭제하시겠습니까?"
    )


    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "삭제 확인",
            type="primary",
            key=(
                f"confirm_debt_delete_"
                f"{selected_debt_id}"
            ),
            use_container_width=True,
        ):

            delete_debt(
                selected_debt_id
            )

            st.session_state[
                "debt_delete_confirm"
            ] = False

            st.session_state[
                "debt_delete_target"
            ] = None

            st.rerun()


    with col2:

        if st.button(
            "취소",
            key=(
                f"cancel_debt_delete_"
                f"{selected_debt_id}"
            ),
            use_container_width=True,
        ):

            st.session_state[
                "debt_delete_confirm"
            ] = False

            st.rerun()