from datetime import date, datetime

import pandas as pd
import streamlit as st

from services.database import (
    get_investment_accounts,
    add_investment_account,
    update_investment_account,
    delete_investment_account,
    get_investment_transactions,
    add_investment_transaction,
    delete_investment_transaction,
    get_household_settings,
    get_available_cash_asset,
)

from services.investment import (
    calculate_holdings,
    evaluate_holdings,
    calculate_account_summary,
    get_current_price,
    get_current_exchange_rate,
    get_historical_exchange_rate,
    search_investment_symbols,
)

from utils.helpers import show_help


st.title("📈 투자")


# ==================================================
# 안내
# ==================================================

show_help(
    "투자자산은 총자산에 어떻게 반영되나요?",
    (
        "이 페이지의 투자 평가액은 투자 성과를 확인하기 위한 분석용입니다. "
        "기존 자산 메뉴에 ISA나 연금저축 잔액을 등록해두었다면 "
        "이 투자 평가액을 총자산에 다시 더하지 않습니다."
    ),
    warning=(
        "같은 ISA나 연금저축 금액을 자산과 투자 평가액에서 "
        "동시에 총자산에 합산하면 자산이 이중 계산됩니다."
    ),
)


show_help(
    "투자금과 매수는 왜 따로 기록하나요?",
    (
        "투자금 입금은 공동 가용자산에서 선택한 개인 투자계좌로 "
        "돈을 옮기는 것입니다. 반대로 투자계좌에서 출금하면 "
        "공동 가용자산으로 돌아옵니다. 매수·매도·배당은 "
        "투자계좌 내부의 자금 흐름입니다."
    ),
    example=(
        "예: ISA에 50만원 입금 → 입금 500,000원 / "
        "그중 ETF 40만원 매수 → 별도의 매수 거래"
    ),
)


# ==================================================
# 투자계좌 조회
# ==================================================

accounts = get_investment_accounts()
household_settings = (
    get_household_settings()
)

available_cash_asset = (
    get_available_cash_asset()
)

available_cash_value = (
    float(
        available_cash_asset.get(
            "current_value",
            0,
        )
        or 0
    )
    if available_cash_asset
    else 0.0
)

# ==================================================
# 가용자산
# ==================================================

if available_cash_asset:

    st.metric(
        "💵 현재 공동 가용자산",
        f"₩{available_cash_value:,.0f}",
    )

    st.caption(
        "투자계좌에 '입금'하면 이 금액이 줄고, "
        "'출금'하면 다시 늘어납니다."
    )

else:

    st.warning(
        "가용자산 기준금액이 설정되어 있지 않습니다. "
        "설정 → 우리집 가용자산에서 먼저 현재 금액을 입력해주세요."
    )


# ==================================================
# 우리집 전체 투자 현황
# ==================================================

st.subheader("📊 우리집 투자 현황")


show_help(
    "전체 투자 평가액도 총자산에 더해지나요?",
    (
        "아니요. 여기 표시되는 투자 평가액은 투자 성과 분석용입니다. "
        "대시보드의 총자산 계산에는 별도로 더하지 않습니다."
    ),
)


# ==================================================
# 전체 시세 새로고침
# ==================================================

if accounts:

    if st.button(
        "🔄 전체 투자 시세 · 환율 새로고침",
        type="primary",
        use_container_width=True,
        key="refresh_all_investments",
    ):

        progress = st.progress(0)
        status = st.empty()

        total_accounts = len(accounts)


        for account_index, account in enumerate(
            accounts
        ):

            refresh_account_id = (
                account["id"]
            )


            status.caption(
                (
                    f'{account["owner"]} · '
                    f'{account["name"]} '
                    "조회 중..."
                )
            )


            account_transactions = (
                get_investment_transactions(
                    refresh_account_id
                )
            )


            account_holdings = (
                calculate_holdings(
                    account_transactions
                )
            )


            # --------------------------------------
            # 종목 현재가
            # --------------------------------------

            new_prices = {}


            for symbol in (
                account_holdings.keys()
            ):

                new_prices[
                    symbol
                ] = get_current_price(
                    symbol
                )


            # --------------------------------------
            # 필요한 통화
            # --------------------------------------

            currencies = {
                (
                    holding.get(
                        "currency"
                    )
                    or "KRW"
                ).upper()

                for holding
                in account_holdings.values()
            }


            # --------------------------------------
            # 현재 환율
            # --------------------------------------

            new_exchange_rates = {
                "KRW": 1.0
            }


            for currency_code in currencies:

                if currency_code == "KRW":
                    continue


                new_exchange_rates[
                    currency_code
                ] = (
                    get_current_exchange_rate(
                        currency_code,
                        "KRW",
                    )
                )


            # --------------------------------------
            # 세션 저장
            # --------------------------------------

            st.session_state[
                (
                    "investment_prices_"
                    f"{refresh_account_id}"
                )
            ] = new_prices


            st.session_state[
                (
                    "investment_exchange_rates_"
                    f"{refresh_account_id}"
                )
            ] = new_exchange_rates


            st.session_state[
                (
                    "investment_price_time_"
                    f"{refresh_account_id}"
                )
            ] = datetime.now()


            progress.progress(
                (
                    account_index + 1
                )
                / total_accounts
            )


        progress.empty()
        status.empty()


        st.success(
            "전체 투자계좌의 시세와 환율을 조회했습니다."
        )

        st.rerun()


# ==================================================
# 계좌별 평가 결과 계산
# ==================================================

account_results = []


for summary_account in accounts:

    summary_account_id = (
        summary_account["id"]
    )


    summary_transactions = (
        get_investment_transactions(
            summary_account_id
        )
    )


    summary_holdings = (
        calculate_holdings(
            summary_transactions
        )
    )


    summary_price_map = (
        st.session_state.get(
            (
                "investment_prices_"
                f"{summary_account_id}"
            ),
            {},
        )
    )


    summary_exchange_map = (
        st.session_state.get(
            (
                "investment_exchange_rates_"
                f"{summary_account_id}"
            ),
            {},
        )
    )


    # ----------------------------------------------
    # 시세 준비 확인
    # ----------------------------------------------

    prices_ready = True
    rates_ready = True


    for symbol in summary_holdings.keys():

        if (
            symbol not in summary_price_map
            or summary_price_map[
                symbol
            ] is None
        ):

            prices_ready = False
            break


    currencies = {
        (
            holding.get(
                "currency"
            )
            or "KRW"
        ).upper()

        for holding
        in summary_holdings.values()
    }


    for currency_code in currencies:

        if currency_code == "KRW":
            continue


        if (
            currency_code
            not in summary_exchange_map
            or
            summary_exchange_map[
                currency_code
            ] is None
        ):

            rates_ready = False
            break


    # 주식이 없는 현금 계좌
    if not summary_holdings:

        prices_ready = True
        rates_ready = True


    evaluation_ready = (
        prices_ready
        and rates_ready
    )


    if evaluation_ready:

        evaluated = (
            evaluate_holdings(
                summary_holdings,
                price_map=(
                    summary_price_map
                    if summary_holdings
                    else {}
                ),
                exchange_rate_map=(
                    summary_exchange_map
                ),
            )
        )


        summary = (
            calculate_account_summary(
                summary_transactions,
                evaluated,
            )
        )


        account_results.append({
            "account":
                summary_account,

            "ready":
                True,

            "summary":
                summary,
        })


    else:

        account_results.append({
            "account":
                summary_account,

            "ready":
                False,

            "summary":
                None,
        })


