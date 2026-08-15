import datetime

import pandas as pd
import streamlit as st

from services.database import (
    get_assets,
    get_savings_detail,
    save_savings_detail,
    get_savings_payments,
    record_savings_payment,
    delete_savings_payment,
    get_available_cash_asset,
)


# ==================================================
# 기본 설정
# ==================================================

st.title("🏦 적금 관리")

st.caption(
    "적금 납입을 기록하면 공동 가용자산에서 해당 금액이 빠지고 "
    "선택한 적금의 현재 잔액이 자동으로 증가합니다. "
    "월 납입액·금리·가입기간·만기정보도 함께 관리합니다."
)


# ==================================================
# 유틸
# ==================================================

def parse_date(value):

    if not value:
        return None

    if isinstance(
        value,
        datetime.date,
    ):
        return value

    try:
        return datetime.date.fromisoformat(
            str(value)
        )

    except Exception:
        return None


def calculate_expected_savings(
    monthly_payment,
    annual_rate,
    term_months,
):
    """
    정액적립식 적금의 세전 예상치.

    매월 동일 금액 납입을 가정한 단순 추정값.
    실제 금융기관의 일수 계산,
    우대금리, 세금 등과 차이가 있을 수 있음.
    """

    if (
        monthly_payment <= 0
        or term_months <= 0
    ):
        return {
            "principal": 0,
            "interest": 0,
            "maturity_amount": 0,
        }


    principal = (
        monthly_payment
        * term_months
    )


    monthly_rate = (
        annual_rate
        / 100
        / 12
    )


    # 첫 납입금은 N개월,
    # 마지막 납입금은 1개월 이자 발생으로 추정
    interest_month_sum = (
        term_months
        * (
            term_months + 1
        )
        / 2
    )


    interest = (
        monthly_payment
        * monthly_rate
        * interest_month_sum
    )


    return {
        "principal":
            principal,

        "interest":
            interest,

        "maturity_amount":
            principal
            + interest,
    }


# ==================================================
# 적금 자산 가져오기
# ==================================================

assets = (
    get_assets()
    or []
)

available_cash_asset = (
    get_available_cash_asset()
)


savings_assets = [
    asset
    for asset in assets
    if asset.get(
        "asset_type"
    ) == "적금"
]


if not savings_assets:

    st.info(
        "등록된 적금 자산이 없습니다.\n\n"
        "먼저 자산 페이지에서 자산 종류를 "
        "'적금'으로 선택해 등록해주세요."
    )

    st.stop()


# ==================================================
# 전체 적금 요약
# ==================================================

st.subheader(
    "📊 적금 현황"
)


total_balance = sum(
    float(
        asset.get(
            "current_value"
        )
        or 0
    )
    for asset in savings_assets
)


total_monthly_payment = 0


for asset in savings_assets:

    detail = (
        get_savings_detail(
            asset["id"]
        )
    )


    if detail:

        total_monthly_payment += float(
            detail.get(
                "monthly_payment"
            )
            or 0
        )


available_cash_value = float(
    available_cash_asset.get(
        "current_value",
        0,
    )
    or 0
) if available_cash_asset else 0


col1, col2, col3, col4 = (
    st.columns(4)
)


with col1:

    st.metric(
        "현재 가용자산",
        f"₩{available_cash_value:,.0f}",
    )


with col2:

    st.metric(
        "적금 현재잔액",
        f"₩{total_balance:,.0f}",
    )


with col3:

    st.metric(
        "월 총 납입액",
        f"₩{total_monthly_payment:,.0f}",
    )


with col4:

    st.metric(
        "적금 개수",
        f"{len(savings_assets)}개",
    )


if not available_cash_asset:

    st.warning(
        "가용자산 기준금액이 아직 설정되어 있지 않습니다. "
        "설정 → 우리집 가용자산에서 먼저 현재 금액을 입력해주세요."
    )


st.divider()


# ==================================================
# 적금 선택
# ==================================================

asset_options = {}


