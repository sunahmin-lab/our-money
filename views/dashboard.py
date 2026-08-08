import calendar
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from services.database import (
    get_assets,
    get_debts,
    get_transactions,
    get_net_worth_history,
    add_net_worth_snapshot,
    delete_net_worth_snapshot,
    get_cards,
    get_funds,
    get_fund_transactions,
    get_household_settings,
)

from utils.helpers import show_help


st.title("📊 우리집 자산 현황")


# ==================================================
# 1. 기본 데이터 조회
# ==================================================

assets = get_assets()
debts = get_debts()
transactions = get_transactions()
cards = get_cards()
funds = get_funds()

household_settings = get_household_settings()

today = date.today()

current_year = today.year
current_month = today.month


# ==================================================
# 2. 총 자산 / 총 부채 / 순자산
# ==================================================

total_assets = sum(
    float(asset["current_value"])
    for asset in assets
)

total_debts = sum(
    float(debt["balance"])
    for debt in debts
)

net_worth = (
    total_assets
    - total_debts
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "총 자산",
        f"₩{int(total_assets):,}",
    )


with col2:

    st.metric(
        "총 부채",
        f"₩{int(total_debts):,}",
    )


with col3:

    st.metric(
        "순자산",
        f"₩{int(net_worth):,}",
    )


show_help(
    "총 자산과 순자산은 어떻게 계산하나요?",
    (
        "총 자산은 자산 메뉴에 등록한 실제 계좌, 예금, 적금, "
        "주식, 부동산 등의 현재 가치를 합산합니다. "
        "순자산은 총 자산에서 총 부채를 뺀 금액입니다."
    ),
    example=(
        "예: 총 자산 1억원 - 총 부채 3천만원 "
        "= 순자산 7천만원"
    ),
    warning=(
        "여행자금이나 용돈을 별도의 자산으로 다시 더하지 않습니다. "
        "실제 통장 잔액이 자산에 등록되어 있다면 이미 총 자산에 포함되어 있습니다."
    ),
)


# ==================================================
# 3. 이번 달 거래 계산
# ==================================================

monthly_income = 0
monthly_expense = 0


for transaction in transactions:

    transaction_date = date.fromisoformat(
        transaction["transaction_date"]
    )

    if (
        transaction_date.year == current_year
        and
        transaction_date.month == current_month
    ):

        amount = float(
            transaction["amount"]
        )

        if (
            transaction["transaction_type"]
            == "수입"
        ):

            monthly_income += amount

        elif (
            transaction["transaction_type"]
            == "지출"
        ):

            monthly_expense += amount


# ==================================================
# 4. 용돈 설정
# ==================================================

my_allowance = float(
    household_settings.get(
        "my_allowance",
        0,
    )
    or 0
)

spouse_allowance = float(
    household_settings.get(
        "spouse_allowance",
        0,
    )
    or 0
)


# ==================================================
# 5. 이번 달 목적자금 적립 계산
# ==================================================

monthly_fund_contribution = 0


fund_summaries = []


for fund in funds:

    fund_id = fund["id"]

    fund_transactions = (
        get_fund_transactions(
            fund_id
        )
    )

    fund_balance = 0
    current_month_fund_contribution = 0
    current_month_fund_usage = 0


    for fund_transaction in fund_transactions:

        amount = float(
            fund_transaction["amount"]
        )

        fund_transaction_date = (
            date.fromisoformat(
                fund_transaction[
                    "transaction_date"
                ]
            )
        )


        if (
            fund_transaction[
                "transaction_type"
            ]
            == "적립"
        ):

            fund_balance += amount

        elif (
            fund_transaction[
                "transaction_type"
            ]
            == "사용"
        ):

            fund_balance -= amount


        if (
            fund_transaction_date.year
            == current_year
            and
            fund_transaction_date.month
            == current_month
        ):

            if (
                fund_transaction[
                    "transaction_type"
                ]
                == "적립"
            ):

                current_month_fund_contribution += (
                    amount
                )

            elif (
                fund_transaction[
                    "transaction_type"
                ]
                == "사용"
            ):

                current_month_fund_usage += (
                    amount
                )


    monthly_fund_contribution += (
        current_month_fund_contribution
    )


    fund_summaries.append({
        "id": fund_id,
        "name": fund["name"],
        "monthly_target": float(
            fund.get(
                "monthly_target",
                0,
            )
            or 0
        ),
        "balance": fund_balance,
        "monthly_contribution":
            current_month_fund_contribution,
        "monthly_usage":
            current_month_fund_usage,
    })


