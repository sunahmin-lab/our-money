import streamlit as st

from services.database import (
    # 카드
    get_cards,
    add_card,
    update_card,
    delete_card,

    # 카테고리
    get_main_categories,
    get_subcategories,
    add_category,
    delete_category,
    ensure_default_categories,

    # 가계 운영 설정
    get_household_settings,
    save_household_settings,
)

from utils.helpers import show_help


st.title("⚙️ 설정")


# ==================================================
# 기본 카테고리 준비
# ==================================================

ensure_default_categories()


# ==================================================
# 공통 옵션
# ==================================================

owners = [
    "나",
    "남편",
    "공동",
]

month_offset_options = {
    "전월": -1,
    "당월": 0,
}

month_offset_labels = {
    -1: "전월",
    0: "당월",
}


# ==================================================
# 1. 카드 관리
# ==================================================

st.subheader("💳 카드 관리")


show_help(
    "카드의 청구기간은 왜 등록하나요?",
    (
        "카드마다 결제일에 청구되는 사용기간이 다를 수 있습니다. "
        "그래서 결제일뿐 아니라 해당 결제일에 어떤 기간의 카드 사용액이 "
        "청구되는지도 카드별로 저장합니다."
    ),
    example=(
        "예: 결제일 12일 / 전월 1일~전월 말일"
    ),
)


show_help(
    "월 실적은 어떻게 계산하나요?",
    (
        "월 실적 목표를 등록하면 이번 달 1일부터 말일까지 "
        "해당 카드로 사용한 실적 인정 거래를 합산해서 "
        "얼마나 채웠는지 계산합니다."
    ),
    warning=(
        "카드사에 따라 세금, 상품권, 관리비 등 일부 결제는 "
        "실적에서 제외될 수 있으므로 거래 입력 시 "
        "'카드 실적에 포함' 여부를 직접 선택하게 됩니다."
    ),
)


# ==================================================
# 카드 추가
# ==================================================

st.markdown("#### ➕ 카드 추가")


new_card_name = st.text_input(
    "카드명",
    placeholder="예: 신한카드 BEST-F",
    key="new_card_name",
)


new_card_owner = st.selectbox(
    "소유자",
    owners,
    key="new_card_owner",
)


new_payment_day = st.number_input(
    "결제일",
    min_value=1,
    max_value=31,
    value=12,
    step=1,
    key="new_card_payment_day",
)


st.markdown("##### 청구 대상 사용기간")


col1, col2 = st.columns(2)


with col1:

    new_start_month_label = st.selectbox(
        "시작 월",
        list(month_offset_options.keys()),
        index=0,
        key="new_card_start_month",
    )


with col2:

    new_start_day_type = st.selectbox(
        "시작 일",
        [
            "1일",
            "2일",
            "3일",
            "4일",
            "5일",
            "6일",
            "7일",
            "8일",
            "9일",
            "10일",
            "11일",
            "12일",
            "13일",
            "14일",
            "15일",
            "16일",
            "17일",
            "18일",
            "19일",
            "20일",
            "21일",
            "22일",
            "23일",
            "24일",
            "25일",
            "26일",
            "27일",
            "28일",
            "29일",
            "30일",
            "31일",
            "말일",
        ],
        index=0,
        key="new_card_start_day",
    )


col1, col2 = st.columns(2)


with col1:

    new_end_month_label = st.selectbox(
        "종료 월",
        list(month_offset_options.keys()),
        index=0,
        key="new_card_end_month",
    )


with col2:

    new_end_day_type = st.selectbox(
        "종료 일",
        [
            "1일",
            "2일",
            "3일",
            "4일",
            "5일",
            "6일",
            "7일",
            "8일",
            "9일",
            "10일",
            "11일",
            "12일",
            "13일",
            "14일",
            "15일",
            "16일",
            "17일",
            "18일",
            "19일",
            "20일",
            "21일",
            "22일",
            "23일",
            "24일",
            "25일",
            "26일",
            "27일",
            "28일",
            "29일",
            "30일",
            "31일",
            "말일",
        ],
        index=31,
        key="new_card_end_day",
    )


