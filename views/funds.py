from datetime import date

import pandas as pd
import streamlit as st

from services.database import (
    get_funds,
    add_fund,
    update_fund,
    delete_fund,
    get_fund_transactions,
    add_fund_transaction,
    delete_fund_transaction,
    get_fund_balance,
)

from utils.helpers import show_help


st.title("🎯 목적자금")


# ==================================================
# 1. 목적자금 추가
# ==================================================

st.subheader("➕ 목적자금 추가")


show_help(
    "목적자금이 뭐예요?",
    (
        "생활비와 별도로 특정 목적을 위해 따로 확보해두는 돈입니다. "
        "예를 들어 여행자금, 비상금, 자동차 교체자금 등을 "
        "목적자금으로 관리할 수 있습니다."
    ),
    example=(
        "예: 여행자금 → 매월 500,000원 적립"
    ),
)


with st.form(
    "add_fund_form",
    clear_on_submit=True,
):

    fund_name = st.text_input(
        "목적자금명",
        placeholder="예: 여행자금",
    )

    monthly_target = st.number_input(
        "매월 적립 목표",
        min_value=0,
        value=500000,
        step=100000,
    )

    fund_memo = st.text_input(
        "메모",
        placeholder="예: 부부 공동 여행자금",
    )

    fund_submit = st.form_submit_button(
        "목적자금 추가",
        use_container_width=True,
    )


if fund_submit:

    if not fund_name.strip():

        st.error(
            "목적자금명을 입력해주세요."
        )

    else:

        try:

            add_fund(
                name=fund_name,
                monthly_target=monthly_target,
                memo=fund_memo,
            )

            st.success(
                "목적자금을 추가했습니다."
            )

            st.rerun()

        except Exception as e:

            st.error(
                "목적자금을 추가하지 못했습니다. "
                "같은 이름이 이미 등록되어 있는지 확인해주세요."
            )


# ==================================================
# 2. 목적자금 조회
# ==================================================

st.divider()


funds = get_funds()


if not funds:

    st.info(
        "아직 등록된 목적자금이 없습니다."
    )

    st.stop()


fund_options = {
    fund["name"]: fund
    for fund in funds
}


selected_fund_name = st.selectbox(
    "관리할 목적자금",
    list(fund_options.keys()),
    key="fund_select",
)


selected_fund = fund_options[
    selected_fund_name
]


fund_id = selected_fund["id"]


# ==================================================
# 3. 목적자금 현황
# ==================================================

fund_transactions = (
    get_fund_transactions(
        fund_id
    )
)


current_balance = (
    get_fund_balance(
        fund_id
    )
)


today = date.today()


monthly_target = float(
    selected_fund.get(
        "monthly_target",
        0,
    )
    or 0
)


current_month_contribution = 0
current_month_usage = 0


for transaction in fund_transactions:

    transaction_date = date.fromisoformat(
        transaction[
            "transaction_date"
        ]
    )

    if (
        transaction_date.year
        == today.year
        and
        transaction_date.month
        == today.month
    ):

        amount = float(
            transaction["amount"]
        )

        if (
            transaction[
                "transaction_type"
            ]
            == "적립"
        ):

            current_month_contribution += (
                amount
            )

        elif (
            transaction[
                "transaction_type"
            ]
            == "사용"
        ):

            current_month_usage += (
                amount
            )


st.subheader(
    f"🎯 {selected_fund_name}"
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "현재 배정 잔액",
        f"₩{int(current_balance):,}",
    )


with col2:

    st.metric(
        "이번 달 적립",
        (
            f"₩"
            f"{int(current_month_contribution):,}"
        ),
    )


with col3:

    st.metric(
        "월 적립 목표",
        (
            f"₩"
            f"{int(monthly_target):,}"
        ),
    )


# ==================================================
# 목적자금 / 총자산 도움말
# ==================================================

show_help(
    "목적자금은 총 자산에 포함되나요?",
    (
        "목적자금 자체를 총 자산에 별도로 더하지는 않습니다. "
        "여행통장처럼 실제 돈이 들어 있는 계좌를 자산 메뉴에 "
        "등록했다면 그 금액은 이미 총 자산에 포함되어 있습니다. "
        "목적자금 페이지에서는 그 돈 중 얼마를 특정 목적으로 "
        "확보해두었는지를 따로 관리합니다."
    ),
    example=(
        "예: 여행통장 잔액 4,500,000원을 자산에 등록했다면 "
        "총 자산에는 이미 4,500,000원이 포함되어 있습니다."
    ),
    warning=(
        "목적자금 잔액을 총 자산에 다시 더하면 "
        "같은 돈이 두 번 계산됩니다."
    ),
)