# ==================================================
# 6. 공동자금 계산
# ==================================================

total_allowance = (
    my_allowance
    + spouse_allowance
)


available_household_money = (
    monthly_income
    - total_allowance
    - monthly_fund_contribution
)


remaining_household_money = (
    available_household_money
    - monthly_expense
)


# ==================================================
# 7. 이번 달 공동자금 흐름
# ==================================================

st.divider()

st.subheader(
    f"💰 {current_year}년 "
    f"{current_month}월 공동자금 흐름"
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "이번 달 총 수입",
        f"₩{int(monthly_income):,}",
    )


with col2:

    st.metric(
        "공동생활 가능액",
        (
            f"₩"
            f"{int(available_household_money):,}"
        ),
    )


with col3:

    st.metric(
        "남은 공동자금",
        (
            f"₩"
            f"{int(remaining_household_money):,}"
        ),
    )


st.markdown("#### 먼저 배정한 돈")


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "내 용돈",
        f"₩{int(my_allowance):,}",
    )


with col2:

    st.metric(
        "남편 용돈",
        f"₩{int(spouse_allowance):,}",
    )


with col3:

    st.metric(
        "목적자금 적립",
        (
            f"₩"
            f"{int(monthly_fund_contribution):,}"
        ),
    )


st.markdown("#### 실제 공동생활 지출")


st.metric(
    "이번 달 실제 지출",
    f"₩{int(monthly_expense):,}",
)


show_help(
    "공동생활 가능액은 어떻게 계산하나요?",
    (
        "두 사람의 월급 등 이번 달 수입에서 "
        "내 용돈, 남편 용돈, 목적자금 적립액을 먼저 빼고 "
        "남은 금액을 공동생활 가능액으로 계산합니다."
    ),
    example=(
        "예: 수입 7,000,000원 - 용돈 800,000원 "
        "- 여행자금 500,000원 = 공동생활 가능액 5,700,000원"
    ),
)


show_help(
    "용돈과 여행자금은 왜 지출에 포함하지 않나요?",
    (
        "용돈과 목적자금 적립은 공동생활비로 소비된 돈이라기보다 "
        "월급에서 먼저 목적별로 배정한 돈으로 관리합니다. "
        "따라서 생활비, 고정비, 경조사비 같은 실제 공동 지출과 분리합니다."
    ),
    warning=(
        "용돈 지급이나 여행자금 적립을 거래내역의 일반 지출로 "
        "중복 입력하면 공동지출이 실제보다 크게 계산됩니다."
    ),
)


# ==================================================
# 8. 목적자금 현황
# ==================================================

st.divider()

st.subheader("🎯 목적자금 현황")


if fund_summaries:

    for fund in fund_summaries:

        monthly_target = (
            fund["monthly_target"]
        )

        monthly_contribution = (
            fund["monthly_contribution"]
        )


        st.markdown(
            f'### {fund["name"]}'
        )


        col1, col2, col3 = (
            st.columns(3)
        )


        with col1:

            st.metric(
                "현재 배정 잔액",
                (
                    f'₩'
                    f'{int(fund["balance"]):,}'
                ),
            )


        with col2:

            st.metric(
                "이번 달 적립",
                (
                    f'₩'
                    f'{int(monthly_contribution):,}'
                ),
            )


        with col3:

            st.metric(
                "월 적립 목표",
                (
                    f'₩'
                    f'{int(monthly_target):,}'
                ),
            )


        if monthly_target > 0:

            progress = min(
                monthly_contribution
                / monthly_target,
                1.0,
            )

            st.progress(
                progress
            )


            achievement_rate = (
                monthly_contribution
                / monthly_target
            ) * 100


            if (
                monthly_contribution
                >= monthly_target
            ):

                st.success(
                    "이번 달 적립 목표 달성 "
                    f"({achievement_rate:.1f}%)"
                )

            else:

                remaining_target = (
                    monthly_target
                    - monthly_contribution
                )

                st.caption(
                    f"달성률 "
                    f"{achievement_rate:.1f}% · "
                    f"₩{int(remaining_target):,} 남음"
                )


        if (
            fund["monthly_usage"]
            > 0
        ):

            st.caption(
                "이번 달 사용 "
                f'₩{int(fund["monthly_usage"]):,}'
            )


        st.divider()


