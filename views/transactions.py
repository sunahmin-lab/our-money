from datetime import date

import pandas as pd
import streamlit as st

from services.database import (
    get_transactions,
    add_transaction,
    update_transaction,
    delete_transaction,
    get_cards,
    get_main_categories,
    get_subcategories,
    ensure_default_categories,
)

from utils.helpers import show_help


st.title("🧾 거래내역")


# ==================================================
# 1. 기본 데이터
# ==================================================

ensure_default_categories()

transactions = get_transactions()
cards = get_cards()


# ==================================================
# 2. 안내
# ==================================================

show_help(
    "여기에는 어떤 거래를 기록하나요?",
    (
        "월급, 상여금 같은 실제 수입과 생활비, 고정비, 경조사비처럼 "
        "공동가계에서 실제로 소비한 지출을 기록합니다."
    ),
    example=(
        "예: 월급 3,500,000원 → 수입 / "
        "마트 장보기 80,000원 → 지출"
    ),
)


show_help(
    "용돈과 여행자금 적립도 여기 입력하나요?",
    (
        "아니요. 내 용돈과 남편 용돈은 설정 메뉴에서 월 배정액으로 관리하고, "
        "여행자금 적립은 목적자금 메뉴에서 기록합니다."
    ),
    warning=(
        "용돈 지급이나 여행자금 적립을 여기서 지출로도 입력하면 "
        "대시보드의 공동지출이 이중 계산됩니다."
    ),
)


# ==================================================
# 3. 거래 추가
# ==================================================

st.subheader("➕ 거래 추가")


transaction_type = st.radio(
    "거래 구분",
    [
        "지출",
        "수입",
    ],
    horizontal=True,
    key="add_transaction_type",
)


# ==================================================
# 카테고리
# ==================================================

main_categories = get_main_categories(
    transaction_type
)


if main_categories:

    main_category_options = {
        category["name"]: category
        for category in main_categories
    }

    selected_main_category_name = (
        st.selectbox(
            "대분류",
            list(
                main_category_options.keys()
            ),
            key="add_main_category",
        )
    )

    selected_main_category = (
        main_category_options[
            selected_main_category_name
        ]
    )

    selected_main_category_id = (
        selected_main_category["id"]
    )

else:

    selected_main_category_name = None
    selected_main_category_id = None

    st.warning(
        "등록된 카테고리가 없습니다. "
        "설정 → 카테고리 관리에서 먼저 추가해주세요."
    )


# ==================================================
# 소분류
# ==================================================

selected_subcategory_name = None


if selected_main_category_id is not None:

    subcategories = get_subcategories(
        selected_main_category_id
    )

    if subcategories:

        subcategory_names = [
            subcategory["name"]
            for subcategory in subcategories
        ]

        selected_subcategory_name = (
            st.selectbox(
                "소분류",
                subcategory_names,
                key="add_subcategory",
            )
        )

    else:

        st.caption(
            "이 대분류에는 소분류가 없습니다."
        )


# ==================================================
# 카드
# ==================================================

payment_method = "기타"
selected_card_id = None


if transaction_type == "지출":

    payment_method = st.radio(
        "결제수단",
        [
            "카드",
            "기타",
        ],
        horizontal=True,
        key="add_payment_method",
    )

    if payment_method == "카드":

        if cards:

            card_options = {
                (
                    f'{card["name"]} · '
                    f'{card["owner"]}'
                ):
                card

                for card in cards
            }

            selected_card_label = (
                st.selectbox(
                    "사용 카드",
                    list(
                        card_options.keys()
                    ),
                    key="add_card_select",
                )
            )

            selected_card = (
                card_options[
                    selected_card_label
                ]
            )

            selected_card_id = (
                selected_card["id"]
            )

        else:

            st.warning(
                "등록된 카드가 없습니다. "
                "설정 → 카드 관리에서 먼저 카드를 추가해주세요."
            )


