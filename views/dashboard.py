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
    get_available_cash_asset,
    get_investment_accounts,
    get_investment_transactions,
)

from services.investment import (
    calculate_holdings,
    evaluate_holdings,
    calculate_account_summary,
)

from utils.helpers import show_help


st.title("📊 우리집 자산 현황")


# ==================================================
# 1. 기본 데이터 조회
# ==================================================

assets = get_assets() or []
debts = get_debts() or []
transactions = get_transactions() or []
cards = get_cards() or []
funds = get_funds() or []

household_settings = get_household_settings()

available_cash_asset = (
    get_available_cash_asset()
)

investment_accounts = (
    get_investment_accounts()
    or []
)

today = date.today()

current_year = today.year
current_month = today.month


# ==================================================
# 2. 자산 분류 및 투자 평가
# ==================================================

# --------------------------------------------------
# 자산 메뉴에서 '투자자산'으로 보는 유형
#
# 투자 페이지의 모든 계좌 평가가 준비되면
# 아래 자산유형은 assets.current_value 대신
# 투자 페이지 평가액을 공식 투자금액으로 사용한다.
# --------------------------------------------------

investment_asset_types = {
    "ISA",
    "연금저축",
    "투자",
    "주식",
    "ETF",
}


available_assets_value = sum(
    float(
        asset.get(
            "current_value",
            0,
        )
        or 0
    )
    for asset in assets
    if bool(
        asset.get(
            "is_available_cash",
            False,
        )
    )
)


savings_assets_value = sum(
    float(
        asset.get(
            "current_value",
            0,
        )
        or 0
    )
    for asset in assets
    if (
        not bool(
            asset.get(
                "is_available_cash",
                False,
            )
        )
        and
        asset.get(
            "asset_type"
        ) == "적금"
    )
)


manual_investment_assets_value = sum(
    float(
        asset.get(
            "current_value",
            0,
        )
        or 0
    )
    for asset in assets
    if (
        not bool(
            asset.get(
                "is_available_cash",
                False,
            )
        )
        and
        asset.get(
            "asset_type"
        )
        in investment_asset_types
    )
)


other_assets_value = sum(
    float(
        asset.get(
            "current_value",
            0,
        )
        or 0
    )
    for asset in assets
    if (
        not bool(
            asset.get(
                "is_available_cash",
                False,
            )
        )
        and
        asset.get(
            "asset_type"
        ) != "적금"
        and
        asset.get(
            "asset_type"
        )
        not in investment_asset_types
    )
)


# ==================================================
# 투자 페이지 평가액 계산
#
# investments.py에서 현재가/환율을 조회하면
# 같은 Streamlit 세션의 session_state에 저장된다.
#
# 모든 투자계좌의 평가 준비가 끝난 경우에만
# 평가액을 총자산의 투자금액으로 채택한다.
#
# 일부 계좌만 조회된 상태라면 총자산이 갑자기
# 작아지는 것을 막기 위해 assets에 저장된
# 투자자산 금액을 fallback으로 사용한다.
# ==================================================

investment_results = []

all_investment_accounts_ready = bool(
    investment_accounts
)