else:

    st.info(
        "등록된 목적자금이 없습니다."
    )


show_help(
    "목적자금 잔액은 총 자산에 다시 더하나요?",
    (
        "아닙니다. 목적자금은 우리 자산 중 특정 목적에 "
        "얼마를 배정했는지 보여주는 관리용 금액입니다. "
        "실제 여행통장이 자산 메뉴에 등록되어 있다면 "
        "이미 총 자산에 포함되어 있습니다."
    ),
)


# ==================================================
# 9. 이번 달 카드 청구 예정
# ==================================================

st.divider()

st.subheader(
    f"💳 {current_year}년 "
    f"{current_month}월 카드 청구 예정"
)


# --------------------------------------------------
# 카드 청구 대상 기간
# 이번 달 청구액 = 전월 1일 ~ 전월 말일 사용액
# --------------------------------------------------

current_month_start = date(
    current_year,
    current_month,
    1,
)

previous_month_end = (
    current_month_start
    - timedelta(days=1)
)

previous_month_start = date(
    previous_month_end.year,
    previous_month_end.month,
    1,
)


# --------------------------------------------------
# 카드별 기본 데이터
# --------------------------------------------------

card_totals = {}


for card in cards:

    card_id = int(
        card["id"]
    )

    card_totals[
        card_id
    ] = {
        "id": card_id,
        "name": card["name"],
        "owner": card["owner"],
        "payment_day": int(
            card["payment_day"]
        ),
        "amount": 0,
    }


# --------------------------------------------------
# 전월 카드 사용액 집계
# --------------------------------------------------

for transaction in transactions:

    if (
        transaction["transaction_type"]
        != "지출"
    ):
        continue


    card_id = transaction.get(
        "card_id"
    )


    if card_id is None:
        continue


    try:

        card_id = int(
            card_id
        )

    except (
        TypeError,
        ValueError,
    ):

        continue


    transaction_date = (
        date.fromisoformat(
            transaction[
                "transaction_date"
            ]
        )
    )


    if not (
        previous_month_start
        <= transaction_date
        <= previous_month_end
    ):
        continue


    if card_id in card_totals:

        card_totals[
            card_id
        ]["amount"] += float(
            transaction["amount"]
        )


# --------------------------------------------------
# 실제 청구액이 있는 카드만
# --------------------------------------------------

used_cards = [
    card
    for card
    in card_totals.values()
    if card["amount"] > 0
]