# ==================================================
# 목표 달성률
# ==================================================

if monthly_target > 0:

    achievement_rate = (
        current_month_contribution
        / monthly_target
    ) * 100


    progress_value = min(
        current_month_contribution
        / monthly_target,
        1.0,
    )


    st.progress(
        progress_value
    )


    if (
        current_month_contribution
        >= monthly_target
    ):

        st.success(
            f"이번 달 적립 목표 달성! "
            f"{achievement_rate:.1f}%"
        )

    else:

        remaining_target = (
            monthly_target
            - current_month_contribution
        )

        st.caption(
            f"이번 달 목표 달성률 "
            f"{achievement_rate:.1f}% · "
            f"₩{int(remaining_target):,} 남음"
        )


if current_month_usage > 0:

    st.caption(
        "이번 달 목적자금 사용: "
        f"₩{int(current_month_usage):,}"
    )


# ==================================================
# 4. 적립 / 사용 기록
# ==================================================

st.divider()

st.subheader(
    "💰 적립 / 사용 기록"
)


show_help(
    "적립과 사용은 어떻게 기록하나요?",
    (
        "공동 생활통장에서 여행통장으로 돈을 옮겼다면 "
        "'적립'으로 기록합니다. "
        "여행자금에서 실제 여행을 위해 돈을 사용했다면 "
        "'사용'으로 기록합니다."
    ),
    example=(
        "예: 매월 여행통장으로 500,000원 이동 "
        "→ 적립 500,000원"
    ),
)


with st.form(
    "fund_transaction_form",
    clear_on_submit=True,
):

    fund_transaction_date = (
        st.date_input(
            "날짜",
            value=date.today(),
        )
    )


    fund_transaction_type = (
        st.radio(
            "구분",
            [
                "적립",
                "사용",
            ],
            horizontal=True,
        )
    )


    fund_transaction_amount = (
        st.number_input(
            "금액",
            min_value=0,
            value=0,
            step=100000,
        )
    )


    fund_transaction_memo = (
        st.text_input(
            "메모",
            placeholder=(
                "예: 8월 여행자금 적립"
            ),
        )
    )


    fund_transaction_submit = (
        st.form_submit_button(
            "기록 추가",
            use_container_width=True,
        )
    )


if fund_transaction_submit:

    if fund_transaction_amount <= 0:

        st.error(
            "금액을 입력해주세요."
        )

    elif (
        fund_transaction_type
        == "사용"
        and
        fund_transaction_amount
        > current_balance
    ):

        st.error(
            "현재 목적자금 잔액보다 "
            "큰 금액은 사용할 수 없습니다."
        )

    else:

        add_fund_transaction(
            fund_id=fund_id,
            transaction_date=(
                fund_transaction_date
            ),
            transaction_type=(
                fund_transaction_type
            ),
            amount=(
                fund_transaction_amount
            ),
            memo=(
                fund_transaction_memo
            ),
        )

        st.success(
            "기록을 추가했습니다."
        )

        st.rerun()


# ==================================================
# 5. 입출금 내역
# ==================================================

st.divider()

st.subheader(
    "📋 목적자금 내역"
)