new_monthly_performance = st.number_input(
    "월 실적 목표",
    min_value=0,
    value=300000,
    step=10000,
    key="new_card_monthly_performance",
)


if st.button(
    "카드 추가",
    use_container_width=True,
    key="add_card_button",
):

    if not new_card_name.strip():

        st.error(
            "카드명을 입력해주세요."
        )

    else:

        start_is_month_end = (
            new_start_day_type
            == "말일"
        )

        end_is_month_end = (
            new_end_day_type
            == "말일"
        )

        start_day = (
            None
            if start_is_month_end
            else int(
                new_start_day_type.replace(
                    "일",
                    "",
                )
            )
        )

        end_day = (
            None
            if end_is_month_end
            else int(
                new_end_day_type.replace(
                    "일",
                    "",
                )
            )
        )

        start_offset = (
            month_offset_options[
                new_start_month_label
            ]
        )

        end_offset = (
            month_offset_options[
                new_end_month_label
            ]
        )


        # ==================================================
        # 청구기간 유효성 검사
        # ==================================================

        invalid_period = False

        if start_offset > end_offset:
            invalid_period = True

        elif start_offset == end_offset:

            start_compare_day = (
                32
                if start_is_month_end
                else start_day
            )

            end_compare_day = (
                32
                if end_is_month_end
                else end_day
            )

            if (
                start_compare_day
                > end_compare_day
            ):
                invalid_period = True


        if invalid_period:

            st.error(
                "청구 대상 사용기간이 올바르지 않습니다. "
                "종료일은 시작일보다 같거나 뒤여야 합니다."
            )

        else:

            try:

                add_card(
                    name=new_card_name,
                    owner=new_card_owner,
                    payment_day=new_payment_day,
                    billing_start_month_offset=(
                        start_offset
                    ),
                    billing_start_day=(
                        start_day
                    ),
                    billing_start_is_month_end=(
                        start_is_month_end
                    ),
                    billing_end_month_offset=(
                        end_offset
                    ),
                    billing_end_day=(
                        end_day
                    ),
                    billing_end_is_month_end=(
                        end_is_month_end
                    ),
                    monthly_performance=(
                        new_monthly_performance
                    ),
                )

                st.success(
                    "카드를 추가했습니다."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"카드를 추가하지 못했습니다: {e}"
                )


# ==================================================
# 카드 목록 / 수정
# ==================================================

cards = get_cards()