# ==================================================
# 거래 입력 폼
# ==================================================

with st.form(
    "add_transaction_form",
    clear_on_submit=True,
):

    transaction_date = st.date_input(
        "거래일",
        value=date.today(),
    )

    owner = st.selectbox(
        "사용자",
        [
            "나",
            "남편",
            "공동",
        ],
    )

    amount = st.number_input(
        "금액",
        min_value=0,
        value=0,
        step=10000,
    )

    memo = st.text_input(
        "메모",
        placeholder="예: 이마트 장보기",
    )

    submitted = st.form_submit_button(
        "거래 추가",
        use_container_width=True,
    )


if submitted:

    if selected_main_category_name is None:

        st.error(
            "카테고리를 먼저 선택해주세요."
        )

    elif amount <= 0:

        st.error(
            "금액을 입력해주세요."
        )

    elif (
        transaction_type == "지출"
        and
        payment_method == "카드"
        and
        selected_card_id is None
    ):

        st.error(
            "카드를 선택해주세요."
        )

    else:

        add_transaction(
            transaction_date=transaction_date,
            transaction_type=transaction_type,
            category=selected_main_category_name,
            subcategory=selected_subcategory_name,
            owner=owner,
            amount=amount,
            memo=memo,
            card_id=selected_card_id,
        )

        st.success(
            "거래를 추가했습니다."
        )

        st.rerun()


# ==================================================
# 4. 거래 목록
# ==================================================

st.divider()

st.subheader("📋 거래 목록")


if transactions:

    card_map = {
        int(card["id"]): (
            f'{card["name"]} · '
            f'{card["owner"]}'
        )
        for card in cards
    }


    rows = []


    for transaction in transactions:

        card_name = ""

        card_id = transaction.get(
            "card_id"
        )

        if card_id is not None:

            try:

                card_name = card_map.get(
                    int(card_id),
                    "",
                )

            except (
                TypeError,
                ValueError,
            ):

                card_name = ""


        rows.append({
            "거래일":
                transaction[
                    "transaction_date"
                ],

            "구분":
                transaction[
                    "transaction_type"
                ],

            "대분류":
                transaction[
                    "category"
                ],

            "소분류":
                transaction.get(
                    "subcategory"
                )
                or "",

            "결제수단":
                (
                    card_name
                    if card_name
                    else "기타"
                ),

            "사용자":
                transaction[
                    "owner"
                ],

            "금액":
                float(
                    transaction[
                        "amount"
                    ]
                ),

            "메모":
                transaction.get(
                    "memo"
                )
                or "",
        })


    transaction_df = pd.DataFrame(
        rows
    )


    transaction_df[
        "거래일"
    ] = pd.to_datetime(
        transaction_df[
            "거래일"
        ]
    )


    st.dataframe(
        transaction_df,
        width="stretch",
        hide_index=True,
        column_config={
            "거래일":
                st.column_config.DateColumn(
                    "거래일",
                    format="YYYY-MM-DD",
                ),

            "금액":
                st.column_config.NumberColumn(
                    "금액",
                    format="₩ %d",
                ),
        },
    )


else:

    st.info(
        "등록된 거래가 없습니다."
    )

    st.stop()


# ==================================================
# 5. 거래 수정
# ==================================================

st.divider()

st.subheader("✏️ 거래 수정")


transaction_options = {
    (
        f'{item["transaction_date"]} · '
        f'{item["transaction_type"]} · '
        f'{item["category"]} · '
        f'₩{int(float(item["amount"])):,}'
    ):
    item

    for item in transactions
}


selected_transaction_label = (
    st.selectbox(
        "수정할 거래",
        list(
            transaction_options.keys()
        ),
        key="edit_transaction_select",
    )
)


selected_transaction = (
    transaction_options[
        selected_transaction_label
    ]
)


transaction_id = (
    selected_transaction["id"]
)


# ==================================================
# 수정용 거래 유형
# ==================================================