for investment_account in (
    investment_accounts
):

    investment_account_id = (
        investment_account[
            "id"
        ]
    )


    investment_transactions = (
        get_investment_transactions(
            investment_account_id
        )
        or []
    )


    investment_holdings = (
        calculate_holdings(
            investment_transactions
        )
    )


    investment_price_map = (
        st.session_state.get(
            (
                "investment_prices_"
                f"{investment_account_id}"
            ),
            {},
        )
    )


    investment_exchange_map = (
        st.session_state.get(
            (
                "investment_exchange_rates_"
                f"{investment_account_id}"
            ),
            {},
        )
    )


    prices_ready = all(
        (
            symbol
            in investment_price_map
            and
            investment_price_map[
                symbol
            ]
            is not None
        )
        for symbol
        in investment_holdings.keys()
    )


    rates_ready = True


    for holding in (
        investment_holdings.values()
    ):

        currency_code = (
            holding.get(
                "currency"
            )
            or "KRW"
        ).upper()


        if currency_code == "KRW":
            continue


        if (
            currency_code
            not in investment_exchange_map
            or
            investment_exchange_map[
                currency_code
            ]
            is None
        ):

            rates_ready = False
            break


    # 종목이 없는 현금 계좌는 평가 가능
    if not investment_holdings:

        prices_ready = True
        rates_ready = True


    account_ready = (
        prices_ready
        and
        rates_ready
    )


    if not account_ready:

        all_investment_accounts_ready = (
            False
        )


    if account_ready:

        evaluated_holdings = (
            evaluate_holdings(
                investment_holdings,
                price_map=(
                    investment_price_map
                ),
                exchange_rate_map=(
                    investment_exchange_map
                ),
            )
        )


        account_summary = (
            calculate_account_summary(
                investment_transactions,
                evaluated_holdings,
            )
        )


        investment_results.append({
            "account":
                investment_account,

            "summary":
                account_summary,
        })


# 투자계좌가 아예 없으면 수동 자산 값을 사용
if not investment_accounts:

    all_investment_accounts_ready = (
        False
    )


if (
    investment_accounts
    and
    all_investment_accounts_ready
):

    investment_value_source = (
        "실시간 투자 평가액"
    )


    total_investment_value = sum(
        float(
            result[
                "summary"
            ][
                "account_value"
            ]
        )
        for result
        in investment_results
    )


    my_investment_value = sum(
        float(
            result[
                "summary"
            ][
                "account_value"
            ]
        )
        for result
        in investment_results
        if (
            result[
                "account"
            ][
                "owner"
            ]
            == "나"
        )
    )


    spouse_investment_value = sum(
        float(
            result[
                "summary"
            ][
                "account_value"
            ]
        )
        for result
        in investment_results
        if (
            result[
                "account"
            ][
                "owner"
            ]
            == "남편"
        )
    )


    shared_investment_value = sum(
        float(
            result[
                "summary"
            ][
                "account_value"
            ]
        )
        for result
        in investment_results
        if (
            result[
                "account"
            ][
                "owner"
            ]
            == "공동"
        )
    )


else:

    investment_value_source = (
        "자산 메뉴 등록값"
    )


    total_investment_value = (
        manual_investment_assets_value
    )


    my_investment_value = sum(
        float(
            asset.get(
                "current_value",
                0,
            )
            or 0
        )
        for asset in assets
        if (
            asset.get(
                "asset_type"
            )
            in investment_asset_types
            and
            asset.get(
                "owner"
            )
            == "나"
        )
    )


    spouse_investment_value = sum(
        float(
            asset.get(
                "current_value",
                0,
            )
            or 0
        )
        for asset in assets
        if (
            asset.get(
                "asset_type"
            )
            in investment_asset_types
            and
            asset.get(
                "owner"
            )
            == "남편"
        )
    )


    shared_investment_value = sum(
        float(
            asset.get(
                "current_value",
                0,
            )
            or 0
        )
        for asset in assets
        if (
            asset.get(
                "asset_type"
            )
            in investment_asset_types
            and
            asset.get(
                "owner"
            )
            == "공동"
        )
    )


# ==================================================
# 총 자산 / 총 부채 / 순자산
#
# 각 자산군을 정확히 한 번씩만 합산한다.
# ==================================================

total_assets = (
    available_assets_value
    + savings_assets_value
    + total_investment_value
    + other_assets_value
)


total_debts = sum(
    float(
        debt.get(
            "balance",
            0,
        )
        or 0
    )
    for debt in debts
)


net_worth = (
    total_assets
    - total_debts
)


# ==================================================
# 핵심 요약
# ==================================================

col1, col2, col3 = (
    st.columns(3)
)


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


st.markdown(
    "#### 자산 성격별 현황"
)


col1, col2, col3, col4 = (
    st.columns(4)
)


with col1:

    st.metric(
        "💵 가용자산",
        (
            f"₩"
            f"{int(available_assets_value):,}"
        ),
    )