if cards:

    st.divider()

    st.markdown("#### 등록된 카드")


    for card in cards:

        card_id = card["id"]

        title = (
            f'💳 {card["name"]} · '
            f'{card["owner"]}'
        )


        with st.expander(title):

            current_start_offset = int(
                card.get(
                    "billing_start_month_offset",
                    -1,
                )
                or -1
            )


            current_end_offset = int(
                card.get(
                    "billing_end_month_offset",
                    -1,
                )
                or -1
            )


            current_start_is_end = bool(
                card.get(
                    "billing_start_is_month_end",
                    False,
                )
            )


            current_end_is_end = bool(
                card.get(
                    "billing_end_is_month_end",
                    True,
                )
            )


            current_start_day = card.get(
                "billing_start_day"
            )


            current_end_day = card.get(
                "billing_end_day"
            )


            st.caption(
                (
                    f'결제일: 매월 '
                    f'{card["payment_day"]}일'
                )
            )


            if current_start_is_end:

                start_text = (
                    f"{month_offset_labels.get(current_start_offset, '전월')} 말일"
                )

            else:

                start_text = (
                    f"{month_offset_labels.get(current_start_offset, '전월')} "
                    f"{current_start_day or 1}일"
                )


            if current_end_is_end:

                end_text = (
                    f"{month_offset_labels.get(current_end_offset, '전월')} 말일"
                )

            else:

                end_text = (
                    f"{month_offset_labels.get(current_end_offset, '전월')} "
                    f"{current_end_day or 1}일"
                )


            st.caption(
                f"청구 대상: {start_text} ~ {end_text}"
            )


            st.caption(
                "월 실적 목표: "
                f'₩{int(float(card.get("monthly_performance", 0) or 0)):,}'
            )


            with st.form(
                f"edit_card_form_{card_id}"
            ):

                edit_name = st.text_input(
                    "카드명",
                    value=card["name"],
                )


                try:

                    owner_index = (
                        owners.index(
                            card["owner"]
                        )
                    )

                except ValueError:

                    owner_index = 0


                edit_owner = st.selectbox(
                    "소유자",
                    owners,
                    index=owner_index,
                )


                edit_payment_day = (
                    st.number_input(
                        "결제일",
                        min_value=1,
                        max_value=31,
                        value=int(
                            card["payment_day"]
                        ),
                        step=1,
                    )
                )


                st.markdown(
                    "##### 청구 대상 사용기간"
                )


                offset_keys = list(
                    month_offset_options.keys()
                )


                try:

                    start_month_index = (
                        offset_keys.index(
                            month_offset_labels[
                                current_start_offset
                            ]
                        )
                    )

                except Exception:

                    start_month_index = 0


                try:

                    end_month_index = (
                        offset_keys.index(
                            month_offset_labels[
                                current_end_offset
                            ]
                        )
                    )

                except Exception:

                    end_month_index = 0


                col1, col2 = (
                    st.columns(2)
                )


                with col1:

                    edit_start_month_label = (
                        st.selectbox(
                            "시작 월",
                            offset_keys,
                            index=start_month_index,
                        )
                    )


                day_options = [
                    *[
                        f"{day}일"
                        for day
                        in range(1, 32)
                    ],
                    "말일",
                ]


                if current_start_is_end:

                    start_day_index = 31

                else:

                    start_day_value = int(
                        current_start_day or 1
                    )

                    start_day_index = (
                        start_day_value - 1
                    )


                with col2:

                    edit_start_day_type = (
                        st.selectbox(
                            "시작 일",
                            day_options,
                            index=start_day_index,
                        )
                    )


                col1, col2 = (
                    st.columns(2)
                )


                with col1:

                    edit_end_month_label = (
                        st.selectbox(
                            "종료 월",
                            offset_keys,
                            index=end_month_index,
                        )
                    )


                if current_end_is_end:

                    end_day_index = 31

                else:

                    end_day_value = int(
                        current_end_day or 1
                    )

                    end_day_index = (
                        end_day_value - 1
                    )


                with col2:

                    edit_end_day_type = (
                        st.selectbox(
                            "종료 일",
                            day_options,
                            index=end_day_index,
                        )
                    )


                edit_monthly_performance = (
                    st.number_input(
                        "월 실적 목표",
                        min_value=0,
                        value=int(
                            float(
                                card.get(
                                    "monthly_performance",
                                    0,
                                )
                                or 0
                            )
                        ),
                        step=10000,
                    )
                )


                card_update_submit = (
                    st.form_submit_button(
                        "수정 저장",
                        use_container_width=True,
                    )
                )


            if card_update_submit:
                start_is_month_end = (
                    edit_start_day_type
                    == "말일"
                )

                end_is_month_end = (
                    edit_end_day_type
                    == "말일"
                )

                start_day = (
                    None
                    if start_is_month_end
                    else int(
                        edit_start_day_type.replace(
                            "일",
                            "",
                        )
                    )
                )

                end_day = (
                    None
                    if end_is_month_end
                    else int(
                        edit_end_day_type.replace(
                            "일",
                            "",
                        )
                    )
                )

                start_offset = (
                    month_offset_options[
                        edit_start_month_label
                    ]
                )

                end_offset = (
                    month_offset_options[
                        edit_end_month_label
                    ]
                )


                invalid_period = False

                if start_offset > end_offset:
                    invalid_period = True

                elif start_offset == end_offset:

                    start_compare_day = (
                        32
                        if start_is_month_end
                        else start_day
                    )

                    end_compare_day = (
                        32
                        if end_is_month_end
                        else end_day
                    )

                    if (
                        start_compare_day
                        > end_compare_day
                    ):
                        invalid_period = True


                if invalid_period:

                    st.error(
                        "청구 대상 사용기간이 올바르지 않습니다. "
                        "종료일은 시작일보다 같거나 뒤여야 합니다."
                    )

                else:

                    update_card(
                        card_id=card_id,
                        name=edit_name,
                        owner=edit_owner,
                        payment_day=edit_payment_day,
                        billing_start_month_offset=(
                            start_offset
                        ),
                        billing_start_day=(
                            start_day
                        ),
                        billing_start_is_month_end=(
                            start_is_month_end
                        ),
                        billing_end_month_offset=(
                            end_offset
                        ),
                        billing_end_day=(
                            end_day
                        ),
                        billing_end_is_month_end=(
                            end_is_month_end
                        ),
                        monthly_performance=(
                            edit_monthly_performance
                        ),
                    )

                    st.success(
                        "카드 정보를 수정했습니다."
                    )

                    st.rerun()


            if st.button(
                "카드 삭제",
                key=(
                    f"delete_card_{card_id}"
                ),
            ):

                delete_card(
                    card_id
                )

                st.success(
                    "카드를 삭제했습니다."
                )

                st.rerun()