if used_cards:

    used_cards = sorted(
        used_cards,
        key=lambda x: (
            x["owner"],
            x["payment_day"],
            x["name"],
        ),
    )


    # ==================================================
    # 사람별 합계
    # ==================================================

    owner_totals = {}


    for card in used_cards:

        owner = card["owner"]

        if owner not in owner_totals:

            owner_totals[
                owner
            ] = 0

        owner_totals[
            owner
        ] += card["amount"]


    total_card_bill = sum(
        card["amount"]
        for card in used_cards
    )


    # ==================================================
    # 전체 요약
    # ==================================================

    st.markdown(
        "#### 이번 달 카드 청구 요약"
    )


    summary_columns = st.columns(3)


    with summary_columns[0]:

        st.metric(
            "내 카드",
            (
                f"₩"
                f"{int(owner_totals.get('나', 0)):,}"
            ),
        )


    with summary_columns[1]:

        st.metric(
            "남편 카드",
            (
                f"₩"
                f"{int(owner_totals.get('남편', 0)):,}"
            ),
        )


    with summary_columns[2]:

        st.metric(
            "부부 총 카드청구액",
            (
                f"₩"
                f"{int(total_card_bill):,}"
            ),
        )


    # 공동 명의 카드가 있을 경우
    shared_total = owner_totals.get(
        "공동",
        0,
    )


    if shared_total > 0:

        st.caption(
            "공동 카드 청구액 "
            f"₩{int(shared_total):,}은 "
            "위 부부 총 카드청구액에 포함되어 있습니다."
        )


    st.divider()


    # ==================================================
    # 사용자별 카드 상세
    # ==================================================

    last_day = calendar.monthrange(
        current_year,
        current_month,
    )[1]


    owner_order = [
        "나",
        "남편",
        "공동",
    ]


    for owner in owner_order:

        owner_cards = [
            card
            for card in used_cards
            if card["owner"] == owner
        ]


        if not owner_cards:
            continue


        # ----------------------------------------------
        # 사용자 제목
        # ----------------------------------------------

        if owner == "나":

            owner_title = "👩 내 카드"

        elif owner == "남편":

            owner_title = "👨 남편 카드"

        else:

            owner_title = "👫 공동 카드"


        st.markdown(
            f"### {owner_title}"
        )


        owner_total = sum(
            card["amount"]
            for card in owner_cards
        )


        # ----------------------------------------------
        # 카드별 상세
        # ----------------------------------------------

        for card in owner_cards:

            actual_payment_day = min(
                card["payment_day"],
                last_day,
            )


            payment_date = date(
                current_year,
                current_month,
                actual_payment_day,
            )


            days_left = (
                payment_date
                - today
            ).days


            if days_left > 0:

                payment_text = (
                    f"{current_month}월 "
                    f"{actual_payment_day}일 결제 "
                    f"· D-{days_left}"
                )

            elif days_left == 0:

                payment_text = (
                    "오늘 결제일"
                )

            else:

                payment_text = (
                    f"{current_month}월 "
                    f"{actual_payment_day}일 "
                    f"· 결제일 지남"
                )


            col1, col2 = st.columns(
                [3, 2]
            )


            with col1:

                st.metric(
                    (
                        f'{card["name"]} '
                        f'· {card["owner"]}'
                    ),
                    (
                        f'₩'
                        f'{int(card["amount"]):,}'
                    ),
                )


            with col2:

                st.write(
                    f"📅 {payment_text}"
                )


        # ----------------------------------------------
        # 사용자 합계
        # ----------------------------------------------

        st.metric(
            f"{owner_title} 합계",
            f"₩{int(owner_total):,}",
        )


        st.divider()


    # ==================================================
    # 전체 합계
    # ==================================================

    st.metric(
        "💳 이번 달 부부 총 카드청구액",
        (
            f"₩"
            f"{int(total_card_bill):,}"
        ),
    )


else:

    st.info(
        "이번 달 청구 예정 카드 사용 내역이 없습니다."
    )


st.caption(
    "카드 사용기간: "
    f"{previous_month_start} "
    "~ "
    f"{previous_month_end}"
)


show_help(
    "카드 청구액은 어떻게 구분하나요?",
    (
        "카드는 카드명뿐 아니라 소유자까지 구분해서 관리합니다. "
        "따라서 같은 신한카드 BEST-F를 사용하더라도 "
        "'신한카드 BEST-F · 나'와 "
        "'신한카드 BEST-F · 남편'은 서로 다른 카드로 계산됩니다."
    ),
    example=(
        "예: 내 BEST-F 35만원 + 남편 BEST-F 42만원 "
        "= 부부 총 카드청구액 77만원"
    ),
)


show_help(
    "이번 달 카드 청구액은 어떤 기간인가요?",
    (
        "우리 집 카드는 전월 1일부터 말일까지 사용한 금액이 "
        "다음 달에 청구되도록 결제일을 설정해두었기 때문에 "
        "이번 달 카드 청구액은 전월 카드 사용액을 합산합니다."
    ),
    example=(
        "예: 8월 카드 청구액 = "
        "7월 1일~7월 31일 카드 사용액"
    ),
)


# ==================================================
# 10. 이번 달 지출 분석
# ==================================================

st.divider()

st.subheader(
    "🏷️ 이번 달 지출 분석"
)