transaction_types = [
    "지출",
    "수입",
]


try:

    transaction_type_index = (
        transaction_types.index(
            selected_transaction[
                "transaction_type"
            ]
        )
    )

except ValueError:

    transaction_type_index = 0


edit_transaction_type = (
    st.radio(
        "거래 구분",
        transaction_types,
        index=transaction_type_index,
        horizontal=True,
        key=(
            f"edit_transaction_type_"
            f"{transaction_id}"
        ),
    )
)


# ==================================================
# 수정용 대분류
# ==================================================

edit_main_categories = (
    get_main_categories(
        edit_transaction_type
    )
)


edit_main_names = [
    category["name"]
    for category
    in edit_main_categories
]


current_category = (
    selected_transaction[
        "category"
    ]
)


if (
    current_category
    not in edit_main_names
):

    edit_main_names.insert(
        0,
        current_category,
    )


current_main_index = (
    edit_main_names.index(
        current_category
    )
)


edit_main_category_name = (
    st.selectbox(
        "대분류",
        edit_main_names,
        index=current_main_index,
        key=(
            f"edit_main_category_"
            f"{transaction_id}"
        ),
    )
)


# ==================================================
# 선택된 대분류 ID 찾기
# ==================================================

edit_main_category_id = None


for category in edit_main_categories:

    if (
        category["name"]
        == edit_main_category_name
    ):

        edit_main_category_id = (
            category["id"]
        )

        break


# ==================================================
# 수정용 소분류
# ==================================================

edit_subcategory_name = None


current_subcategory = (
    selected_transaction.get(
        "subcategory"
    )
    or ""
)


if edit_main_category_id is not None:

    edit_subcategories = (
        get_subcategories(
            edit_main_category_id
        )
    )


    edit_subcategory_names = [
        subcategory["name"]
        for subcategory
        in edit_subcategories
    ]


    if (
        current_subcategory
        and
        current_subcategory
        not in edit_subcategory_names
    ):

        edit_subcategory_names.insert(
            0,
            current_subcategory,
        )


    if edit_subcategory_names:

        if (
            current_subcategory
            in edit_subcategory_names
        ):

            subcategory_index = (
                edit_subcategory_names.index(
                    current_subcategory
                )
            )

        else:

            subcategory_index = 0


        edit_subcategory_name = (
            st.selectbox(
                "소분류",
                edit_subcategory_names,
                index=subcategory_index,
                key=(
                    f"edit_subcategory_"
                    f"{transaction_id}"
                ),
            )
        )


# ==================================================
# 수정용 카드
# ==================================================

edit_card_id = None


if (
    edit_transaction_type
    == "지출"
):

    current_card_id = (
        selected_transaction.get(
            "card_id"
        )
    )


    try:

        current_card_id = (
            int(current_card_id)
            if current_card_id
            is not None
            else None
        )

    except (
        TypeError,
        ValueError,
    ):

        current_card_id = None


    if current_card_id is not None:

        default_payment_method = (
            "카드"
        )

    else:

        default_payment_method = (
            "기타"
        )


    payment_methods = [
        "카드",
        "기타",
    ]


    edit_payment_method = (
        st.radio(
            "결제수단",
            payment_methods,
            index=(
                payment_methods.index(
                    default_payment_method
                )
            ),
            horizontal=True,
            key=(
                f"edit_payment_method_"
                f"{transaction_id}"
            ),
        )
    )


    if (
        edit_payment_method
        == "카드"
        and cards
    ):

        edit_card_options = {
            (
                f'{card["name"]} · '
                f'{card["owner"]}'
            ):
            card

            for card in cards
        }


        edit_card_labels = list(
            edit_card_options.keys()
        )


        card_index = 0


        if (
            current_card_id
            is not None
        ):

            for index, label in enumerate(
                edit_card_labels
            ):

                if (
                    int(
                        edit_card_options[
                            label
                        ]["id"]
                    )
                    == current_card_id
                ):

                    card_index = index
                    break


        edit_card_label = (
            st.selectbox(
                "사용 카드",
                edit_card_labels,
                index=card_index,
                key=(
                    f"edit_card_"
                    f"{transaction_id}"
                ),
            )
        )


        edit_card_id = (
            edit_card_options[
                edit_card_label
            ]["id"]
        )