if fund_transactions:

    fund_df = pd.DataFrame(
        fund_transactions
    )


    fund_df[
        "transaction_date"
    ] = pd.to_datetime(
        fund_df[
            "transaction_date"
        ]
    )


    fund_df[
        "amount"
    ] = (
        fund_df["amount"]
        .astype(float)
    )


    display_fund_df = fund_df[
        [
            "transaction_date",
            "transaction_type",
            "amount",
            "memo",
        ]
    ].copy()


    display_fund_df = (
        display_fund_df.rename(
            columns={
                "transaction_date":
                    "날짜",

                "transaction_type":
                    "구분",

                "amount":
                    "금액",

                "memo":
                    "메모",
            }
        )
    )


    st.dataframe(
        display_fund_df,
        width="stretch",
        hide_index=True,
        column_config={

            "날짜":
                st.column_config.DateColumn(
                    "날짜",
                    format="YYYY-MM-DD",
                ),

            "금액":
                st.column_config.NumberColumn(
                    "금액",
                    format="₩ %d",
                ),
        },
    )


    # ==================================================
    # 기록 삭제
    # ==================================================

    st.markdown(
        "#### 🗑 기록 삭제"
    )


    transaction_options = {
        (
            f'{item["transaction_date"]} · '
            f'{item["transaction_type"]} · '
            f'₩{int(float(item["amount"])):,} · '
            f'{item.get("memo") or ""}'
        ):
        item["id"]

        for item
        in fund_transactions
    }


    delete_transaction_label = (
        st.selectbox(
            "삭제할 기록",
            list(
                transaction_options.keys()
            ),
            key=(
                "delete_fund_transaction_select"
            ),
        )
    )


    if (
        "fund_transaction_delete_confirm"
        not in st.session_state
    ):

        st.session_state[
            "fund_transaction_delete_confirm"
        ] = False


    if not st.session_state[
        "fund_transaction_delete_confirm"
    ]:

        if st.button(
            "선택한 기록 삭제",
            key=(
                "delete_fund_transaction_button"
            ),
        ):

            st.session_state[
                "fund_transaction_delete_confirm"
            ] = True

            st.rerun()


    else:

        st.warning(
            f"{delete_transaction_label} "
            "기록을 정말 삭제하시겠습니까?"
        )


        col1, col2 = st.columns(2)


        with col1:

            if st.button(
                "삭제 확인",
                type="primary",
                key=(
                    "confirm_fund_transaction_delete"
                ),
                use_container_width=True,
            ):

                delete_fund_transaction(
                    transaction_options[
                        delete_transaction_label
                    ]
                )

                st.session_state[
                    "fund_transaction_delete_confirm"
                ] = False

                st.rerun()


        with col2:

            if st.button(
                "취소",
                key=(
                    "cancel_fund_transaction_delete"
                ),
                use_container_width=True,
            ):

                st.session_state[
                    "fund_transaction_delete_confirm"
                ] = False

                st.rerun()


else:

    st.info(
        "아직 입출금 기록이 없습니다."
    )


# ==================================================
# 6. 목적자금 설정 수정
# ==================================================

st.divider()

st.subheader(
    "⚙️ 목적자금 설정"
)


with st.form(
    f"edit_fund_form_{fund_id}"
):

    edit_fund_name = (
        st.text_input(
            "목적자금명",
            value=(
                selected_fund["name"]
            ),
        )
    )


    edit_monthly_target = (
        st.number_input(
            "월 적립 목표",
            min_value=0,
            value=int(
                float(
                    selected_fund[
                        "monthly_target"
                    ]
                )
            ),
            step=100000,
        )
    )


    edit_fund_memo = (
        st.text_input(
            "메모",
            value=(
                selected_fund.get(
                    "memo"
                )
                or ""
            ),
        )
    )


    edit_fund_submit = (
        st.form_submit_button(
            "목적자금 설정 저장",
            use_container_width=True,
        )
    )


if edit_fund_submit:

    if not edit_fund_name.strip():

        st.error(
            "목적자금명을 입력해주세요."
        )

    else:

        update_fund(
            fund_id=fund_id,
            name=edit_fund_name,
            monthly_target=(
                edit_monthly_target
            ),
            memo=edit_fund_memo,
        )

        st.success(
            "목적자금 설정을 수정했습니다."
        )

        st.rerun()


# ==================================================
# 7. 목적자금 삭제
# ==================================================

st.divider()

st.subheader(
    "🗑 목적자금 삭제"
)


if (
    "fund_delete_confirm"
    not in st.session_state
):

    st.session_state[
        "fund_delete_confirm"
    ] = False


if not st.session_state[
    "fund_delete_confirm"
]:

    if st.button(
        "이 목적자금 삭제",
        key="delete_fund_button",
    ):

        st.session_state[
            "fund_delete_confirm"
        ] = True

        st.rerun()


else:

    st.warning(
        f"'{selected_fund_name}'을 삭제하면 "
        "이 목적자금의 모든 적립/사용 기록도 함께 삭제됩니다."
    )


    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "삭제 확인",
            type="primary",
            key="confirm_delete_fund",
            use_container_width=True,
        ):

            delete_fund(
                fund_id
            )

            st.session_state[
                "fund_delete_confirm"
            ] = False

            st.rerun()


    with col2:

        if st.button(
            "취소",
            key="cancel_delete_fund",
            use_container_width=True,
        ):

            st.session_state[
                "fund_delete_confirm"
            ] = False

            st.rerun()