if transactions:

    expense_df = pd.DataFrame(
        transactions
    )


    expense_df[
        "amount"
    ] = expense_df[
        "amount"
    ].astype(float)


    expense_df[
        "transaction_date"
    ] = pd.to_datetime(
        expense_df[
            "transaction_date"
        ]
    )


    if (
        "subcategory"
        not in expense_df.columns
    ):

        expense_df[
            "subcategory"
        ] = None


    current_expense_df = (
        expense_df[
            (
                expense_df[
                    "transaction_type"
                ]
                == "지출"
            )
            &
            (
                expense_df[
                    "transaction_date"
                ].dt.year
                == current_year
            )
            &
            (
                expense_df[
                    "transaction_date"
                ].dt.month
                == current_month
            )
        ].copy()
    )


    if not current_expense_df.empty:

        main_category_summary = (
            current_expense_df
            .groupby(
                "category",
                as_index=False,
            )["amount"]
            .sum()
            .sort_values(
                "amount",
                ascending=False,
            )
        )


        st.markdown(
            "#### 대분류별 지출"
        )


        main_display_df = (
            main_category_summary.rename(
                columns={
                    "category":
                        "대분류",
                    "amount":
                        "지출액",
                }
            )
        )


        st.dataframe(
            main_display_df,
            width="stretch",
            hide_index=True,
            column_config={
                "지출액":
                    st.column_config.NumberColumn(
                        "지출액",
                        format="₩ %d",
                    ),
            },
        )


        fig_main_category = (
            px.pie(
                main_category_summary,
                names="category",
                values="amount",
                hole=0.4,
                title=(
                    f"{current_month}월 "
                    "대분류별 지출 비중"
                ),
            )
        )


        st.plotly_chart(
            fig_main_category,
            width="stretch",
            key=(
                "main_category_expense_chart"
            ),
        )


        st.markdown(
            "#### 소분류 상세"
        )


        main_category_names = (
            main_category_summary[
                "category"
            ].tolist()
        )


        selected_main_category = (
            st.selectbox(
                "상세하게 볼 대분류",
                main_category_names,
                key=(
                    "dashboard_main_category_select"
                ),
            )
        )


        selected_main_df = (
            current_expense_df[
                current_expense_df[
                    "category"
                ]
                == selected_main_category
            ].copy()
        )


        selected_main_df[
            "subcategory"
        ] = (
            selected_main_df[
                "subcategory"
            ]
            .fillna("미분류")
        )


        selected_main_df.loc[
            selected_main_df[
                "subcategory"
            ]
            .astype(str)
            .str.strip()
            == "",
            "subcategory"
        ] = "미분류"


        subcategory_summary = (
            selected_main_df
            .groupby(
                "subcategory",
                as_index=False,
            )["amount"]
            .sum()
            .sort_values(
                "amount",
                ascending=False,
            )
        )


        selected_main_total = (
            subcategory_summary[
                "amount"
            ].sum()
        )


        st.metric(
            (
                f"{selected_main_category} "
                "총 지출"
            ),
            (
                f"₩"
                f"{int(selected_main_total):,}"
            ),
        )


        sub_display_df = (
            subcategory_summary.rename(
                columns={
                    "subcategory":
                        "소분류",
                    "amount":
                        "지출액",
                }
            )
        )


        st.dataframe(
            sub_display_df,
            width="stretch",
            hide_index=True,
            column_config={
                "지출액":
                    st.column_config.NumberColumn(
                        "지출액",
                        format="₩ %d",
                    ),
            },
        )


        fig_subcategory = (
            px.bar(
                subcategory_summary,
                x="subcategory",
                y="amount",
                title=(
                    f"{selected_main_category} "
                    "소분류별 지출"
                ),
                labels={
                    "subcategory":
                        "소분류",
                    "amount":
                        "지출액",
                },
            )
        )


        fig_subcategory.update_layout(
            yaxis_tickformat=","
        )


        st.plotly_chart(
            fig_subcategory,
            width="stretch",
            key=(
                "subcategory_expense_chart"
            ),
        )


    else:

        st.info(
            "이번 달 지출 데이터가 없습니다."
        )


else:

    st.info(
        "등록된 거래가 없습니다."
    )


show_help(
    "대분류와 소분류는 어떻게 보나요?",
    (
        "대분류에서는 생활비, 고정비, 차량유지처럼 "
        "큰 지출 영역을 비교합니다. "
        "대분류를 하나 선택하면 그 안의 식비, 생필품, 보험료 등 "
        "세부 소분류 지출을 확인할 수 있습니다."
    ),
)