for asset in savings_assets:

    label = (
        f'{asset["name"]}'
        f' · {asset["owner"]}'
    )

    asset_options[
        label
    ] = asset


selected_label = (
    st.selectbox(
        "관리할 적금",
        list(
            asset_options.keys()
        ),
    )
)


selected_asset = (
    asset_options[
        selected_label
    ]
)


asset_id = (
    selected_asset[
        "id"
    ]
)


current_balance = float(
    selected_asset.get(
        "current_value"
    )
    or 0
)


detail = (
    get_savings_detail(
        asset_id
    )
    or {}
)


# ==================================================
# 현재 상태
# ==================================================

st.subheader(
    selected_asset[
        "name"
    ]
)


owner = (
    selected_asset.get(
        "owner"
    )
    or "-"
)


asset_col1, asset_col2, asset_col3 = (
    st.columns(3)
)


with asset_col1:

    st.metric(
        "현재 적금잔액",
        f"₩{current_balance:,.0f}",
    )


with asset_col2:

    st.metric(
        "소유자",
        owner,
    )


with asset_col3:

    st.metric(
        "현재 가용자산",
        f"₩{available_cash_value:,.0f}",
    )


st.caption(
    "앞으로 이 화면에서 적금 납입을 기록하면 "
    "가용자산은 감소하고 해당 적금 잔액은 같은 금액만큼 자동 증가합니다."
)


# ==================================================
# 상세정보 입력
# ==================================================

st.subheader(
    "⚙️ 적금 조건"
)


existing_start_date = (
    parse_date(
        detail.get(
            "start_date"
        )
    )
    or datetime.date.today()
)


existing_maturity_date = (
    parse_date(
        detail.get(
            "maturity_date"
        )
    )
    or (
        datetime.date.today()
        + datetime.timedelta(
            days=365
        )
    )
)


with st.form(
    f"savings_detail_form_{asset_id}"
):

    monthly_payment = (
        st.number_input(
            "월 납입금액",
            min_value=0.0,
            value=float(
                detail.get(
                    "monthly_payment"
                )
                or 0
            ),
            step=10000.0,
            format="%.0f",
        )
    )


    interest_rate = (
        st.number_input(
            "적용 금리 (%)",
            min_value=0.0,
            value=float(
                detail.get(
                    "interest_rate"
                )
                or 0
            ),
            step=0.1,
            format="%.2f",
        )
    )


    col1, col2 = (
        st.columns(2)
    )


    with col1:

        start_date = (
            st.date_input(
                "가입일",
                value=(
                    existing_start_date
                ),
            )
        )


    with col2:

        maturity_date = (
            st.date_input(
                "만기일",
                value=(
                    existing_maturity_date
                ),
            )
        )


    col1, col2 = (
        st.columns(2)
    )


    with col1:

        term_months = (
            st.number_input(
                "가입기간 (개월)",
                min_value=1,
                max_value=120,
                value=int(
                    detail.get(
                        "term_months"
                    )
                    or 12
                ),
                step=1,
            )
        )


    with col2:

        payment_day = (
            st.number_input(
                "매월 납입일",
                min_value=1,
                max_value=31,
                value=int(
                    detail.get(
                        "payment_day"
                    )
                    or 1
                ),
                step=1,
            )
        )


    submitted = (
        st.form_submit_button(
            "💾 적금 정보 저장",
            use_container_width=True,
        )
    )


if submitted:

    if (
        maturity_date
        <= start_date
    ):

        st.error(
            "만기일은 가입일보다 "
            "뒤여야 합니다."
        )

    else:

        save_savings_detail(
            asset_id=asset_id,
            monthly_payment=(
                monthly_payment
            ),
            interest_rate=(
                interest_rate
            ),
            start_date=(
                start_date
            ),
            maturity_date=(
                maturity_date
            ),
            payment_day=(
                payment_day
            ),
            term_months=(
                term_months
            ),
        )


        st.success(
            "적금 정보가 저장되었습니다."
        )

        st.rerun()


