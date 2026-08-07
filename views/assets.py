import streamlit as st
import pandas as pd

from services.database import (
    get_assets,
    add_asset,
    update_asset,
    delete_asset,
)

# -------------------------
# 자산 입력
# -------------------------

st.subheader("➕ 자산 추가")

with st.form("asset_form"):

    asset_type = st.selectbox(
        "자산 종류",
        [
            "현금",
            "예금",
            "적금",
            "주식",
            "ETF",
            "부동산",
            "자동차",
            "기타",
        ],
    )

    name = st.text_input("자산명")

    owner = st.selectbox(
        "소유자",
        [
            "나",
            "남편",
            "공동",
        ],
    )

    current_value = st.number_input(
        "현재 가치",
        min_value=0,
        step=10000,
    )

    memo = st.text_input("메모")

    submitted = st.form_submit_button("저장")

    if submitted:

        if not name:
            st.error("자산명을 입력해주세요.")

        else:
            add_asset(
                name=name,
                asset_type=asset_type,
                owner=owner,
                current_value=current_value,
                memo=memo,
            )

            st.success("저장되었습니다!")
            st.rerun()


# -------------------------
# 자산 목록
# -------------------------

st.divider()
st.subheader("💰 현재 자산")

assets = get_assets()

if not assets:
    st.info("아직 등록된 자산이 없습니다.")

else:
    total_assets = sum(
        float(asset["current_value"])
        for asset in assets
    )

    st.metric(
        "총 자산",
        f"₩{int(total_assets):,}",
    )

    df = pd.DataFrame(assets)

    display_df = df[
        [
            "asset_type",
            "name",
            "owner",
            "current_value",
            "memo",
        ]
    ].copy()

    display_df = display_df.rename(
        columns={
            "asset_type": "자산 종류",
            "name": "자산명",
            "owner": "소유자",
            "current_value": "현재 가치",
            "memo": "메모",
        }
    )

    display_df["현재 가치"] = display_df["현재 가치"].astype(float)

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        column_config={
            "현재 가치": st.column_config.NumberColumn(
                "현재 가치",
                format="₩ %d",
            ),
        },
    )


# -------------------------
# 자산 수정 / 삭제
# -------------------------

st.divider()
st.subheader("✏️ 자산 수정 / 삭제")

assets = get_assets()

if assets:
    asset_map = {
        f'{asset["name"]} / {asset["owner"]} / {int(float(asset["current_value"])):,}원': asset
        for asset in assets
    }

    selected_label = st.selectbox(
        "수정할 자산 선택",
        list(asset_map.keys()),
    )

    selected_asset = asset_map[selected_label]

    with st.form("edit_asset_form"):
        edit_name = st.text_input(
            "자산명",
            value=selected_asset["name"],
        )

        asset_types = [
            "현금",
            "예금",
            "적금",
            "주식",
            "ETF",
            "부동산",
            "자동차",
            "기타",
        ]

        current_asset_type = selected_asset["asset_type"]

        edit_asset_type = st.selectbox(
            "자산 종류",
            asset_types,
            index=asset_types.index(current_asset_type)
            if current_asset_type in asset_types
            else 0,
        )

        owners = ["나", "남편", "공동"]

        current_owner = selected_asset["owner"]

        edit_owner = st.selectbox(
            "소유자",
            owners,
            index=owners.index(current_owner)
            if current_owner in owners
            else 0,
        )

        edit_current_value = st.number_input(
            "현재 가치",
            min_value=0,
            value=int(float(selected_asset["current_value"])),
            step=10000,
        )

        edit_memo = st.text_input(
            "메모",
            value=selected_asset["memo"] or "",
        )

        update_submitted = st.form_submit_button("수정 저장")

        if update_submitted:
            update_asset(
                asset_id=selected_asset["id"],
                name=edit_name,
                asset_type=edit_asset_type,
                owner=edit_owner,
                current_value=edit_current_value,
                memo=edit_memo,
            )

            st.success("수정되었습니다.")
            st.rerun()

    if "delete_confirm" not in st.session_state:
        st.session_state.delete_confirm = False

    if not st.session_state.delete_confirm:

        if st.button("🗑️ 선택한 자산 삭제"):
            st.session_state.delete_confirm = True
            st.rerun()

    else:
        st.warning(
            f'정말 "{selected_asset["name"]}" 자산을 삭제하시겠습니까?'
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "예, 삭제합니다",
                type="primary",
                use_container_width=True,
            ):
                delete_asset(selected_asset["id"])

                st.session_state.delete_confirm = False

                st.success("삭제되었습니다.")
                st.rerun()

        with col2:
            if st.button(
                "아니오, 취소",
                use_container_width=True,
            ):
                st.session_state.delete_confirm = False
                st.rerun()

else:
    st.info("수정하거나 삭제할 자산이 없습니다.")