# ==================================================
# 11. 자산 현황 기록
# ==================================================

st.divider()

st.subheader(
    "📸 자산 현황 기록"
)


snapshot_date = st.date_input(
    "기록 날짜",
    value=date.today(),
    key="net_worth_snapshot_date",
)


if st.button(
    "현재 자산 현황 저장",
    key="save_net_worth_snapshot",
):

    add_net_worth_snapshot(
        record_date=snapshot_date,
        total_assets=total_assets,
        total_debts=total_debts,
        net_worth=net_worth,
    )

    st.success(
        f"{snapshot_date} "
        "자산 현황을 저장했습니다."
    )

    st.rerun()


history = get_net_worth_history()


# ==================================================
# 12. 저장된 자산 현황
# ==================================================

st.divider()

st.subheader(
    "📋 저장된 자산 현황"
)


if history:

    history_table_df = (
        pd.DataFrame(
            history
        )
    )


    history_table_df[
        "record_date"
    ] = pd.to_datetime(
        history_table_df[
            "record_date"
        ]
    )


    for column in [
        "total_assets",
        "total_debts",
        "net_worth",
    ]:

        history_table_df[
            column
        ] = history_table_df[
            column
        ].astype(float)


    history_table_df = (
        history_table_df
        .sort_values(
            "record_date",
            ascending=False,
        )
    )


    display_history_df = (
        history_table_df[
            [
                "record_date",
                "total_assets",
                "total_debts",
                "net_worth",
            ]
        ].copy()
    )


    display_history_df = (
        display_history_df.rename(
            columns={
                "record_date":
                    "기록 날짜",
                "total_assets":
                    "총 자산",
                "total_debts":
                    "총 부채",
                "net_worth":
                    "순자산",
            }
        )
    )


    st.dataframe(
        display_history_df,
        width="stretch",
        hide_index=True,
        column_config={
            "기록 날짜":
                st.column_config.DateColumn(
                    "기록 날짜",
                    format="YYYY-MM-DD",
                ),

            "총 자산":
                st.column_config.NumberColumn(
                    "총 자산",
                    format="₩ %d",
                ),

            "총 부채":
                st.column_config.NumberColumn(
                    "총 부채",
                    format="₩ %d",
                ),

            "순자산":
                st.column_config.NumberColumn(
                    "순자산",
                    format="₩ %d",
                ),
        },
    )


    st.markdown(
        "#### 🗑 기록 삭제"
    )


    history_options = {
        (
            f'{item["record_date"]} · '
            f'순자산 ₩'
            f'{int(float(item["net_worth"])):,}'
        ):
        item["id"]

        for item in history
    }


    selected_history_label = (
        st.selectbox(
            "삭제할 기록",
            list(
                history_options.keys()
            ),
            key=(
                "delete_history_select"
            ),
        )
    )


    selected_history_id = (
        history_options[
            selected_history_label
        ]
    )


    if (
        "history_delete_confirm"
        not in st.session_state
    ):

        st.session_state[
            "history_delete_confirm"
        ] = False


    if not st.session_state[
        "history_delete_confirm"
    ]:

        if st.button(
            "선택한 기록 삭제",
            key=(
                "delete_history_button"
            ),
        ):

            st.session_state[
                "history_delete_confirm"
            ] = True

            st.rerun()


    else:

        st.warning(
            f"{selected_history_label} "
            "기록을 정말 삭제하시겠습니까?"
        )


        col1, col2 = st.columns(2)


        with col1:

            if st.button(
                "삭제 확인",
                type="primary",
                key=(
                    "confirm_history_delete"
                ),
                use_container_width=True,
            ):

                delete_net_worth_snapshot(
                    selected_history_id
                )

                st.session_state[
                    "history_delete_confirm"
                ] = False

                st.rerun()


        with col2:

            if st.button(
                "취소",
                key=(
                    "cancel_history_delete"
                ),
                use_container_width=True,
            ):

                st.session_state[
                    "history_delete_confirm"
                ] = False

                st.rerun()


else:

    st.info(
        "아직 저장된 자산 현황 기록이 없습니다."
    )