# ==================================================
# 개인별 투자 합계
# ==================================================

def calculate_owner_investment_summary(
    owner,
):

    owner_results = [
        result

        for result in account_results

        if (
            result["account"]["owner"]
            == owner
        )
    ]


    ready_results = [
        result

        for result in owner_results

        if result["ready"]
    ]


    net_contribution = sum(
        result[
            "summary"
        ][
            "net_contribution"
        ]

        for result in ready_results
    )


    account_value = sum(
        result[
            "summary"
        ][
            "account_value"
        ]

        for result in ready_results
    )


    profit = (
        account_value
        - net_contribution
    )


    if net_contribution > 0:

        return_rate = (
            profit
            / net_contribution
            * 100
        )

    else:

        return_rate = 0


    return {
        "accounts":
            owner_results,

        "ready_accounts":
            ready_results,

        "net_contribution":
            net_contribution,

        "account_value":
            account_value,

        "profit":
            profit,

        "return_rate":
            return_rate,
    }


my_investment = (
    calculate_owner_investment_summary(
        "나"
    )
)


spouse_investment = (
    calculate_owner_investment_summary(
        "남편"
    )
)

# ==================================================
# 이번 달 실제 투자금 입금 계산
# ==================================================

current_year = date.today().year
current_month = date.today().month


monthly_owner_deposits = {
    "나": 0.0,
    "남편": 0.0,
    "공동": 0.0,
}


for account in accounts:

    account_transactions = (
        get_investment_transactions(
            account["id"]
        )
    )


    for tx in account_transactions:

        if (
            tx.get("transaction_type")
            != "입금"
        ):
            continue


        tx_date = date.fromisoformat(
            tx["transaction_date"]
        )


        if (
            tx_date.year != current_year
            or tx_date.month != current_month
        ):
            continue


        amount = float(
            tx.get("amount")
            or 0
        )


        currency = (
            tx.get("currency")
            or "KRW"
        ).upper()


        if currency == "KRW":

            amount_krw = amount

        else:

            exchange_rate = float(
                tx.get("exchange_rate")
                or 0
            )

            amount_krw = (
                amount
                * exchange_rate
            )


        owner = account["owner"]


        if owner in monthly_owner_deposits:

            monthly_owner_deposits[
                owner
            ] += amount_krw


# ==================================================
# 개인별 투자 현황 출력
# ==================================================

def show_owner_investment(
    title,
    data,
):

    st.markdown(
        f"### {title}"
    )


    if not data["accounts"]:

        st.caption(
            "등록된 투자계좌가 없습니다."
        )

        return


    not_ready_accounts = [
        result

        for result in data["accounts"]

        if not result["ready"]
    ]


    if not_ready_accounts:

        st.warning(
            "일부 계좌의 현재가 또는 환율이 아직 조회되지 않았습니다. "
            "위의 '전체 투자 시세 · 환율 새로고침'을 눌러주세요."
        )


    # ----------------------------------------------
    # 계좌별
    # ----------------------------------------------

    for result in data[
        "ready_accounts"
    ]:

        account = (
            result["account"]
        )


        summary = (
            result["summary"]
        )


        st.markdown(
            (
                f'**{account["account_type"]} · '
                f'{account["name"]}**'
            )
        )


        col1, col2, col3 = (
            st.columns(3)
        )


        with col1:

            st.metric(
                "순투자금",
                (
                    f'₩'
                    f'{int(summary["net_contribution"]):,}'
                ),
            )


        with col2:

            st.metric(
                "현재 평가액",
                (
                    f'₩'
                    f'{int(summary["account_value"]):,}'
                ),
            )


        with col3:

            st.metric(
                "수익률",
                (
                    f'{summary["return_rate"]:+.2f}%'
                ),
                (
                    f'{"+₩" if summary["profit"] >= 0 else "-₩"}'
                    f'{abs(int(summary["profit"])):,}'
                ),
            )


    # ----------------------------------------------
    # 개인 합계
    # ----------------------------------------------

    if data[
        "ready_accounts"
    ]:

        st.markdown(
            "##### 합계"
        )


        col1, col2, col3 = (
            st.columns(3)
        )


        with col1:

            st.metric(
                "총 순투자금",
                (
                    f'₩'
                    f'{int(data["net_contribution"]):,}'
                ),
            )


        with col2:

            st.metric(
                "총 평가액",
                (
                    f'₩'
                    f'{int(data["account_value"]):,}'
                ),
            )


        with col3:

            st.metric(
                "총 수익률",
                (
                    f'{data["return_rate"]:+.2f}%'
                ),
                (
                    f'{"+₩" if data["profit"] >= 0 else "-₩"}'
                    f'{abs(int(data["profit"])):,}'
                ),
            )


show_owner_investment(
    "👩 나",
    my_investment,
)


st.divider()


show_owner_investment(
    "👨 남편",
    spouse_investment,
)

# ==================================================
# 이번 달 투자금 배정 현황
# ==================================================

st.divider()

st.markdown(
    f"### 💵 {current_month}월 투자금 배정 현황"
)


my_budget = float(
    household_settings.get(
        "my_investment_budget",
        0,
    )
    or 0
)


spouse_budget = float(
    household_settings.get(
        "spouse_investment_budget",
        0,
    )
    or 0
)


my_actual = (
    monthly_owner_deposits["나"]
)


spouse_actual = (
    monthly_owner_deposits["남편"]
)