else:

    st.info(
        "등록된 카드가 없습니다."
    )


# ==================================================
# 2. 카테고리 관리
# ==================================================

st.divider()

st.subheader(
    "🏷️ 카테고리 관리"
)


show_help(
    "대분류와 소분류는 어떻게 나누나요?",
    (
        "대분류는 큰 지출 영역이고, "
        "소분류는 그 안의 세부 지출 항목입니다."
    ),
    example=(
        "예: 생활비 → 식비 / 생필품 / 외식 / 카페"
    ),
)


category_transaction_type = (
    st.radio(
        "카테고리 종류",
        [
            "지출",
            "수입",
        ],
        horizontal=True,
        key="settings_category_type",
    )
)


main_categories = (
    get_main_categories(
        category_transaction_type
    )
)


st.markdown(
    "#### 대분류"
)


if main_categories:

    for category in main_categories:

        st.write(
            f'• {category["name"]}'
        )

else:

    st.info(
        "등록된 대분류가 없습니다."
    )


with st.form(
    "add_main_category_form",
    clear_on_submit=True,
):

    new_main_category = (
        st.text_input(
            "새 대분류",
            placeholder="예: 생활비",
        )
    )

    add_main_submit = (
        st.form_submit_button(
            "대분류 추가",
            use_container_width=True,
        )
    )


if add_main_submit:

    if not new_main_category.strip():

        st.error(
            "대분류명을 입력해주세요."
        )

    else:

        try:

            add_category(
                transaction_type=(
                    category_transaction_type
                ),
                name=new_main_category,
                parent_id=None,
            )

            st.success(
                "대분류를 추가했습니다."
            )

            st.rerun()

        except Exception:

            st.error(
                "같은 이름의 카테고리가 "
                "이미 등록되어 있을 수 있습니다."
            )


main_categories = (
    get_main_categories(
        category_transaction_type
    )
)


if main_categories:

    main_category_options = {
        category["name"]:
            category

        for category
        in main_categories
    }


    selected_main_name = (
        st.selectbox(
            "소분류를 관리할 대분류",
            list(
                main_category_options.keys()
            ),
            key=(
                "settings_main_category_select"
            ),
        )
    )


    selected_main = (
        main_category_options[
            selected_main_name
        ]
    )


    selected_main_id = (
        selected_main["id"]
    )


    st.markdown(
        f"#### {selected_main_name} 소분류"
    )


    subcategories = (
        get_subcategories(
            selected_main_id
        )
    )


    if subcategories:

        for subcategory in subcategories:

            col1, col2 = st.columns(
                [4, 1]
            )

            with col1:

                st.write(
                    f'• '
                    f'{subcategory["name"]}'
                )

            with col2:

                if st.button(
                    "삭제",
                    key=(
                        f'delete_subcategory_'
                        f'{subcategory["id"]}'
                    ),
                ):

                    delete_category(
                        subcategory["id"]
                    )

                    st.rerun()

    else:

        st.caption(
            "등록된 소분류가 없습니다."
        )


    with st.form(
        "add_subcategory_form",
        clear_on_submit=True,
    ):

        new_subcategory = (
            st.text_input(
                "새 소분류",
                placeholder="예: 식비",
            )
        )

        add_subcategory_submit = (
            st.form_submit_button(
                "소분류 추가",
                use_container_width=True,
            )
        )


    if add_subcategory_submit:

        if not new_subcategory.strip():

            st.error(
                "소분류명을 입력해주세요."
            )

        else:

            try:

                add_category(
                    transaction_type=(
                        category_transaction_type
                    ),
                    name=new_subcategory,
                    parent_id=(
                        selected_main_id
                    ),
                )

                st.success(
                    "소분류를 추가했습니다."
                )

                st.rerun()

            except Exception:

                st.error(
                    "같은 이름의 카테고리가 "
                    "이미 등록되어 있을 수 있습니다."
                )


    st.markdown(
        "#### 대분류 삭제"
    )


    st.warning(
        "대분류를 삭제하면 "
        "그 아래 소분류도 함께 삭제됩니다."
    )


    if st.button(
        f"'{selected_main_name}' 삭제",
        key=(
            f'delete_main_category_'
            f'{selected_main_id}'
        ),
    ):

        delete_category(
            selected_main_id
        )

        st.rerun()