# ==================================================
# 수정 폼
# ==================================================

with st.form(
    f"edit_transaction_form_{transaction_id}"
):

    edit_date = st.date_input(
        "거래일",
        value=date.fromisoformat(
            selected_transaction[
                "transaction_date"
            ]
        ),
    )


    owners = [
        "나",
        "남편",
        "공동",
    ]


    try:

        owner_index = (
            owners.index(
                selected_transaction[
                    "owner"
                ]
            )
        )

    except ValueError:

        owner_index = 0


    edit_owner = st.selectbox(
        "사용자",
        owners,
        index=owner_index,
    )


    edit_amount = st.number_input(
        "금액",
        min_value=0,
        value=int(
            float(
                selected_transaction[
                    "amount"
                ]
            )
        ),
        step=10000,
    )


    edit_memo = st.text_input(
        "메모",
        value=(
            selected_transaction.get(
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

    if edit_amount <= 0:

        st.error(
            "금액을 입력해주세요."
        )

    elif (
        edit_transaction_type
        == "지출"
        and
        edit_payment_method
        == "카드"
        and
        edit_card_id
        is None
    ):

        st.error(
            "카드를 선택해주세요."
        )

    else:

        update_transaction(
            transaction_id=transaction_id,
            transaction_date=edit_date,
            transaction_type=(
                edit_transaction_type
            ),
            category=(
                edit_main_category_name
            ),
            subcategory=(
                edit_subcategory_name
            ),
            owner=edit_owner,
            amount=edit_amount,
            memo=edit_memo,
            card_id=(
                edit_card_id
                if (
                    edit_transaction_type
                    == "지출"
                )
                else None
            ),
        )

        st.success(
            "거래를 수정했습니다."
        )

        st.rerun()


# ==================================================
# 6. 거래 삭제
# ==================================================

st.divider()

st.subheader("🗑 거래 삭제")


if (
    "transaction_delete_target"
    not in st.session_state
):

    st.session_state[
        "transaction_delete_target"
    ] = None


if (
    st.session_state[
        "transaction_delete_target"
    ]
    != transaction_id
):

    st.session_state[
        "transaction_delete_confirm"
    ] = False

    st.session_state[
        "transaction_delete_target"
    ] = transaction_id


if (
    "transaction_delete_confirm"
    not in st.session_state
):

    st.session_state[
        "transaction_delete_confirm"
    ] = False


if not st.session_state[
    "transaction_delete_confirm"
]:

    if st.button(
        "선택한 거래 삭제",
        key=(
            f"delete_transaction_"
            f"{transaction_id}"
        ),
    ):

        st.session_state[
            "transaction_delete_confirm"
        ] = True

        st.rerun()


else:

    st.warning(
        f"{selected_transaction_label} "
        "거래를 정말 삭제하시겠습니까?"
    )


    col1, col2 = st.columns(2)


    with col1:

        if st.button(
            "삭제 확인",
            type="primary",
            key=(
                f"confirm_transaction_delete_"
                f"{transaction_id}"
            ),
            use_container_width=True,
        ):

            delete_transaction(
                transaction_id
            )

            st.session_state[
                "transaction_delete_confirm"
            ] = False

            st.session_state[
                "transaction_delete_target"
            ] = None

            st.rerun()


    with col2:

        if st.button(
            "취소",
            key=(
                f"cancel_transaction_delete_"
                f"{transaction_id}"
            ),
            use_container_width=True,
        ):

            st.session_state[
                "transaction_delete_confirm"
            ] = False

            st.rerun()