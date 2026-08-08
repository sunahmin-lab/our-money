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
# 1. 카드 관리
# ==================================================

st.subheader("💳 카드 관리")


show_help(
    "카드는 왜 등록하나요?",
    (
        "카드를 등록하면 거래내역에서 어떤 카드로 결제했는지 "
        "기록할 수 있고, 대시보드에서 카드별 예상 청구액을 "
        "계산할 수 있습니다."
    ),
    example=(
        "예: 신한카드 결제일 12일 → "
        "전월 1일~말일 사용액을 이번 달 청구액으로 계산"
    ),
)


# ==================================================
# 카드 추가
# ==================================================

with st.form(
    "add_card_form",
    clear_on_submit=True,
):

    card_name = st.text_input(
        "카드명",
        placeholder="예: 신한카드",
    )

    card_owner = st.selectbox(
        "소유자",
        [
            "나",
            "남편",
            "공동",
        ],
    )

    payment_day = st.number_input(
        "결제일",
        min_value=1,
        max_value=31,
        value=12,
        step=1,
    )

    card_submit = (
        st.form_submit_button(
            "카드 추가",
            use_container_width=True,
        )
    )


if card_submit:

    if not card_name.strip():

        st.error(
            "카드명을 입력해주세요."
        )

    else:

        try:

            add_card(
                name=card_name,
                owner=card_owner,
                payment_day=payment_day,
            )

            st.success(
                "카드를 추가했습니다."
            )

            st.rerun()

        except Exception:

            st.error(
                "카드를 추가하지 못했습니다. "
                "같은 이름의 카드가 이미 있는지 확인해주세요."
            )


# ==================================================
# 카드 목록
# ==================================================

cards = get_cards()


if cards:

    st.markdown("#### 등록된 카드")


    for card in cards:

        with st.expander(
            (
                f'💳 {card["name"]} '
                f'· {card["owner"]} '
                f'· {card["payment_day"]}일'
            )
        ):

            with st.form(
                f'edit_card_form_{card["id"]}'
            ):

                edit_name = st.text_input(
                    "카드명",
                    value=card["name"],
                )

                owners = [
                    "나",
                    "남편",
                    "공동",
                ]

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
                            card[
                                "payment_day"
                            ]
                        ),
                        step=1,
                    )
                )


                card_update_submit = (
                    st.form_submit_button(
                        "수정 저장",
                        use_container_width=True,
                    )
                )


            if card_update_submit:

                update_card(
                    card_id=card["id"],
                    name=edit_name,
                    owner=edit_owner,
                    payment_day=(
                        edit_payment_day
                    ),
                )

                st.success(
                    "카드 정보를 수정했습니다."
                )

                st.rerun()


            if st.button(
                "카드 삭제",
                key=(
                    f'delete_card_'
                    f'{card["id"]}'
                ),
            ):

                delete_card(
                    card["id"]
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


# ==================================================
# 대분류 조회
# ==================================================

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


# ==================================================
# 대분류 추가
# ==================================================

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


# ==================================================
# 대분류 선택
# ==================================================

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


    # ==================================================
    # 소분류
    # ==================================================

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


    # ==================================================
    # 소분류 추가
    # ==================================================

    with st.form(
        "add_subcategory_form",
        clear_on_submit=True,
    ):

        new_subcategory = (
            st.text_input(
                "새 소분류",
                placeholder=(
                    "예: 식비"
                ),
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


    # ==================================================
    # 대분류 삭제
    # ==================================================

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
    "용돈은 왜 일반 지출과 따로 관리하나요?",
    (
        "우리 집에서는 두 사람의 월급을 공동 생활통장으로 합친 뒤 "
        "각자의 용돈을 먼저 배정합니다. "
        "따라서 용돈은 생활비나 고정비와 같은 공동 소비 지출과 "
        "분리해서 관리합니다."
    ),
    example=(
        "예: 총 월급 7,000,000원에서 "
        "내 용돈 400,000원 + 남편 용돈 400,000원을 "
        "먼저 배정"
    ),
)


show_help(
    "용돈은 총 자산에서 빠지나요?",
    (
        "용돈 금액 자체를 총 자산에서 자동으로 빼지는 않습니다. "
        "총 자산은 실제 계좌와 예금, 투자자산 등의 현재 잔액을 "
        "기준으로 계산합니다. "
        "용돈은 이번 달 공동생활에 사용할 수 있는 돈을 계산할 때 "
        "선배정 금액으로 차감합니다."
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


with st.form(
    "household_settings_form"
):

    my_allowance = (
        st.number_input(
            "내 월 용돈",
            min_value=0,
            value=(
                current_my_allowance
            ),
            step=10000,
        )
    )


    spouse_allowance = (
        st.number_input(
            "남편 월 용돈",
            min_value=0,
            value=(
                current_spouse_allowance
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
        my_allowance=(
            my_allowance
        ),
        spouse_allowance=(
            spouse_allowance
        ),
    )

    st.success(
        "가계 운영 설정을 저장했습니다."
    )

    st.rerun()