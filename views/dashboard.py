import streamlit as st
from datetime import date
import pandas as pd
import plotly.express as px

from services.database import (
    get_assets,
    get_debts,
    get_transactions,
    get_net_worth_history,
    add_net_worth_snapshot,
    delete_net_worth_snapshot,
)

st.title("📊 우리집 자산 현황")


# =========================
# 1. 자산 / 부채 / 순자산
# =========================

assets = get_assets()
debts = get_debts()

total_assets = sum(
    float(asset["current_value"])
    for asset in assets
)

total_debts = sum(
    float(debt["balance"])
    for debt in debts
)

net_worth = total_assets - total_debts

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


# =========================
# 2. 이번 달 수입 / 지출
# =========================

transactions = get_transactions()

today = date.today()
current_year = today.year
current_month = today.month

monthly_income = 0
monthly_expense = 0

for transaction in transactions:
    transaction_date = date.fromisoformat(
        transaction["transaction_date"]
    )

    if (
        transaction_date.year == current_year
        and transaction_date.month == current_month
    ):
        amount = float(transaction["amount"])

        if transaction["transaction_type"] == "수입":
            monthly_income += amount

        elif transaction["transaction_type"] == "지출":
            monthly_expense += amount


monthly_savings = (
    monthly_income - monthly_expense
)

if monthly_income > 0:
    savings_rate = (
        monthly_savings / monthly_income
    ) * 100
else:
    savings_rate = 0


st.divider()

st.subheader(
    f"📅 {current_year}년 {current_month}월 현황"
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "이번 달 수입",
        f"₩{int(monthly_income):,}",
    )

with col2:
    st.metric(
        "이번 달 지출",
        f"₩{int(monthly_expense):,}",
    )

with col3:
    st.metric(
        "이번 달 저축",
        f"₩{int(monthly_savings):,}",
    )

with col4:
    st.metric(
        "저축률",
        f"{savings_rate:.1f}%",
    )


# =========================
# 3. 자산 현황 기록
# =========================

st.divider()

st.subheader("📸 자산 현황 기록")

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
        f"{snapshot_date} 자산 현황을 저장했습니다."
    )

    st.rerun()


# 저장된 자산 현황 조회
history = get_net_worth_history()


# =========================
# 4. 저장된 자산 현황 표
# =========================

st.divider()

st.subheader("📋 저장된 자산 현황")

if history:

    history_table_df = pd.DataFrame(
        history
    )

    history_table_df["record_date"] = (
        pd.to_datetime(
            history_table_df["record_date"]
        )
    )

    history_table_df["total_assets"] = (
        history_table_df[
            "total_assets"
        ].astype(float)
    )

    history_table_df["total_debts"] = (
        history_table_df[
            "total_debts"
        ].astype(float)
    )

    history_table_df["net_worth"] = (
        history_table_df[
            "net_worth"
        ].astype(float)
    )

    history_table_df = (
        history_table_df.sort_values(
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
                "record_date": "기록 날짜",
                "total_assets": "총 자산",
                "total_debts": "총 부채",
                "net_worth": "순자산",
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


    # =====================
    # 기록 삭제
    # =====================

    st.subheader("🗑 기록 삭제")

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
            "삭제할 기록을 선택하세요.",
            options=list(
                history_options.keys()
            ),
            key="delete_history_select",
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
            key="delete_history_button",
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
                key="confirm_history_delete",
                use_container_width=True,
            ):

                delete_net_worth_snapshot(
                    selected_history_id
                )

                st.session_state[
                    "history_delete_confirm"
                ] = False

                st.success(
                    "자산 현황 기록을 "
                    "삭제했습니다."
                )

                st.rerun()


        with col2:

            if st.button(
                "취소",
                key="cancel_history_delete",
                use_container_width=True,
            ):

                st.session_state[
                    "history_delete_confirm"
                ] = False

                st.rerun()


else:

    st.info(
        "아직 저장된 자산 현황 "
        "기록이 없습니다."
    )


# =========================
# 5. 자산 변화 그래프
# =========================

st.divider()

st.subheader("📈 자산 변화")

if history:

    history_df = pd.DataFrame(
        history
    )

    history_df["record_date"] = (
        pd.to_datetime(
            history_df["record_date"]
        )
    )

    history_df["total_assets"] = (
        history_df[
            "total_assets"
        ].astype(float)
    )

    history_df["total_debts"] = (
        history_df[
            "total_debts"
        ].astype(float)
    )

    history_df["net_worth"] = (
        history_df[
            "net_worth"
        ].astype(float)
    )


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
            "자산 / 부채 / "
            "순자산 변화"
        ),
    )

    fig_net_worth.update_layout(
        yaxis_tickformat=","
    )

    st.plotly_chart(
        fig_net_worth,
        width="stretch",
        key="net_worth_history_chart",
    )