# ==================================================
# 13. 순자산 변화
# ==================================================

st.divider()

st.subheader(
    "📈 자산 변화"
)


if history:

    history_df = pd.DataFrame(
        history
    )


    history_df[
        "record_date"
    ] = pd.to_datetime(
        history_df[
            "record_date"
        ]
    )


    for column in [
        "total_assets",
        "total_debts",
        "net_worth",
    ]:

        history_df[
            column
        ] = history_df[
            column
        ].astype(float)


    chart_df = history_df[
        [
            "record_date",
            "total_assets",
            "total_debts",
            "net_worth",
        ]
    ].copy()


    chart_df = chart_df.rename(
        columns={
            "record_date": "날짜",
            "total_assets": "총 자산",
            "total_debts": "총 부채",
            "net_worth": "순자산",
        }
    )


    chart_df = chart_df.melt(
        id_vars="날짜",
        value_vars=[
            "총 자산",
            "총 부채",
            "순자산",
        ],
        var_name="구분",
        value_name="금액",
    )


    fig_net_worth = px.line(
        chart_df,
        x="날짜",
        y="금액",
        color="구분",
        markers=True,
        title=(
            "자산 / 부채 / 순자산 변화"
        ),
    )


    fig_net_worth.update_layout(
        yaxis_tickformat=","
    )


    st.plotly_chart(
        fig_net_worth,
        width="stretch",
        key=(
            "net_worth_history_chart"
        ),
    )


else:

    st.info(
        "자산 변화 그래프를 표시하려면 "
        "먼저 자산 현황을 저장해주세요."
    )


# ==================================================
# 14. 월별 수입 / 지출
# ==================================================

st.divider()

st.subheader(
    "📊 월별 수입 / 지출"
)


if transactions:

    monthly_df = pd.DataFrame(
        transactions
    )


    monthly_df[
        "amount"
    ] = monthly_df[
        "amount"
    ].astype(float)


    monthly_df[
        "transaction_date"
    ] = pd.to_datetime(
        monthly_df[
            "transaction_date"
        ]
    )


    monthly_df[
        "year_month"
    ] = (
        monthly_df[
            "transaction_date"
        ]
        .dt.to_period("M")
        .astype(str)
    )


    monthly_summary = (
        monthly_df
        .groupby(
            [
                "year_month",
                "transaction_type",
            ],
            as_index=False,
        )["amount"]
        .sum()
    )


    fig_monthly = px.bar(
        monthly_summary,
        x="year_month",
        y="amount",
        color="transaction_type",
        barmode="group",
        title="월별 수입 / 지출",
        labels={
            "year_month":
                "월",
            "amount":
                "금액",
            "transaction_type":
                "구분",
        },
    )


    st.plotly_chart(
        fig_monthly,
        width="stretch",
        key=(
            "monthly_income_expense_chart"
        ),
    )


else:

    st.info(
        "등록된 거래가 없습니다."
    )


# ==================================================
# 15. 자산 구성
# ==================================================

st.divider()

st.subheader(
    "💰 자산 구성"
)


if assets:

    asset_df = pd.DataFrame(
        assets
    )


    asset_df[
        "current_value"
    ] = asset_df[
        "current_value"
    ].astype(float)


    asset_summary = (
        asset_df
        .groupby(
            "asset_type",
            as_index=False,
        )["current_value"]
        .sum()
    )


    fig_assets = px.pie(
        asset_summary,
        names="asset_type",
        values="current_value",
        hole=0.45,
        title="자산 종류별 비중",
    )


    st.plotly_chart(
        fig_assets,
        width="stretch",
        key="asset_type_chart",
    )


    st.subheader(
        "👫 소유자별 자산"
    )


    owner_summary = (
        asset_df
        .groupby(
            "owner",
            as_index=False,
        )["current_value"]
        .sum()
    )


    fig_owner = px.bar(
        owner_summary,
        x="owner",
        y="current_value",
        title="소유자별 자산",
        labels={
            "owner":
                "소유자",
            "current_value":
                "자산",
        },
    )


    st.plotly_chart(
        fig_owner,
        width="stretch",
        key="asset_owner_chart",
    )


else:

    st.info(
        "등록된 자산이 없습니다."
    )