# ==================================================
# 예상 만기
# ==================================================

if detail:

    st.divider()

    st.subheader(
        "🎯 만기 예상"
    )


    monthly_payment_saved = float(
        detail.get(
            "monthly_payment"
        )
        or 0
    )


    interest_rate_saved = float(
        detail.get(
            "interest_rate"
        )
        or 0
    )


    term_months_saved = int(
        detail.get(
            "term_months"
        )
        or 0
    )


    estimate = (
        calculate_expected_savings(
            monthly_payment_saved,
            interest_rate_saved,
            term_months_saved,
        )
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    with col1:

        st.metric(
            "총 납입 예정 원금",
            (
                f'₩'
                f'{estimate["principal"]:,.0f}'
            ),
        )


    with col2:

        st.metric(
            "예상 세전 이자",
            (
                f'₩'
                f'{estimate["interest"]:,.0f}'
            ),
        )


    with col3:

        st.metric(
            "예상 세전 만기금액",
            (
                f'₩'
                f'{estimate["maturity_amount"]:,.0f}'
            ),
        )


    st.caption(
        "예상 만기금액은 매월 동일한 금액을 납입하는 "
        "정액적립식 기준의 단순 추정값입니다. "
        "실제 은행의 일수 계산, 우대금리, 이자소득세 등에 "
        "따라 실제 수령액과 차이가 날 수 있습니다."
    )


    # ==================================================
    # 만기 D-day
    # ==================================================

    maturity_date_saved = (
        parse_date(
            detail.get(
                "maturity_date"
            )
        )
    )


    if maturity_date_saved:

        today = (
            datetime.date.today()
        )


        remaining_days = (
            maturity_date_saved
            - today
        ).days


        if remaining_days > 0:

            st.info(
                f"📅 만기까지 D-{remaining_days}"
            )


        elif remaining_days == 0:

            st.success(
                "🎉 오늘이 만기일입니다."
            )


        else:

            st.warning(
                "이미 만기가 지난 적금입니다."
            )

# ==================================================
# 납입 관리
# ==================================================

st.divider()

st.subheader(
    "💳 적금 납입 관리"
)


saved_monthly_payment = float(
    detail.get(
        "monthly_payment"
    )
    or 0
)


saved_payment_day = int(
    detail.get(
        "payment_day"
    )
    or 1
)


today = datetime.date.today()


# ==================================================
# 이번 달 납입 여부 확인
# ==================================================

payments = (
    get_savings_payments(
        asset_id
    )
    or []
)


this_month_payments = [
    payment
    for payment in payments
    if (
        parse_date(
            payment.get(
                "payment_date"
            )
        )
        and
        parse_date(
            payment.get(
                "payment_date"
            )
        ).year
        == today.year
        and
        parse_date(
            payment.get(
                "payment_date"
            )
        ).month
        == today.month
    )
]


this_month_paid = sum(
    float(
        payment.get(
            "amount"
        )
        or 0
    )
    for payment
    in this_month_payments
)


# ==================================================
# 이번 달 상태
# ==================================================

col1, col2, col3 = (
    st.columns(3)
)


with col1:

    st.metric(
        "이번 달 예정",
        f"₩{saved_monthly_payment:,.0f}",
    )


with col2:

    st.metric(
        "이번 달 납입",
        f"₩{this_month_paid:,.0f}",
    )


with col3:

    remaining_payment = max(
        saved_monthly_payment
        - this_month_paid,
        0,
    )


    st.metric(
        "남은 납입액",
        f"₩{remaining_payment:,.0f}",
    )


if (
    saved_monthly_payment > 0
    and
    this_month_paid
    >= saved_monthly_payment
):

    st.success(
        "✅ 이번 달 적금 납입이 완료되었습니다."
    )


elif (
    saved_monthly_payment > 0
    and
    this_month_paid > 0
):

    st.warning(
        "이번 달 납입이 일부만 기록되어 있습니다."
    )


elif (
    saved_monthly_payment > 0
):

    st.info(
        (
            f"이번 달 예정 납입액은 "
            f"₩{saved_monthly_payment:,.0f}입니다."
        )
    )


# ==================================================
# 납입 등록
# ==================================================

if available_cash_asset:

    st.caption(
        "적금 납입은 지출이 아니라 자산 이동입니다. "
        "납입금액만큼 가용자산이 줄고 적금자산이 늘어나므로 "
        "총자산은 변하지 않습니다."
    )

else:

    st.warning(
        "가용자산이 설정되지 않아 새 적금 납입을 기록할 수 없습니다."
    )


with st.expander(
    "➕ 납입 완료 기록",
    expanded=False,
):

    with st.form(
        f"savings_payment_form_{asset_id}"
    ):

        payment_date = (
            st.date_input(
                "납입일",
                value=today,
            )
        )


        default_payment_amount = (
            remaining_payment
            if remaining_payment > 0
            else saved_monthly_payment
        )


        payment_amount = (
            st.number_input(
                "납입금액",
                min_value=0.0,
                value=float(
                    default_payment_amount
                    or 0
                ),
                step=10000.0,
                format="%.0f",
            )
        )


        payment_memo = (
            st.text_input(
                "메모",
                placeholder=(
                    "예: 8월 정기납입"
                ),
            )
        )


        if payment_amount > 0 and available_cash_asset:

            after_available_cash = (
                available_cash_value
                - payment_amount
            )

            after_savings_balance = (
                current_balance
                + payment_amount
            )

            st.caption(
                (
                    f"납입 후 예상: 가용자산 "
                    f"₩{after_available_cash:,.0f} / "
                    f"적금잔액 ₩{after_savings_balance:,.0f}"
                )
            )


        payment_submit = (
            st.form_submit_button(
                "✅ 납입 완료",
                use_container_width=True,
            )
        )


    if payment_submit:

        if not available_cash_asset:

            st.error(
                "먼저 설정 페이지에서 가용자산 기준금액을 설정해주세요."
            )

        elif payment_amount <= 0:

            st.error(
                "납입금액을 입력해주세요."
            )

        elif available_cash_value < payment_amount:

            st.error(
                (
                    "가용자산 잔액이 부족합니다. "
                    f"현재 가용자산: ₩{available_cash_value:,.0f}"
                )
            )


        else:

            try:

                record_savings_payment(
                    asset_id=asset_id,
                    payment_date=(
                        payment_date
                    ),
                    amount=(
                        payment_amount
                    ),
                    memo=(
                        payment_memo
                    ),
                )


                st.success(
                    (
                        f"₩{payment_amount:,.0f} "
                        "납입을 기록했습니다."
                    )
                )


                st.rerun()


            except Exception as e:

                st.error(
                    (
                        "납입 기록 중 오류가 "
                        f"발생했습니다: {e}"
                    )
                )


# ==================================================
# 납입 내역
# ==================================================

st.markdown(
    "#### 📋 납입 내역"
)


payments = (
    get_savings_payments(
        asset_id
    )
    or []
)


if not payments:

    st.caption(
        "아직 기록된 납입 내역이 없습니다."
    )


else:

    payment_rows = []


    for payment in payments:

        payment_rows.append({
            "납입일":
                payment.get(
                    "payment_date"
                ),

            "납입금액":
                float(
                    payment.get(
                        "amount"
                    )
                    or 0
                ),

            "자산반영":
                (
                    "반영됨"
                    if bool(
                        payment.get(
                            "affects_asset_transfer",
                            False,
                        )
                    )
                    else "기존기록"
                ),

            "메모":
                payment.get(
                    "memo"
                )
                or "",
        })


    payment_df = (
        pd.DataFrame(
            payment_rows
        )
    )


    st.dataframe(
        payment_df,
        width="stretch",
        hide_index=True,
        column_config={
            "납입금액":
                st.column_config.NumberColumn(
                    "납입금액",
                    format="₩%,.0f",
                ),
        },
    )


    # ==================================================
    # 잘못 입력한 납입 삭제
    # ==================================================

    with st.expander(
        "🗑️ 납입내역 삭제",
        expanded=False,
    ):

        payment_options = {}


        for payment in payments:

            label = (
                f'{payment["payment_date"]}'
                f' · '
                f'₩{float(payment["amount"]):,.0f}'
            )


            if payment.get(
                "memo"
            ):

                label += (
                    f' · {payment["memo"]}'
                )


            payment_options[
                label
            ] = payment


        selected_payment_label = (
            st.selectbox(
                "삭제할 납입내역",
                list(
                    payment_options.keys()
                ),
                key=(
                    f"delete_savings_payment_"
                    f"{asset_id}"
                ),
            )
        )


        selected_payment = (
            payment_options[
                selected_payment_label
            ]
        )


        selected_affects_transfer = bool(
            selected_payment.get(
                "affects_asset_transfer",
                False,
            )
        )


        if selected_affects_transfer:

            st.warning(
                (
                    "이 납입은 자산 이동이 반영된 기록입니다. "
                    "삭제하면 적금잔액이 해당 금액만큼 감소하고 "
                    "가용자산으로 같은 금액이 돌아갑니다."
                )
            )

        else:

            st.info(
                (
                    "이 납입은 전환 이전의 기존 기록입니다. "
                    "삭제해도 현재 가용자산과 적금잔액은 변경하지 않습니다."
                )
            )


        confirm_delete_payment = (
            st.checkbox(
                "삭제 내용을 확인했습니다.",
                key=(
                    f"confirm_delete_payment_"
                    f"{asset_id}_"
                    f'{selected_payment["id"]}'
                ),
            )
        )


        if st.button(
            "납입내역 삭제",
            type="secondary",
            disabled=(
                not confirm_delete_payment
            ),
            key=(
                f"delete_payment_button_"
                f'{selected_payment["id"]}'
            ),
        ):

            try:

                delete_savings_payment(
                    selected_payment[
                        "id"
                    ]
                )


                st.success(
                    "납입내역을 삭제했습니다."
                )


                st.rerun()


            except Exception as e:

                st.error(
                    (
                        "삭제 중 오류가 "
                        f"발생했습니다: {e}"
                    )
                )

# ==================================================
# 적금 전체 목록
# ==================================================

st.divider()

st.subheader(
    "📋 전체 적금"
)


rows = []


for asset in savings_assets:

    savings_detail = (
        get_savings_detail(
            asset[
                "id"
            ]
        )
        or {}
    )


    maturity = (
        parse_date(
            savings_detail.get(
                "maturity_date"
            )
        )
    )


    remaining = None


    if maturity:

        remaining = (
            maturity
            - datetime.date.today()
        ).days


    rows.append({
        "적금명":
            asset.get(
                "name"
            ),

        "소유자":
            asset.get(
                "owner"
            ),

        "현재잔액":
            float(
                asset.get(
                    "current_value"
                )
                or 0
            ),

        "월납입":
            float(
                savings_detail.get(
                    "monthly_payment"
                )
                or 0
            ),

        "금리":
            (
                f'{float(savings_detail.get("interest_rate") or 0):.2f}%'
            ),

        "가입일":
            savings_detail.get(
                "start_date"
            )
            or "-",

        "만기일":
            savings_detail.get(
                "maturity_date"
            )
            or "-",

        "만기까지":
            (
                f"D-{remaining}"
                if (
                    remaining is not None
                    and remaining >= 0
                )
                else "-"
            ),
    })


df = pd.DataFrame(
    rows
)


st.dataframe(
    df,
    width="stretch",
    hide_index=True,
    column_config={
        "현재잔액":
            st.column_config.NumberColumn(
                "현재잔액",
                format="₩%,.0f",
            ),

        "월납입":
            st.column_config.NumberColumn(
                "월납입",
                format="₩%,.0f",
            ),
    },
)