else:

    st.info(
        "자산 변화 그래프를 표시하려면 "
        "먼저 자산 현황을 저장해주세요."
    )


# =========================
# 6. 소비 분석
# =========================

st.divider()

st.subheader("📊 소비 분석")

if transactions:

    df = pd.DataFrame(
        transactions
    )

    df["amount"] = (
        df["amount"].astype(float)
    )

    df["transaction_date"] = (
        pd.to_datetime(
            df["transaction_date"]
        )
    )

    df["year"] = (
        df["transaction_date"].dt.year
    )

    df["month"] = (
        df["transaction_date"].dt.month
    )

    df["year_month"] = (
        df["transaction_date"]
        .dt.to_period("M")
        .astype(str)
    )


    current_month_df = df[
        (df["year"] == current_year)
        &
        (df["month"] == current_month)
    ]


    expense_df = current_month_df[
        current_month_df[
            "transaction_type"
        ] == "지출"
    ]


    if not expense_df.empty:

        category_expense = (
            expense_df.groupby(
                "category",
                as_index=False,
            )["amount"].sum()
        )

        fig_category = px.pie(
            category_expense,
            names="category",
            values="amount",
            title=(
                "이번 달 "
                "카테고리별 지출"
            ),
            hole=0.4,
        )

        st.plotly_chart(
            fig_category,
            width="stretch",
            key="category_expense_chart",
        )


    else:

        st.info(
            "이번 달 지출 데이터가 없습니다."
        )


    monthly_summary = (
        df.groupby(
            [
                "year_month",
                "transaction_type",
            ],
            as_index=False,
        )["amount"].sum()
    )


    fig_monthly = px.bar(
        monthly_summary,
        x="year_month",
        y="amount",
        color="transaction_type",
        barmode="group",
        title="월별 수입 / 지출",
        labels={
            "year_month": "월",
            "amount": "금액",
            "transaction_type": "구분",
        },
    )


    st.plotly_chart(
        fig_monthly,
        width="stretch",
        key="monthly_income_expense_chart",
    )


else:

    st.info(
        "차트를 표시할 거래 데이터가 "
        "없습니다."
    )


# =========================
# 7. 자산 구성
# =========================

st.divider()

st.subheader("💰 자산 구성")

if assets:

    asset_df = pd.DataFrame(
        assets
    )

    asset_df["current_value"] = (
        asset_df[
            "current_value"
        ].astype(float)
    )


    asset_summary = (
        asset_df.groupby(
            "asset_type",
            as_index=False,
        )["current_value"].sum()
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


    st.subheader("👫 소유자별 자산")


    owner_summary = (
        asset_df.groupby(
            "owner",
            as_index=False,
        )["current_value"].sum()
    )


    fig_owner = px.bar(
        owner_summary,
        x="owner",
        y="current_value",
        title="소유자별 자산",
        labels={
            "owner": "소유자",
            "current_value": "자산",
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