with col2:

    st.metric(
        "🏦 적금",
        (
            f"₩"
            f"{int(savings_assets_value):,}"
        ),
    )


with col3:

    st.metric(
        "📈 투자",
        (
            f"₩"
            f"{int(total_investment_value):,}"
        ),
    )


with col4:

    st.metric(
        "📦 기타자산",
        (
            f"₩"
            f"{int(other_assets_value):,}"
        ),
    )


# ==================================================
# 나 / 남편 투자 분리 표시
# ==================================================

if (
    total_investment_value > 0
    or investment_accounts
):

    st.markdown(
        "##### 투자 소유자별"
    )


    investment_cols = (
        st.columns(3)
    )


    with investment_cols[0]:

        st.metric(
            "👩 내 투자",
            (
                f"₩"
                f"{int(my_investment_value):,}"
            ),
        )


    with investment_cols[1]:

        st.metric(
            "👨 남편 투자",
            (
                f"₩"
                f"{int(spouse_investment_value):,}"
            ),
        )


    with investment_cols[2]:

        if (
            shared_investment_value
            > 0
        ):

            st.metric(
                "👫 공동 투자",
                (
                    f"₩"
                    f"{int(shared_investment_value):,}"
                ),
            )

        else:

            st.metric(
                "투자 합계",
                (
                    f"₩"
                    f"{int(total_investment_value):,}"
                ),
            )


st.caption(
    (
        "투자금액 기준: "
        f"{investment_value_source}"
    )
)


if (
    investment_accounts
    and
    not all_investment_accounts_ready
):

    st.info(
        "투자계좌의 현재가·환율이 모두 조회되지 않아 "
        "총자산에는 자산 메뉴에 저장된 투자자산 금액을 사용하고 있습니다. "
        "투자 페이지에서 '전체 투자 시세 · 환율 새로고침'을 하면 "
        "현재 평가액 기준으로 전환됩니다."
    )