# ==================================================
# 3. 가계 운영 설정
# ==================================================

st.divider()

st.subheader(
    "💰 가계 운영 설정"
)


show_help(
    "용돈과 투자금은 어떻게 계산되나요?",
    (
        "월급 등 가계 수입이 들어오면 각자의 용돈과 투자금을 "
        "먼저 배정하고, 여행자금도 따로 적립한 뒤 "
        "남은 돈을 공동생활비로 사용하는 구조입니다."
    ),
    example=(
        "예: 내 투자금 50만원 + 남편 투자금 50만원을 "
        "매달 먼저 배정"
    ),
)


show_help(
    "투자계좌 입금도 지출로 입력해야 하나요?",
    (
        "아니요. 여기 설정하는 월 투자금은 가계 운영자금에서 "
        "얼마를 투자용으로 배정할지 정하는 값입니다. "
        "ISA나 연금저축으로 실제 이체한 금액은 투자 페이지에서 "
        "'입금' 거래로 기록합니다."
    ),
    warning=(
        "투자계좌 입금을 일반 거래내역의 지출로도 입력하면 "
        "가계자금이 이중으로 차감됩니다."
    ),
)


household_settings = (
    get_household_settings()
)


current_my_allowance = int(
    float(
        household_settings.get(
            "my_allowance",
            0,
        )
        or 0
    )
)


current_spouse_allowance = int(
    float(
        household_settings.get(
            "spouse_allowance",
            0,
        )
        or 0
    )
)


current_my_investment_budget = int(
    float(
        household_settings.get(
            "my_investment_budget",
            0,
        )
        or 0
    )
)


current_spouse_investment_budget = int(
    float(
        household_settings.get(
            "spouse_investment_budget",
            0,
        )
        or 0
    )
)


with st.form(
    "household_settings_form"
):

    st.markdown(
        "#### 👛 월 용돈"
    )


    col1, col2 = st.columns(2)


    with col1:

        my_allowance = (
            st.number_input(
                "내 월 용돈",
                min_value=0,
                value=current_my_allowance,
                step=10000,
            )
        )


    with col2:

        spouse_allowance = (
            st.number_input(
                "남편 월 용돈",
                min_value=0,
                value=current_spouse_allowance,
                step=10000,
            )
        )


    st.markdown(
        "#### 📈 월 투자금 배정"
    )


    col1, col2 = st.columns(2)


    with col1:

        my_investment_budget = (
            st.number_input(
                "내 월 투자금",
                min_value=0,
                value=(
                    current_my_investment_budget
                ),
                step=10000,
            )
        )


    with col2:

        spouse_investment_budget = (
            st.number_input(
                "남편 월 투자금",
                min_value=0,
                value=(
                    current_spouse_investment_budget
                ),
                step=10000,
            )
        )


    household_settings_submit = (
        st.form_submit_button(
            "가계 운영 설정 저장",
            use_container_width=True,
        )
    )


if household_settings_submit:

    save_household_settings(
        my_allowance=my_allowance,
        spouse_allowance=spouse_allowance,
        my_investment_budget=(
            my_investment_budget
        ),
        spouse_investment_budget=(
            spouse_investment_budget
        ),
    )

    st.success(
        "가계 운영 설정을 저장했습니다."
    )

    st.rerun()