def show_investment_budget(
    title,
    budget,
    actual,
):

    remaining = max(
        budget - actual,
        0,
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    with col1:

        st.metric(
            f"{title} 목표",
            f"₩{int(budget):,}",
        )


    with col2:

        st.metric(
            "실제 입금",
            f"₩{int(actual):,}",
        )


    with col3:

        if actual >= budget:

            st.metric(
                "남은 투자금",
                "완료 ✅",
            )

        else:

            st.metric(
                "남은 투자금",
                f"₩{int(remaining):,}",
            )


    if budget > 0:

        progress_value = min(
            actual / budget,
            1.0,
        )

        st.progress(
            progress_value
        )


        st.caption(
            f"{actual / budget * 100:.1f}% 입금 완료"
        )


st.markdown(
    "#### 👩 나"
)

show_investment_budget(
    "이번 달 투자",
    my_budget,
    my_actual,
)


st.markdown(
    "#### 👨 남편"
)

show_investment_budget(
    "이번 달 투자",
    spouse_budget,
    spouse_actual,
)
# ==================================================
# 부부 전체 투자
# ==================================================

st.divider()

st.markdown(
    "### 👫 부부 전체 투자"
)


couple_net_contribution = (
    my_investment[
        "net_contribution"
    ]
    +
    spouse_investment[
        "net_contribution"
    ]
)


couple_account_value = (
    my_investment[
        "account_value"
    ]
    +
    spouse_investment[
        "account_value"
    ]
)


couple_profit = (
    couple_account_value
    - couple_net_contribution
)


if couple_net_contribution > 0:

    couple_return_rate = (
        couple_profit
        / couple_net_contribution
        * 100
    )

else:

    couple_return_rate = 0


col1, col2, col3 = (
    st.columns(3)
)


with col1:

    st.metric(
        "부부 순투자금",
        (
            f"₩"
            f"{int(couple_net_contribution):,}"
        ),
    )


with col2:

    st.metric(
        "부부 투자 평가액",
        (
            f"₩"
            f"{int(couple_account_value):,}"
        ),
    )


with col3:

    st.metric(
        "부부 투자 수익",
        (
            f'{"+₩" if couple_profit >= 0 else "-₩"}'
            f'{abs(int(couple_profit)):,}'
        ),
        (
            f"{couple_return_rate:+.2f}%"
        ),
    )


st.caption(
    "※ 투자 평가액은 투자성과 분석용이며 "
    "대시보드 총자산에 별도로 가산하지 않습니다."
)


# ==================================================
# 투자계좌 관리
# ==================================================

st.divider()

st.subheader(
    "🏦 투자계좌"
)


# ==================================================
# 투자계좌 추가
# ==================================================

with st.expander(
    "➕ 투자계좌 추가"
):

    with st.form(
        "add_investment_account_form",
        clear_on_submit=True,
    ):

        new_owner = st.selectbox(
            "소유자",
            [
                "나",
                "남편",
                "공동",
            ],
        )


        new_account_type = (
            st.selectbox(
                "계좌 유형",
                [
                    "ISA",
                    "연금저축",
                    "기타",
                ],
            )
        )


        new_account_name = (
            st.text_input(
                "계좌명",
                placeholder=(
                    "예: 내 ISA"
                ),
            )
        )


        new_account_memo = (
            st.text_input(
                "메모",
            )
        )


        add_account_submit = (
            st.form_submit_button(
                "계좌 추가",
                use_container_width=True,
            )
        )


    if add_account_submit:

        if not new_account_name.strip():

            st.error(
                "계좌명을 입력해주세요."
            )

        else:

            try:

                add_investment_account(
                    owner=new_owner,
                    account_type=(
                        new_account_type
                    ),
                    name=(
                        new_account_name
                    ),
                    memo=(
                        new_account_memo
                    ),
                )

                st.success(
                    "투자계좌를 추가했습니다."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "투자계좌를 추가하지 "
                    f"못했습니다: {e}"
                )


# ==================================================
# 계좌 다시 조회
# ==================================================

accounts = (
    get_investment_accounts()
)


if not accounts:

    st.info(
        "등록된 투자계좌가 없습니다. "
        "먼저 ISA 또는 연금저축 계좌를 추가해주세요."
    )

    st.stop()


# ==================================================
# 계좌 선택
# ==================================================

account_options = {
    (
        f'{account["owner"]} · '
        f'{account["account_type"]} · '
        f'{account["name"]}'
    ):
    account

    for account in accounts
}


selected_account_label = (
    st.selectbox(
        "투자계좌 선택",
        list(
            account_options.keys()
        ),
        key="selected_investment_account",
    )
)


selected_account = (
    account_options[
        selected_account_label
    ]
)


account_id = (
    selected_account["id"]
)


# ==================================================
# 해당 계좌 거래
# ==================================================

transactions = (
    get_investment_transactions(
        account_id
    )
)


# ==================================================
# 시세 세션
# ==================================================

price_session_key = (
    f"investment_prices_"
    f"{account_id}"
)


exchange_rate_session_key = (
    f"investment_exchange_rates_"
    f"{account_id}"
)


price_time_key = (
    f"investment_price_time_"
    f"{account_id}"
)


if (
    price_session_key
    not in st.session_state
):

    st.session_state[
        price_session_key
    ] = {}


if (
    exchange_rate_session_key
    not in st.session_state
):

    st.session_state[
        exchange_rate_session_key
    ] = {}


# ==================================================
# 보유 종목
# ==================================================

holdings = calculate_holdings(
    transactions
)


# ==================================================
# 선택 계좌 현재가 조회
# ==================================================

st.divider()

st.subheader(
    "📡 현재가 조회"
)


if not holdings:

    st.info(
        "현재 보유 중인 종목이 없습니다. "
        "매수 거래를 먼저 등록해주세요."
    )


else:

    st.caption(
        f"조회 대상 종목: {len(holdings)}개"
    )


    with st.expander(
        "조회할 종목 보기"
    ):

        for holding in (
            holdings.values()
        ):

            currency_code = (
                holding.get(
                    "currency"
                )
                or "KRW"
            ).upper()


            flag = (
                "🇺🇸"
                if currency_code
                == "USD"
                else "🇰🇷"
            )


            st.write(
                (
                    f'{flag} '
                    f'{holding["asset_name"]} '
                    f'({holding["symbol"]})'
                )
            )


    if st.button(
        "🔄 현재가 · 환율 새로고침",
        type="primary",
        use_container_width=True,
        key=(
            f"refresh_investment_prices_"
            f"{account_id}"
        ),
    ):

        new_prices = {}

        symbols = list(
            holdings.keys()
        )


        progress = st.progress(0)
        status_text = st.empty()


        for index, symbol in enumerate(
            symbols
        ):

            holding = (
                holdings[
                    symbol
                ]
            )


            asset_name = (
                holding.get(
                    "asset_name"
                )
                or symbol
            )


            status_text.caption(
                (
                    "현재가 조회 중: "
                    f"{asset_name}"
                )
            )


            new_prices[
                symbol
            ] = get_current_price(
                symbol
            )


            progress.progress(
                (
                    index + 1
                )
                / len(symbols)
            )


        # ------------------------------------------
        # 환율
        # ------------------------------------------

        currencies = {
            (
                holding.get(
                    "currency"
                )
                or "KRW"
            ).upper()

            for holding
            in holdings.values()
        }


        new_exchange_rates = {
            "KRW": 1.0
        }


        for currency_code in currencies:

            if currency_code == "KRW":
                continue


            status_text.caption(
                (
                    f"{currency_code}/KRW "
                    "환율 조회 중..."
                )
            )


            new_exchange_rates[
                currency_code
            ] = (
                get_current_exchange_rate(
                    currency_code,
                    "KRW",
                )
            )


        st.session_state[
            price_session_key
        ] = new_prices


        st.session_state[
            exchange_rate_session_key
        ] = new_exchange_rates


        st.session_state[
            price_time_key
        ] = datetime.now()


        progress.empty()
        status_text.empty()


        failed_symbols = [
            symbol

            for symbol, price
            in new_prices.items()

            if price is None
        ]


        failed_currencies = [
            currency_code

            for currency_code, rate
            in new_exchange_rates.items()

            if rate is None
        ]


        if (
            not failed_symbols
            and not failed_currencies
        ):

            st.success(
                "현재가와 환율을 정상적으로 조회했습니다."
            )

        else:

            if failed_symbols:

                st.warning(
                    "현재가 조회 실패: "
                    + ", ".join(
                        failed_symbols
                    )
                )


            if failed_currencies:

                st.warning(
                    "환율 조회 실패: "
                    + ", ".join(
                        failed_currencies
                    )
                )


# ==================================================
# 조회 결과
# ==================================================

price_map = (
    st.session_state.get(
        price_session_key,
        {},
    )
)


exchange_rate_map = (
    st.session_state.get(
        exchange_rate_session_key,
        {},
    )
)


last_price_time = (
    st.session_state.get(
        price_time_key
    )
)


if last_price_time:

    st.caption(
        "마지막 시세 조회: "
        f'{last_price_time.strftime("%Y-%m-%d %H:%M:%S")}'
    )


# ==================================================
# 현재 환율 표시
# ==================================================

if exchange_rate_map:

    foreign_rates = {
        currency_code: rate

        for currency_code, rate
        in exchange_rate_map.items()

        if (
            currency_code != "KRW"
            and rate is not None
        )
    }


    if foreign_rates:

        st.markdown(
            "##### 💱 적용 환율"
        )


        for (
            currency_code,
            rate,
        ) in foreign_rates.items():

            st.caption(
                (
                    f"1 {currency_code} = "
                    f"₩{rate:,.2f}"
                )
            )


# ==================================================
# 종목 평가
# ==================================================

if holdings:

    prices_ready = all(
        (
            symbol in price_map
            and
            price_map[
                symbol
            ] is not None
        )

        for symbol in holdings.keys()
    )


    rates_ready = True


    for holding in (
        holdings.values()
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
            not in exchange_rate_map
            or
            exchange_rate_map[
                currency_code
            ] is None
        ):

            rates_ready = False
            break


else:

    prices_ready = True
    rates_ready = True


evaluation_ready = (
    prices_ready
    and rates_ready
)


if evaluation_ready:

    evaluated_holdings = (
        evaluate_holdings(
            holdings,
            price_map=(
                price_map
            ),
            exchange_rate_map=(
                exchange_rate_map
            ),
        )
    )


    account_summary = (
        calculate_account_summary(
            transactions,
            evaluated_holdings,
        )
    )


else:

    evaluated_holdings = []

    account_summary = None


# ==================================================
# 선택 계좌 요약
# ==================================================

st.divider()

st.subheader(
    f'📊 {selected_account["name"]}'
)


st.caption(
    (
        f'{selected_account["owner"]} · '
        f'{selected_account["account_type"]}'
    )
)


if account_summary is None:

    st.warning(
        "현재가 또는 환율이 아직 조회되지 않았습니다. "
        "위의 현재가 · 환율 새로고침 버튼을 눌러주세요."
    )


else:

    col1, col2, col3 = (
        st.columns(3)
    )


    with col1:

        st.metric(
            "순투자금",
            (
                f'₩'
                f'{int(account_summary["net_contribution"]):,}'
            ),
        )


    with col2:

        st.metric(
            "현재 평가액",
            (
                f'₩'
                f'{int(account_summary["account_value"]):,}'
            ),
        )


    with col3:

        profit = (
            account_summary[
                "profit"
            ]
        )


        st.metric(
            "총 손익",
            (
                f'{"+₩" if profit >= 0 else "-₩"}'
                f'{abs(int(profit)):,}'
            ),
            (
                f'{account_summary["return_rate"]:+.2f}%'
            ),
        )


    col1, col2 = (
        st.columns(2)
    )


    with col1:

        st.metric(
            "보유주식 평가액",
            (
                f'₩'
                f'{int(account_summary["stock_value"]):,}'
            ),
        )


    with col2:

        st.metric(
            "계좌 내 현금",
            (
                f'₩'
                f'{int(account_summary["cash_balance"]):,}'
            ),
        )


# ==================================================
# 보유종목 표
# ==================================================

st.divider()

st.subheader(
    "📌 보유 종목"
)


if evaluated_holdings:

    holding_rows = []


    for holding in (
        evaluated_holdings
    ):

        holding_rows.append({
            "종목":
                holding[
                    "asset_name"
                ],

            "티커":
                holding[
                    "symbol"
                ],

            "통화":
                holding.get(
                    "currency",
                    "KRW",
                ),

            "수량":
                holding[
                    "quantity"
                ],

            "평균매수가":
                holding[
                    "average_price"
                ],

            "원화 평균원가":
                holding.get(
                    "average_price_krw"
                ),

            "현재가":
                holding[
                    "current_price"
                ],

            "현재 환율":
                holding.get(
                    "current_exchange_rate"
                ),

            "투자원가(KRW)":
                holding.get(
                    "cost_basis_krw"
                ),

            "평가액(KRW)":
                holding[
                    "market_value"
                ],

            "평가손익(KRW)":
                holding[
                    "profit"
                ],

            "수익률":
                holding[
                    "return_rate"
                ],
        })


    holding_df = (
        pd.DataFrame(
            holding_rows
        )
    )


    st.dataframe(
        holding_df,
        hide_index=True,
        width="stretch",
        column_config={
            "수량":
                st.column_config.NumberColumn(
                    format="%.4f",
                ),

            "평균매수가":
                st.column_config.NumberColumn(
                    format="%.2f",
                ),

            "원화 평균원가":
                st.column_config.NumberColumn(
                    format="₩ %.0f",
                ),

            "현재가":
                st.column_config.NumberColumn(
                    format="%.2f",
                ),

            "현재 환율":
                st.column_config.NumberColumn(
                    format="₩ %.2f",
                ),

            "투자원가(KRW)":
                st.column_config.NumberColumn(
                    format="₩ %.0f",
                ),

            "평가액(KRW)":
                st.column_config.NumberColumn(
                    format="₩ %.0f",
                ),

            "평가손익(KRW)":
                st.column_config.NumberColumn(
                    format="₩ %.0f",
                ),

            "수익률":
                st.column_config.NumberColumn(
                    format="%.2f %%",
                ),
        },
    )


elif holdings:

    st.caption(
        "현재가와 환율을 조회해주세요."
    )


else:

    st.caption(
        "현재 보유 중인 종목이 없습니다."
    )


# ==================================================
# 투자 거래 추가
# ==================================================

st.divider()

st.subheader(
    "➕ 투자 거래"
)


transaction_type = (
    st.radio(
        "거래 종류",
        [
            "입금",
            "매수",
            "매도",
            "배당",
            "출금",
        ],
        horizontal=True,
        key=(
            f"investment_tx_type_"
            f"{account_id}"
        ),
    )
)


transaction_date = (
    st.date_input(
        "거래일",
        value=date.today(),
        key=(
            f"investment_date_"
            f"{account_id}"
        ),
    )
)


# ==================================================
# 기본값
# ==================================================

symbol = None
asset_name = None
quantity = None
price = None
amount = None
fee = 0

currency = "KRW"
exchange_rate = 1.0


# ==================================================
# 입금 / 출금
# ==================================================

if transaction_type in [
    "입금",
    "출금",
]:

    amount = st.number_input(
        "금액",
        min_value=0,
        value=0,
        step=10000,
        key=(
            f"investment_amount_"
            f"{account_id}_"
            f"{transaction_type}"
        ),
    )


    if amount > 0:

        if transaction_type == "입금":

            after_available_cash = (
                available_cash_value
                - amount
            )

            st.caption(
                (
                    f"입금 후 공동 가용자산 예상: "
                    f"₩{after_available_cash:,.0f}"
                )
            )

            if (
                available_cash_asset
                and amount
                > available_cash_value
            ):

                st.warning(
                    "현재 공동 가용자산보다 큰 금액입니다."
                )


        elif transaction_type == "출금":

            after_available_cash = (
                available_cash_value
                + amount
            )

            st.caption(
                (
                    f"출금 후 공동 가용자산 예상: "
                    f"₩{after_available_cash:,.0f}"
                )
            )


# ==================================================
# 매수 / 매도
# ==================================================

elif transaction_type in [
    "매수",
    "매도",
]:

    st.markdown(
        "#### 📌 종목 선택"
    )


    # ==================================================
    # 현재 보유종목 목록
    # ==================================================

    current_holdings = (
        calculate_holdings(
            transactions
        )
    )


    selection_modes = []


    if current_holdings:
        selection_modes.append(
            "보유 종목에서 선택"
        )


    selection_modes.append(
        "새 종목 검색"
    )


    selection_mode = (
        st.radio(
            "종목 선택 방법",
            selection_modes,
            horizontal=True,
            key=(
                f"investment_symbol_mode_"
                f"{account_id}_"
                f"{transaction_type}"
            ),
        )
    )


    selected_result = None


    # ==================================================
    # 1. 보유 종목에서 선택
    # ==================================================

    if (
        selection_mode
        == "보유 종목에서 선택"
    ):

        holding_options = {}


        for (
            holding_symbol,
            holding,
        ) in current_holdings.items():

            holding_currency = (
                holding.get(
                    "currency"
                )
                or "KRW"
            ).upper()


            flag = (
                "🇺🇸"
                if holding_currency
                == "USD"
                else "🇰🇷"
            )


            label = (
                f"{flag} "
                f'{holding["asset_name"]} · '
                f'{holding_symbol} · '
                f'{holding_currency}'
            )


            holding_options[
                label
            ] = {
                "symbol":
                    holding_symbol,

                "name":
                    holding[
                        "asset_name"
                    ],

                "currency":
                    holding_currency,

                "exchange":
                    "",
            }


        selected_holding_label = (
            st.selectbox(
                "보유 종목",
                list(
                    holding_options.keys()
                ),
                key=(
                    f"existing_holding_"
                    f"{account_id}_"
                    f"{transaction_type}"
                ),
            )
        )


        selected_result = (
            holding_options[
                selected_holding_label
            ]
        )


        selected_holding = (
            current_holdings[
                selected_result[
                    "symbol"
                ]
            ]
        )


        st.caption(
            (
                "현재 보유수량: "
                f'{selected_holding["quantity"]:,.4f}'
            )
        )


        if transaction_type == "매도":

            st.info(
                (
                    "매도 수량은 현재 보유수량을 "
                    "초과하지 않도록 입력해주세요."
                )
            )


    # ==================================================
    # 2. 새 종목 검색
    # ==================================================

    else:

        st.markdown(
            "#### 🔎 종목 검색"
        )


        search_query = st.text_input(
            "종목명 또는 티커",
            placeholder=(
                "예: TIME 미국 나스닥 / "
                "Apple / NVIDIA / 삼성전자"
            ),
            key=(
                f"investment_search_query_"
                f"{account_id}_"
                f"{transaction_type}"
            ),
        )


        search_button = st.button(
            "종목 검색",
            use_container_width=True,
            key=(
                f"investment_search_button_"
                f"{account_id}_"
                f"{transaction_type}"
            ),
        )


        search_result_key = (
            f"investment_search_results_"
            f"{account_id}_"
            f"{transaction_type}"
        )


        if search_button:

            if not search_query.strip():

                st.warning(
                    "검색할 종목명을 입력해주세요."
                )

            else:

                with st.spinner(
                    "종목을 검색하고 있습니다..."
                ):

                    results = (
                        search_investment_symbols(
                            search_query,
                            max_results=30,
                        )
                    )


                st.session_state[
                    search_result_key
                ] = results


                if not results:

                    st.warning(
                        "검색 결과가 없습니다. "
                        "다른 검색어로 다시 검색해주세요."
                    )


        search_results = (
            st.session_state.get(
                search_result_key,
                [],
            )
        )


        if search_results:

            result_options = {}


            for result in search_results:

                symbol_text = (
                    result[
                        "symbol"
                    ]
                )


                name_text = (
                    result[
                        "name"
                    ]
                )


                exchange_text = (
                    result.get(
                        "exchange"
                    )
                    or ""
                )


                currency_text = (
                    result.get(
                        "currency"
                    )
                    or ""
                )


                source_text = (
                    result.get(
                        "source"
                    )
                    or ""
                )


                label = (
                    f"{name_text} · "
                    f"{symbol_text}"
                )


                if exchange_text:

                    label += (
                        f" · {exchange_text}"
                    )


                if currency_text:

                    label += (
                        f" · {currency_text}"
                    )


                if source_text:

                    label += (
                        f" · {source_text}"
                    )


                result_options[
                    label
                ] = result


            selected_result_label = (
                st.selectbox(
                    "검색 결과에서 선택",
                    list(
                        result_options.keys()
                    ),
                    key=(
                        f"investment_search_select_"
                        f"{account_id}_"
                        f"{transaction_type}"
                    ),
                )
            )


            selected_result = (
                result_options[
                    selected_result_label
                ]
            )


    # ==================================================
    # 선택된 종목
    # ==================================================

    if selected_result:

        symbol = (
            selected_result[
                "symbol"
            ]
        )


        asset_name = (
            selected_result[
                "name"
            ]
        )


        currency = (
            selected_result.get(
                "currency"
            )
            or "KRW"
        ).upper()


        st.success(
            "종목이 선택되었습니다."
        )


        col1, col2 = (
            st.columns(2)
        )


        with col1:

            st.text_input(
                "종목명",
                value=asset_name,
                disabled=True,
                key=(
                    f"selected_asset_name_"
                    f"{account_id}_"
                    f"{transaction_type}"
                ),
            )


        with col2:

            st.text_input(
                "티커",
                value=symbol,
                disabled=True,
                key=(
                    f"selected_symbol_"
                    f"{account_id}_"
                    f"{transaction_type}"
                ),
            )


        st.caption(
            f"거래 통화: {currency}"
        )


        # ==================================================
        # 현재가 확인
        # ==================================================

        if st.button(
            "📡 현재가 확인",
            key=(
                f"test_selected_price_"
                f"{account_id}_"
                f"{transaction_type}_"
                f"{symbol}"
            ),
        ):

            with st.spinner(
                "현재가를 조회하고 있습니다..."
            ):

                test_price = (
                    get_current_price(
                        symbol
                    )
                )


            if test_price is None:

                st.error(
                    "현재가를 조회하지 못했습니다."
                )


            elif currency == "USD":

                st.success(
                    (
                        "현재가 조회 성공: "
                        f"${test_price:,.2f}"
                    )
                )


            else:

                st.success(
                    (
                        "현재가 조회 성공: "
                        f"₩{test_price:,.0f}"
                    )
                )


        # ==================================================
        # 수량
        # ==================================================

        max_quantity = None


        if (
            transaction_type
            == "매도"
            and
            symbol
            in current_holdings
        ):

            max_quantity = float(
                current_holdings[
                    symbol
                ][
                    "quantity"
                ]
            )


        if max_quantity is not None:

            quantity = (
                st.number_input(
                    "매도 수량",
                    min_value=0.0,
                    max_value=(
                        max_quantity
                    ),
                    value=0.0,
                    step=1.0,
                    key=(
                        f"investment_quantity_"
                        f"{account_id}_"
                        f"{transaction_type}"
                    ),
                )
            )


            if st.button(
                "전량 입력",
                key=(
                    f"sell_all_"
                    f"{account_id}_"
                    f"{symbol}"
                ),
            ):

                st.session_state[
                    (
                        f"investment_quantity_"
                        f"{account_id}_"
                        f"{transaction_type}"
                    )
                ] = max_quantity

                st.rerun()


        else:

            quantity = (
                st.number_input(
                    "수량",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key=(
                        f"investment_quantity_"
                        f"{account_id}_"
                        f"{transaction_type}"
                    ),
                )
            )


        # ==================================================
        # 거래가격
        # ==================================================

        price_label = (
            "1주당 거래가격 ($)"
            if currency == "USD"
            else "1주당 거래가격 (₩)"
        )


        price = st.number_input(
            price_label,
            min_value=0.0,
            value=0.0,
            step=(
                0.01
                if currency == "USD"
                else 100.0
            ),
            key=(
                f"investment_price_"
                f"{account_id}_"
                f"{transaction_type}"
            ),
        )


        # ==================================================
        # 수수료
        # ==================================================

        fee = st.number_input(
            (
                "수수료 ($)"
                if currency == "USD"
                else "수수료 (₩)"
            ),
            min_value=0.0,
            value=0.0,
            step=(
                0.01
                if currency == "USD"
                else 100.0
            ),
            key=(
                f"investment_fee_"
                f"{account_id}_"
                f"{transaction_type}"
            ),
        )


        # ==================================================
        # USD 환율
        # ==================================================

        if currency == "USD":

            st.markdown(
                "##### 💱 거래 당시 환율"
            )


            auto_exchange_rate = (
                get_historical_exchange_rate(
                    transaction_date,
                    "USD",
                    "KRW",
                )
            )


            if auto_exchange_rate:

                exchange_rate = (
                    st.number_input(
                        "USD/KRW 적용환율",
                        min_value=0.0,
                        value=float(
                            auto_exchange_rate
                        ),
                        step=0.1,
                        key=(
                            f"investment_fx_"
                            f"{account_id}_"
                            f"{transaction_type}_"
                            f"{transaction_date}"
                        ),
                    )
                )


                st.caption(
                    "거래일 기준 환율입니다. "
                    "실제 증권사 적용환율과 다르면 수정해주세요."
                )


            else:

                exchange_rate = (
                    st.number_input(
                        "USD/KRW 적용환율",
                        min_value=0.0,
                        value=0.0,
                        step=0.1,
                        key=(
                            f"investment_fx_manual_"
                            f"{account_id}_"
                            f"{transaction_type}_"
                            f"{transaction_date}"
                        ),
                    )
                )


                st.warning(
                    "거래일 환율을 자동 조회하지 못했습니다."
                )


        else:

            exchange_rate = 1.0


        # ==================================================
        # 거래 금액 미리보기
        # ==================================================

        if (
            quantity
            and quantity > 0
            and price
            and price > 0
        ):

            local_amount = (
                quantity
                * price
            )


            if currency == "USD":

                krw_amount = (
                    local_amount
                    * exchange_rate
                )


                st.info(
                    (
                        f"거래금액: "
                        f"${local_amount:,.2f}\n\n"
                        f"원화 환산: "
                        f"₩{int(krw_amount):,}"
                    )
                )


            else:

                st.info(
                    (
                        "거래금액: "
                        f"₩{int(local_amount):,}"
                    )
                )


    else:

        st.info(
            "거래할 종목을 선택해주세요."
        )
# ==================================================
# 배당
# ==================================================

elif transaction_type == "배당":

    currency = st.radio(
        "배당 통화",
        [
            "KRW",
            "USD",
        ],
        horizontal=True,
        key=(
            f"dividend_currency_"
            f"{account_id}"
        ),
    )


    symbol = st.text_input(
        "종목 티커",
        placeholder="선택사항",
        key=(
            f"dividend_symbol_"
            f"{account_id}"
        ),
    )


    asset_name = st.text_input(
        "종목명",
        placeholder=(
            "예: Apple"
        ),
        key=(
            f"dividend_name_"
            f"{account_id}"
        ),
    )


    amount = st.number_input(
        (
            "배당금 ($)"
            if currency == "USD"
            else "배당금 (₩)"
        ),
        min_value=0.0,
        value=0.0,
        step=(
            0.01
            if currency == "USD"
            else 1000.0
        ),
        key=(
            f"dividend_amount_"
            f"{account_id}"
        ),
    )


    if currency == "USD":

        auto_exchange_rate = (
            get_historical_exchange_rate(
                transaction_date,
                "USD",
                "KRW",
            )
        )


        exchange_rate = (
            st.number_input(
                "배당 당시 USD/KRW 환율",
                min_value=0.0,
                value=float(
                    auto_exchange_rate
                    or 0
                ),
                step=0.1,
                key=(
                    f"dividend_fx_"
                    f"{account_id}_"
                    f"{transaction_date}"
                ),
            )
        )


# ==================================================
# 메모
# ==================================================

memo = st.text_input(
    "메모",
    key=(
        f"investment_memo_"
        f"{account_id}_"
        f"{transaction_type}"
    ),
)


# ==================================================
# 투자 거래 저장
# ==================================================

if st.button(
    "투자 거래 저장",
    type="primary",
    use_container_width=True,
    key=(
        f"save_investment_tx_"
        f"{account_id}"
    ),
):

    valid = True


    if transaction_type in [
        "입금",
        "출금",
        "배당",
    ]:

        if (
            amount is None
            or amount <= 0
        ):

            st.error(
                "금액을 입력해주세요."
            )

            valid = False


    if (
        transaction_type
        in ["입금", "출금"]
        and not available_cash_asset
    ):

        st.error(
            "먼저 설정 페이지에서 공동 가용자산을 설정해주세요."
        )

        valid = False


    if (
        transaction_type == "입금"
        and available_cash_asset
        and amount is not None
        and amount > available_cash_value
    ):

        st.error(
            (
                "공동 가용자산 잔액이 부족합니다. "
                f"현재 가용자산: ₩{available_cash_value:,.0f}"
            )
        )

        valid = False


    elif transaction_type in [
        "매수",
        "매도",
    ]:

        if not (
            symbol
            and symbol.strip()
        ):

            st.error(
                "종목 티커를 입력해주세요."
            )

            valid = False


        elif not (
            asset_name
            and asset_name.strip()
        ):

            st.error(
                "종목명을 입력해주세요."
            )

            valid = False


        elif (
            quantity is None
            or quantity <= 0
        ):

            st.error(
                "수량을 입력해주세요."
            )

            valid = False


        elif (
            price is None
            or price <= 0
        ):

            st.error(
                "거래가격을 입력해주세요."
            )

            valid = False


    if (
        currency != "KRW"
        and exchange_rate <= 0
    ):

        st.error(
            "외화 거래의 적용환율을 입력해주세요."
        )

        valid = False


    if valid:

        try:

            add_investment_transaction(
                account_id=(
                    account_id
                ),
                transaction_date=(
                    transaction_date
                ),
                transaction_type=(
                    transaction_type
                ),
                symbol=symbol,
                asset_name=(
                    asset_name
                ),
                quantity=quantity,
                price=price,
                amount=amount,
                fee=fee,
                memo=memo,
                currency=currency,
                exchange_rate=(
                    exchange_rate
                ),
            )


            # 기존 시세 캐시 초기화
            st.session_state[
                price_session_key
            ] = {}


            st.session_state[
                exchange_rate_session_key
            ] = {}


            st.success(
                "투자 거래를 저장했습니다."
            )

            st.rerun()


        except Exception as e:

            st.error(
                "거래를 저장하지 "
                f"못했습니다: {e}"
            )


# ==================================================
# 투자 거래내역
# ==================================================

st.divider()

st.subheader(
    "📋 투자 거래내역"
)


if transactions:

    transaction_rows = []


    for tx in transactions:

        tx_type = (
            tx["transaction_type"]
        )


        tx_currency = (
            tx.get(
                "currency"
            )
            or "KRW"
        )


        if tx_type in [
            "매수",
            "매도",
        ]:

            transaction_amount = (
                float(
                    tx.get(
                        "quantity"
                    )
                    or 0
                )
                *
                float(
                    tx.get(
                        "price"
                    )
                    or 0
                )
            )

        else:

            transaction_amount = (
                float(
                    tx.get(
                        "amount"
                    )
                    or 0
                )
            )


        transaction_rows.append({
            "거래일":
                tx[
                    "transaction_date"
                ],

            "종류":
                tx_type,

            "종목":
                (
                    tx.get(
                        "asset_name"
                    )
                    or ""
                ),

            "티커":
                (
                    tx.get(
                        "symbol"
                    )
                    or ""
                ),

            "통화":
                tx_currency,

            "수량":
                tx.get(
                    "quantity"
                ),

            "거래가격":
                tx.get(
                    "price"
                ),

            "금액":
                transaction_amount,

            "적용환율":
                tx.get(
                    "exchange_rate"
                ),

            "수수료":
                float(
                    tx.get(
                        "fee"
                    )
                    or 0
                ),

            "가용자산반영":
                (
                    "반영됨"
                    if bool(
                        tx.get(
                            "affects_available_cash",
                            False,
                        )
                    )
                    else (
                        "기존기록"
                        if tx_type
                        in ["입금", "출금"]
                        else "-"
                    )
                ),

            "메모":
                (
                    tx.get(
                        "memo"
                    )
                    or ""
                ),
        })


    transaction_df = (
        pd.DataFrame(
            transaction_rows
        )
    )


    st.dataframe(
        transaction_df,
        hide_index=True,
        width="stretch",
    )


    # ==================================================
    # 거래 삭제
    # ==================================================

    transaction_options = {
        (
            f'{tx["transaction_date"]} · '
            f'{tx["transaction_type"]} · '
            f'{tx.get("asset_name") or ""} · '
            f'#{tx["id"]}'
        ):
        tx

        for tx in transactions
    }


    delete_label = (
        st.selectbox(
            "삭제할 투자 거래",
            list(
                transaction_options.keys()
            ),
        )
    )


    delete_target = (
        transaction_options[
            delete_label
        ]
    )


    delete_affects_cash = bool(
        delete_target.get(
            "affects_available_cash",
            False,
        )
    )


    if delete_affects_cash:

        if (
            delete_target.get(
                "transaction_type"
            )
            == "입금"
        ):

            st.caption(
                "이 입금 기록을 삭제하면 해당 금액이 "
                "공동 가용자산으로 되돌아갑니다."
            )

        elif (
            delete_target.get(
                "transaction_type"
            )
            == "출금"
        ):

            st.caption(
                "이 출금 기록을 삭제하면 해당 금액만큼 "
                "공동 가용자산이 다시 감소합니다."
            )


    elif (
        delete_target.get(
            "transaction_type"
        )
        in ["입금", "출금"]
    ):

        st.caption(
            "전환 이전의 기존 입출금 기록입니다. "
            "삭제해도 현재 공동 가용자산은 변경하지 않습니다."
        )


    if (
        "investment_delete_target"
        not in st.session_state
    ):

        st.session_state[
            "investment_delete_target"
        ] = None


    if (
        st.session_state[
            "investment_delete_target"
        ]
        != delete_target["id"]
    ):

        st.session_state[
            "investment_delete_confirm"
        ] = False

        st.session_state[
            "investment_delete_target"
        ] = delete_target["id"]


    if (
        "investment_delete_confirm"
        not in st.session_state
    ):

        st.session_state[
            "investment_delete_confirm"
        ] = False


    if not st.session_state[
        "investment_delete_confirm"
    ]:

        if st.button(
            "선택한 투자 거래 삭제",
            key=(
                f"delete_investment_tx_"
                f'{delete_target["id"]}'
            ),
        ):

            st.session_state[
                "investment_delete_confirm"
            ] = True

            st.rerun()


    else:

        st.warning(
            "선택한 투자 거래를 "
            "정말 삭제하시겠습니까?"
        )


        col1, col2 = st.columns(2)


        with col1:

            if st.button(
                "삭제 확인",
                type="primary",
                use_container_width=True,
                key=(
                    "confirm_investment_delete"
                ),
            ):

                try:

                    delete_investment_transaction(
                        delete_target[
                            "id"
                        ]
                    )


                    st.session_state[
                        "investment_delete_confirm"
                    ] = False


                    st.session_state[
                        "investment_delete_target"
                    ] = None


                    st.session_state[
                        price_session_key
                    ] = {}


                    st.session_state[
                        exchange_rate_session_key
                    ] = {}


                    st.rerun()


                except Exception as e:

                    st.error(
                        "투자 거래를 삭제하지 "
                        f"못했습니다: {e}"
                    )


        with col2:

            if st.button(
                "취소",
                use_container_width=True,
                key=(
                    "cancel_investment_delete"
                ),
            ):

                st.session_state[
                    "investment_delete_confirm"
                ] = False

                st.rerun()


else:

    st.caption(
        "등록된 투자 거래가 없습니다."
    )


# ==================================================
# 투자계좌 설정
# ==================================================

st.divider()


with st.expander(
    "⚙️ 선택한 투자계좌 설정"
):

    owners = [
        "나",
        "남편",
        "공동",
    ]


    account_types = [
        "ISA",
        "연금저축",
        "기타",
    ]


    try:

        owner_index = (
            owners.index(
                selected_account[
                    "owner"
                ]
            )
        )

    except ValueError:

        owner_index = 0


    try:

        account_type_index = (
            account_types.index(
                selected_account[
                    "account_type"
                ]
            )
        )

    except ValueError:

        account_type_index = 0


    with st.form(
        f"edit_investment_account_{account_id}"
    ):

        edit_owner = st.selectbox(
            "소유자",
            owners,
            index=owner_index,
        )


        edit_account_type = (
            st.selectbox(
                "계좌 유형",
                account_types,
                index=(
                    account_type_index
                ),
            )
        )


        edit_name = st.text_input(
            "계좌명",
            value=(
                selected_account[
                    "name"
                ]
            ),
        )


        edit_memo = st.text_input(
            "메모",
            value=(
                selected_account.get(
                    "memo"
                )
                or ""
            ),
        )


        edit_account_submit = (
            st.form_submit_button(
                "계좌 정보 저장",
                use_container_width=True,
            )
        )


    if edit_account_submit:

        if not edit_name.strip():

            st.error(
                "계좌명을 입력해주세요."
            )

        else:

            update_investment_account(
                account_id=(
                    account_id
                ),
                owner=edit_owner,
                account_type=(
                    edit_account_type
                ),
                name=edit_name,
                memo=edit_memo,
            )

            st.success(
                "투자계좌 정보를 수정했습니다."
            )

            st.rerun()


    st.warning(
        "투자계좌를 삭제하면 해당 계좌의 모든 투자 거래도 함께 삭제됩니다. "
        "가용자산 연동 이후의 입금·출금 기록이 있다면 "
        "그 가용자산 영향도 함께 원복됩니다."
    )


    if (
        "investment_account_delete_target"
        not in st.session_state
    ):

        st.session_state[
            "investment_account_delete_target"
        ] = None


    if st.session_state[
        "investment_account_delete_target"
    ] != account_id:

        st.session_state[
            "investment_account_delete_confirm"
        ] = False

        st.session_state[
            "investment_account_delete_target"
        ] = account_id


    if (
        "investment_account_delete_confirm"
        not in st.session_state
    ):

        st.session_state[
            "investment_account_delete_confirm"
        ] = False


    if not st.session_state[
        "investment_account_delete_confirm"
    ]:

        if st.button(
            "투자계좌 삭제",
            key=(
                f"delete_investment_account_"
                f"{account_id}"
            ),
        ):

            st.session_state[
                "investment_account_delete_confirm"
            ] = True

            st.rerun()


    else:

        st.error(
            (
                f"'{selected_account['name']}' 계좌와 "
                "모든 투자 거래를 삭제합니다."
            )
        )


        col1, col2 = st.columns(2)


        with col1:

            if st.button(
                "계좌 삭제 확인",
                type="primary",
                use_container_width=True,
                key=(
                    f"confirm_account_delete_"
                    f"{account_id}"
                ),
            ):

                try:

                    delete_investment_account(
                        account_id
                    )


                    st.session_state[
                        "investment_account_delete_confirm"
                    ] = False


                    st.session_state[
                        "investment_account_delete_target"
                    ] = None


                    st.rerun()


                except Exception as e:

                    st.error(
                        "투자계좌를 삭제하지 "
                        f"못했습니다: {e}"
                    )


        with col2:

            if st.button(
                "취소",
                use_container_width=True,
                key=(
                    f"cancel_account_delete_"
                    f"{account_id}"
                ),
            ):

                st.session_state[
                    "investment_account_delete_confirm"
                ] = False

                st.rerun()