show_help(
    "총 자산과 순자산은 어떻게 계산하나요?",
    (
        "총 자산은 가용자산, 적금, 투자, 기타자산을 각각 한 번씩만 "
        "합산합니다. 투자계좌의 현재가와 환율이 모두 조회된 경우에는 "
        "투자 페이지의 평가액을 사용하고, 그렇지 않으면 자산 메뉴에 "
        "등록된 투자자산 금액을 임시 기준으로 사용합니다. "
        "순자산은 총 자산에서 총 부채를 뺀 금액입니다."
    ),
    example=(
        "예: 가용자산 1,000만원 + 적금 500만원 + "
        "투자 2,000만원 + 기타 3,000만원 = 총자산 6,500만원"
    ),
    warning=(
        "목적자금 잔액, 적금 예상 만기금액, 투자 페이지 평가액을 "
        "별도로 다시 더하지 않습니다."
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

my_investment_budget = float(
    household_settings.get(
        "my_investment_budget",
        0,
    )
    or 0
)


spouse_investment_budget = float(
    household_settings.get(
        "spouse_investment_budget",
        0,
    )
    or 0
)


total_investment_budget = (
    my_investment_budget
    + spouse_investment_budget
)

available_household_money = (
    monthly_income
    - monthly_fund_contribution
    - total_investment_budget
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


col1, col2 = st.columns(2)


with col1:

    st.metric(
        "목적자금 적립",
        (
            f"₩"
            f"{int(monthly_fund_contribution):,}"
        ),
    )


with col2:

    st.metric(
        "투자금 배정",
        (
            f"₩"
            f"{int(total_investment_budget):,}"
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
        "목적자금 적립액과 월 투자금 배정액을 먼저 빼고 "
        "남은 금액을 공동생활 가능액으로 계산합니다. "
        "용돈은 별도 배정금으로 계산하지 않고 실제 지급 시 일반 지출로 처리합니다."
    ),
    example=(
        "예: 수입 7,000,000원 - 여행자금 500,000원 "
        "- 투자금 1,000,000원 = 공동생활 가능액 5,500,000원"
    ),
)


show_help(
    "용돈은 어떻게 처리하나요?",
    (
        "용돈은 별도 관리하지 않습니다. 각자에게 실제로 지급한 시점에 "
        "거래내역에서 일반 지출로 한 번만 기록하고, 그 이후 개인 사용처는 "
        "앱에서 추적하지 않습니다."
    ),
    example=(
        "예: 내 용돈 400,000원 지급 → 거래내역에서 지출 400,000원으로 기록"
    ),
    warning=(
        "용돈을 설정값으로 한 번 빼고 거래내역에서도 다시 지출로 입력하면 "
        "이중 차감되므로, 앞으로는 거래내역 지출만 사용합니다."
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
# 9. 이번 달 카드 현황
# ==================================================

st.divider()

st.subheader(
    f"💳 {current_year}년 "
    f"{current_month}월 카드 현황"
)


# ==================================================
# 날짜 계산 함수
# ==================================================

def get_offset_year_month(
    base_year,
    base_month,
    month_offset,
):
    """
    기준 연/월에서 month_offset만큼 이동한
    연도와 월을 반환한다.

    -1 = 전월
     0 = 당월
     1 = 다음 달
    """

    month_index = (
        base_year * 12
        + (base_month - 1)
        + month_offset
    )

    result_year = (
        month_index // 12
    )

    result_month = (
        month_index % 12
    ) + 1

    return (
        result_year,
        result_month,
    )


def make_billing_date(
    base_year,
    base_month,
    month_offset,
    day,
    is_month_end,
):
    """
    카드 청구기간 날짜를 실제 date 객체로 변환한다.
    """

    year, month = (
        get_offset_year_month(
            base_year,
            base_month,
            month_offset,
        )
    )

    last_day = calendar.monthrange(
        year,
        month,
    )[1]


    if is_month_end:

        actual_day = last_day

    else:

        actual_day = min(
            int(day or 1),
            last_day,
        )


    return date(
        year,
        month,
        actual_day,
    )


# ==================================================
# 카드별 데이터 계산
# ==================================================

card_summaries = []


current_month_start = date(
    current_year,
    current_month,
    1,
)


for card in cards:

    card_id = int(
        card["id"]
    )


    # ----------------------------------------------
    # 카드 설정값
    # ----------------------------------------------

    start_offset = int(
        card.get(
            "billing_start_month_offset",
            -1,
        )
    )


    end_offset = int(
        card.get(
            "billing_end_month_offset",
            -1,
        )
    )


    start_day = card.get(
        "billing_start_day"
    )


    end_day = card.get(
        "billing_end_day"
    )


    start_is_month_end = bool(
        card.get(
            "billing_start_is_month_end",
            False,
        )
    )


    end_is_month_end = bool(
        card.get(
            "billing_end_is_month_end",
            True,
        )
    )


    monthly_performance = float(
        card.get(
            "monthly_performance",
            0,
        )
        or 0
    )


    # ----------------------------------------------
    # 이번 달 청구대상 기간 계산
    # ----------------------------------------------

    billing_start_date = (
        make_billing_date(
            current_year,
            current_month,
            start_offset,
            start_day,
            start_is_month_end,
        )
    )


    billing_end_date = (
        make_billing_date(
            current_year,
            current_month,
            end_offset,
            end_day,
            end_is_month_end,
        )
    )


    # ----------------------------------------------
    # 청구액 계산
    # ----------------------------------------------

    billing_amount = 0


    # ----------------------------------------------
    # 이번 달 실적
    # ----------------------------------------------

    performance_amount = 0


    for transaction in transactions:

        if (
            transaction[
                "transaction_type"
            ]
            != "지출"
        ):

            continue


        transaction_card_id = (
            transaction.get(
                "card_id"
            )
        )


        if transaction_card_id is None:

            continue


        try:

            transaction_card_id = int(
                transaction_card_id
            )

        except (
            TypeError,
            ValueError,
        ):

            continue


        if (
            transaction_card_id
            != card_id
        ):

            continue


        transaction_date = (
            date.fromisoformat(
                transaction[
                    "transaction_date"
                ]
            )
        )


        transaction_amount = float(
            transaction[
                "amount"
            ]
        )


        # ------------------------------------------
        # 이번 달 청구 예정액
        # ------------------------------------------

        if (
            billing_start_date
            <= transaction_date
            <= billing_end_date
        ):

            billing_amount += (
                transaction_amount
            )


        # ------------------------------------------
        # 이번 달 카드 실적
        #
        # 이번 달 1일 ~ 오늘
        # + 실적 포함 거래만
        # ------------------------------------------

        if (
            current_month_start
            <= transaction_date
            <= today
        ):

            counts_for_performance = bool(
                transaction.get(
                    "counts_for_performance",
                    True,
                )
            )


            if counts_for_performance:

                performance_amount += (
                    transaction_amount
                )


    # ----------------------------------------------
    # 결제일 계산
    # ----------------------------------------------

    last_payment_day = (
        calendar.monthrange(
            current_year,
            current_month,
        )[1]
    )


    actual_payment_day = min(
        int(
            card["payment_day"]
        ),
        last_payment_day,
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
            f"{actual_payment_day}일 "
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


    # ----------------------------------------------
    # 실적 상태
    # ----------------------------------------------

    if monthly_performance > 0:

        performance_remaining = max(
            monthly_performance
            - performance_amount,
            0,
        )


        performance_rate = (
            performance_amount
            / monthly_performance
        ) * 100


        performance_achieved = (
            performance_amount
            >= monthly_performance
        )

    else:

        performance_remaining = 0
        performance_rate = 0
        performance_achieved = False


    # ----------------------------------------------
    # 카드 데이터 저장
    # ----------------------------------------------

    card_summaries.append({
        "id":
            card_id,

        "name":
            card["name"],

        "owner":
            card["owner"],

        "payment_day":
            int(
                card["payment_day"]
            ),

        "payment_date":
            payment_date,

        "payment_text":
            payment_text,

        "billing_start_date":
            billing_start_date,

        "billing_end_date":
            billing_end_date,

        "billing_amount":
            billing_amount,

        "monthly_performance":
            monthly_performance,

        "performance_amount":
            performance_amount,

        "performance_remaining":
            performance_remaining,

        "performance_rate":
            performance_rate,

        "performance_achieved":
            performance_achieved,
    })


# ==================================================
# 카드가 없는 경우
# ==================================================

if not card_summaries:

    st.info(
        "등록된 카드가 없습니다. "
        "설정 → 카드 관리에서 카드를 추가해주세요."
    )


else:

    # ==================================================
    # 사람별 청구액 계산
    # ==================================================

    my_card_total = sum(
        card["billing_amount"]
        for card in card_summaries
        if card["owner"] == "나"
    )


    spouse_card_total = sum(
        card["billing_amount"]
        for card in card_summaries
        if card["owner"] == "남편"
    )


    shared_card_total = sum(
        card["billing_amount"]
        for card in card_summaries
        if card["owner"] == "공동"
    )


    total_card_bill = sum(
        card["billing_amount"]
        for card in card_summaries
    )


    # ==================================================
    # 전체 요약
    # ==================================================

    st.markdown(
        "#### 💳 이번 달 카드 청구 요약"
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    with col1:

        st.metric(
            "내 카드",
            (
                f"₩"
                f"{int(my_card_total):,}"
            ),
        )


    with col2:

        st.metric(
            "남편 카드",
            (
                f"₩"
                f"{int(spouse_card_total):,}"
            ),
        )


    with col3:

        st.metric(
            "부부 총 카드청구액",
            (
                f"₩"
                f"{int(total_card_bill):,}"
            ),
        )


    if shared_card_total > 0:

        st.caption(
            "공동 카드 청구액 "
            f"₩{int(shared_card_total):,}은 "
            "부부 총 카드청구액에 포함되어 있습니다."
        )


    # ==================================================
    # 카드별 상세
    # ==================================================

    st.divider()

    st.markdown(
        "#### 카드별 청구액 · 실적"
    )


    owner_order = [
        "나",
        "남편",
        "공동",
    ]


    for owner in owner_order:

        owner_cards = [
            card
            for card in card_summaries
            if card["owner"] == owner
        ]


        if not owner_cards:

            continue


        owner_cards = sorted(
            owner_cards,
            key=lambda x: (
                x["payment_day"],
                x["name"],
            ),
        )


        if owner == "나":

            owner_title = (
                "👩 내 카드"
            )

        elif owner == "남편":

            owner_title = (
                "👨 남편 카드"
            )

        else:

            owner_title = (
                "👫 공동 카드"
            )


        st.markdown(
            f"### {owner_title}"
        )


        # ----------------------------------------------
        # 카드 하나씩 출력
        # ----------------------------------------------

        for card in owner_cards:

            st.markdown(
                f'#### 💳 '
                f'{card["name"]} · '
                f'{card["owner"]}'
            )


            col1, col2 = (
                st.columns(2)
            )


            with col1:

                st.metric(
                    "이번 달 청구 예정",
                    (
                        f'₩'
                        f'{int(card["billing_amount"]):,}'
                    ),
                )


            with col2:

                st.metric(
                    "결제일",
                    (
                        card[
                            "payment_date"
                        ].strftime(
                            "%m/%d"
                        )
                    ),
                )

                st.caption(
                    card[
                        "payment_text"
                    ]
                )


            st.caption(
                "청구 대상 사용기간: "
                f'{card["billing_start_date"].strftime("%Y-%m-%d")}'
                " ~ "
                f'{card["billing_end_date"].strftime("%Y-%m-%d")}'
            )


            # ==========================================
            # 카드 실적
            # ==========================================

            monthly_performance = (
                card[
                    "monthly_performance"
                ]
            )


            if monthly_performance > 0:

                st.markdown(
                    "##### 이번 달 카드 실적"
                )


                col1, col2, col3 = (
                    st.columns(3)
                )


                with col1:

                    st.metric(
                        "현재 실적",
                        (
                            f'₩'
                            f'{int(card["performance_amount"]):,}'
                        ),
                    )


                with col2:

                    st.metric(
                        "실적 목표",
                        (
                            f'₩'
                            f'{int(monthly_performance):,}'
                        ),
                    )


                with col3:

                    if (
                        card[
                            "performance_achieved"
                        ]
                    ):

                        st.metric(
                            "남은 실적",
                            "달성 ✅",
                        )

                    else:

                        st.metric(
                            "남은 실적",
                            (
                                f'₩'
                                f'{int(card["performance_remaining"]):,}'
                            ),
                        )


                progress_value = min(
                    card[
                        "performance_amount"
                    ]
                    / monthly_performance,
                    1.0,
                )


                st.progress(
                    progress_value
                )


                if (
                    card[
                        "performance_achieved"
                    ]
                ):

                    st.success(
                        "이번 달 카드 실적을 "
                        "달성했습니다."
                    )


                else:

                    st.caption(
                        "현재 달성률 "
                        f'{card["performance_rate"]:.1f}%'
                        " · 실적까지 "
                        f'₩{int(card["performance_remaining"]):,} '
                        "남음"
                    )


            else:

                st.caption(
                    "이 카드는 월 실적 목표가 "
                    "설정되어 있지 않습니다."
                )


            st.divider()


        # ----------------------------------------------
        # 사용자별 합계
        # ----------------------------------------------

        owner_total = sum(
            card["billing_amount"]
            for card in owner_cards
        )


        st.metric(
            f"{owner_title} 청구 합계",
            (
                f"₩"
                f"{int(owner_total):,}"
            ),
        )


        st.divider()


    # ==================================================
    # 최종 전체 합계
    # ==================================================

    st.metric(
        "💳 이번 달 부부 총 카드청구액",
        (
            f"₩"
            f"{int(total_card_bill):,}"
        ),
    )


# ==================================================
# 카드 도움말
# ==================================================

show_help(
    "청구액과 카드 실적은 왜 금액이 다를 수 있나요?",
    (
        "카드 청구액은 각 카드에 설정한 청구 대상 사용기간을 기준으로 계산하고, "
        "카드 실적은 이번 달 1일부터 현재까지 사용한 금액 중 "
        "'카드 실적에 포함'으로 기록한 거래만 합산합니다. "
        "따라서 두 금액은 서로 다를 수 있습니다."
    ),
    example=(
        "예: 8월 청구기간이 7월 1일~7월 31일이라면 "
        "8월 청구액은 7월 사용액이고, "
        "8월 실적은 8월에 사용한 실적 인정 금액입니다."
    ),
)


show_help(
    "실적 금액은 카드사 앱과 완전히 동일한가요?",
    (
        "우리 앱은 거래 등록 시 선택한 '카드 실적에 포함' 여부를 기준으로 "
        "실적을 계산합니다. 카드사에서는 거래 취소, 할인 전후 금액, "
        "상품권, 세금, 관리비 등 카드별 세부 규칙을 적용할 수 있으므로 "
        "카드사 앱의 공식 실적과 차이가 날 수 있습니다."
    ),
    warning=(
        "실적이 중요한 달에는 카드사 앱의 공식 실적도 함께 확인하는 것이 안전합니다."
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


asset_composition_rows = [
    {
        "자산구분":
            "가용자산",
        "금액":
            available_assets_value,
    },
    {
        "자산구분":
            "적금",
        "금액":
            savings_assets_value,
    },
    {
        "자산구분":
            "투자",
        "금액":
            total_investment_value,
    },
    {
        "자산구분":
            "기타자산",
        "금액":
            other_assets_value,
    },
]


asset_composition_df = pd.DataFrame(
    asset_composition_rows
)


asset_composition_df = (
    asset_composition_df[
        asset_composition_df[
            "금액"
        ]
        > 0
    ]
)


if not asset_composition_df.empty:

    fig_assets = px.pie(
        asset_composition_df,
        names="자산구분",
        values="금액",
        hole=0.45,
        title="자산 성격별 비중",
    )


    st.plotly_chart(
        fig_assets,
        width="stretch",
        key="asset_type_chart",
    )


else:

    st.info(
        "등록된 자산이 없습니다."
    )


# ==================================================
# 소유자별 자산
#
# 투자 평가액을 사용할 경우 투자자산은
# 별도 계산값으로 소유자별 합계에 넣는다.
# ==================================================

st.subheader(
    "👫 소유자별 자산"
)


owner_values = {
    "나": 0.0,
    "남편": 0.0,
    "공동": 0.0,
}


# 투자자산을 제외한 assets
for asset in assets:

    if (
        asset.get(
            "asset_type"
        )
        in investment_asset_types
    ):

        continue


    owner = (
        asset.get(
            "owner"
        )
        or "공동"
    )


    if owner not in owner_values:

        owner_values[
            owner
        ] = 0.0


    owner_values[
        owner
    ] += float(
        asset.get(
            "current_value",
            0,
        )
        or 0
    )


# 투자값은 정확히 한 번만 추가
owner_values["나"] += (
    my_investment_value
)

owner_values["남편"] += (
    spouse_investment_value
)

owner_values["공동"] += (
    shared_investment_value
)


owner_summary = pd.DataFrame(
    [
        {
            "소유자":
                owner,
            "자산":
                value,
        }
        for owner, value
        in owner_values.items()
        if value > 0
    ]
)


if not owner_summary.empty:

    fig_owner = px.bar(
        owner_summary,
        x="소유자",
        y="자산",
        title="소유자별 자산",
        labels={
            "소유자":
                "소유자",
            "자산":
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
        "소유자별로 표시할 자산이 없습니다."
    )


st.caption(
    "투자는 나와 남편의 계좌를 각각 분리해서 계산하며, "
    "위 합계 화면에서만 부부 전체 자산으로 합산합니다."
)