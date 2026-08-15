import streamlit as st
from supabase import create_client, Client


def create_supabase_client() -> Client:
    """
    새로운 Supabase 클라이언트를 생성한다.

    Streamlit 사용자 세션별로 별도 클라이언트를 사용하기 위해
    전역 cache_resource를 사용하지 않는다.
    """

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(
        url,
        key,
    )

def get_supabase() -> Client:

    # Streamlit 세션 안에 클라이언트가 없으면 생성
    if "supabase_client" not in st.session_state:

        st.session_state.supabase_client = (
            create_supabase_client()
        )

    supabase = (
        st.session_state.supabase_client
    )


    # 로그인 토큰이 있으면 Supabase 세션 복원
    access_token = (
        st.session_state.get(
            "access_token"
        )
    )

    refresh_token = (
        st.session_state.get(
            "refresh_token"
        )
    )


    if access_token and refresh_token:

        if not st.session_state.get(
            "supabase_session_restored",
            False,
        ):

            response = (
                supabase.auth.set_session(
                    access_token,
                    refresh_token,
                )
            )

            # set_session 과정에서 토큰이
            # 갱신됐을 수도 있으므로 다시 저장
            if response.session:

                st.session_state.access_token = (
                    response.session.access_token
                )

                st.session_state.refresh_token = (
                    response.session.refresh_token
                )

            st.session_state[
                "supabase_session_restored"
            ] = True


    return supabase

def get_assets():
    supabase = get_supabase()

    response = (
        supabase
        .table("assets")
        .select("*")
        .order("created_at")
        .execute()
    )

    return response.data

def add_asset(name, asset_type, owner, current_value, memo=""):
    supabase = get_supabase()

    family_id = get_family_id()

    response = (
        supabase
        .table("assets")
        .insert({
            "family_id": family_id,
            "name": name,
            "asset_type": asset_type,
            "owner": owner,
            "current_value": current_value,
            "memo": memo,
        })
        .execute()
    )

    return response.data

def update_asset(asset_id, name, asset_type, owner, current_value, memo=""):
    supabase = get_supabase()

    response = (
        supabase
        .table("assets")
        .update({
            "name": name,
            "asset_type": asset_type,
            "owner": owner,
            "current_value": current_value,
            "memo": memo,
        })
        .eq("id", asset_id)
        .execute()
    )

    return response.data

def delete_asset(asset_id):
    supabase = get_supabase()

    response = (
        supabase
        .table("assets")
        .delete()
        .eq("id", asset_id)
        .execute()
    )

    return response.data

def get_debts():
    supabase = get_supabase()

    response = (
        supabase
        .table("debts")
        .select("*")
        .order("created_at")
        .execute()
    )

    return response.data

def add_debt(
    name,
    debt_type,
    owner,
    balance,
    interest_rate=0,
    memo="",
    limit_amount=0,
):
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("debts")
        .insert({
            "family_id": family_id,
            "name": name.strip(),
            "debt_type": debt_type,
            "owner": owner,
            "balance": balance,
            "interest_rate": interest_rate,
            "limit_amount": limit_amount,
            "memo": memo,
        })
        .execute()
    )

    return response.data

def update_debt(
    debt_id,
    name,
    debt_type,
    owner,
    balance,
    interest_rate=0,
    memo="",
    limit_amount=0,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("debts")
        .update({
            "name": name.strip(),
            "debt_type": debt_type,
            "owner": owner,
            "balance": balance,
            "interest_rate": interest_rate,
            "limit_amount": limit_amount,
            "memo": memo,
        })
        .eq(
            "id",
            debt_id,
        )
        .execute()
    )

    return response.data

def delete_debt(debt_id):
    supabase = get_supabase()

    response = (
        supabase
        .table("debts")
        .delete()
        .eq("id", debt_id)
        .execute()
    )

    return response.data

def get_transactions():
    supabase = get_supabase()

    response = (
        supabase
        .table("transactions")
        .select("*")
        .order("transaction_date", desc=True)
        .execute()
    )

    return response.data

def add_transaction(
    transaction_date,
    transaction_type,
    category,
    owner,
    amount,
    memo="",
    card_id=None,
    subcategory=None,
    counts_for_performance=True,
):
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("transactions")
        .insert({
            "family_id": family_id,
            "transaction_date":
                str(transaction_date),
            "transaction_type":
                transaction_type,
            "category":
                category,
            "subcategory":
                subcategory,
            "owner":
                owner,
            "amount":
                amount,
            "memo":
                memo,
            "card_id":
                card_id,
            "counts_for_performance":
                bool(
                    counts_for_performance
                ),
        })
        .execute()
    )

    return response.data

def update_transaction(
    transaction_id,
    transaction_date,
    transaction_type,
    category,
    owner,
    amount,
    memo="",
    card_id=None,
    subcategory=None,
    counts_for_performance=True,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("transactions")
        .update({
            "transaction_date":
                str(transaction_date),
            "transaction_type":
                transaction_type,
            "category":
                category,
            "subcategory":
                subcategory,
            "owner":
                owner,
            "amount":
                amount,
            "memo":
                memo,
            "card_id":
                card_id,
            "counts_for_performance":
                bool(
                    counts_for_performance
                ),
        })
        .eq(
            "id",
            transaction_id,
        )
        .execute()
    )

    return response.data

def delete_transaction(transaction_id):
    supabase = get_supabase()

    response = (
        supabase
        .table("transactions")
        .delete()
        .eq("id", transaction_id)
        .execute()
    )

    return response.data

def get_net_worth_history():
    supabase = get_supabase()

    response = (
        supabase
        .table("net_worth_history")
        .select("*")
        .order("record_date")
        .execute()
    )

    return response.data

def add_net_worth_snapshot(
    record_date,
    total_assets,
    total_debts,
    net_worth,
):
    supabase = get_supabase()

    family_id = get_family_id()

    response = (
        supabase
        .table("net_worth_history")
        .upsert(
            {
                "family_id": family_id,
                "record_date": str(record_date),
                "total_assets": total_assets,
                "total_debts": total_debts,
                "net_worth": net_worth,
            },
            on_conflict="family_id,record_date",
        )
        .execute()
    )

    return response.data

def login(
    email,
    password,
):

    # 로그인할 때는 새로운 클라이언트 사용
    supabase = (
        create_supabase_client()
    )

    response = (
        supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )
    )


    if (
        response.user
        and response.session
    ):

        # 이 브라우저의 Streamlit 세션에만 저장
        st.session_state[
            "supabase_client"
        ] = supabase

        st.session_state[
            "access_token"
        ] = (
            response.session.access_token
        )

        st.session_state[
            "refresh_token"
        ] = (
            response.session.refresh_token
        )

        st.session_state[
            "supabase_session_restored"
        ] = True

        st.session_state[
            "logged_in"
        ] = True

        st.session_state[
            "user_email"
        ] = response.user.email


    return response

def logout():

    supabase = st.session_state.get(
        "supabase_client"
    )

    if supabase:

        try:
            supabase.auth.sign_out()

        except Exception:
            pass


    # 인증 관련 상태 삭제
    keys_to_delete = [
        "supabase_client",
        "access_token",
        "refresh_token",
        "supabase_session_restored",
        "logged_in",
        "user_email",
        "family_id",
    ]


    for key in keys_to_delete:

        if key in st.session_state:
            del st.session_state[key]

def get_family_id():
    supabase = get_supabase()

    user_response = supabase.auth.get_user()

    if not user_response.user:
        raise Exception("로그인된 사용자가 없습니다.")

    user_id = user_response.user.id

    response = (
        supabase
        .table("family_members")
        .select("family_id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    return response.data["family_id"]

def delete_net_worth_snapshot(snapshot_id):
    supabase = get_supabase()

    response = (
        supabase
        .table("net_worth_history")
        .delete()
        .eq("id", snapshot_id)
        .execute()
    )

    return response.data

# =========================
# 카드
# =========================

def get_cards():
    supabase = get_supabase()

    response = (
        supabase
        .table("cards")
        .select("*")
        .order("name")
        .execute()
    )

    return response.data


def add_card(
    name,
    owner,
    payment_day,
    billing_start_month_offset=-1,
    billing_start_day=1,
    billing_start_is_month_end=False,
    billing_end_month_offset=-1,
    billing_end_day=None,
    billing_end_is_month_end=True,
    monthly_performance=0,
):
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("cards")
        .insert({
            "family_id": family_id,
            "name": name.strip(),
            "owner": owner,
            "payment_day": int(
                payment_day
            ),
            "billing_start_month_offset":
                int(
                    billing_start_month_offset
                ),
            "billing_start_day":
                (
                    int(billing_start_day)
                    if billing_start_day
                    is not None
                    else None
                ),
            "billing_start_is_month_end":
                bool(
                    billing_start_is_month_end
                ),
            "billing_end_month_offset":
                int(
                    billing_end_month_offset
                ),
            "billing_end_day":
                (
                    int(billing_end_day)
                    if billing_end_day
                    is not None
                    else None
                ),
            "billing_end_is_month_end":
                bool(
                    billing_end_is_month_end
                ),
            "monthly_performance":
                float(
                    monthly_performance
                ),
        })
        .execute()
    )

    return response.data


def update_card(
    card_id,
    name,
    owner,
    payment_day,
    billing_start_month_offset=-1,
    billing_start_day=1,
    billing_start_is_month_end=False,
    billing_end_month_offset=-1,
    billing_end_day=None,
    billing_end_is_month_end=True,
    monthly_performance=0,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("cards")
        .update({
            "name": name.strip(),
            "owner": owner,
            "payment_day": int(
                payment_day
            ),
            "billing_start_month_offset":
                int(
                    billing_start_month_offset
                ),
            "billing_start_day":
                (
                    int(billing_start_day)
                    if billing_start_day
                    is not None
                    else None
                ),
            "billing_start_is_month_end":
                bool(
                    billing_start_is_month_end
                ),
            "billing_end_month_offset":
                int(
                    billing_end_month_offset
                ),
            "billing_end_day":
                (
                    int(billing_end_day)
                    if billing_end_day
                    is not None
                    else None
                ),
            "billing_end_is_month_end":
                bool(
                    billing_end_is_month_end
                ),
            "monthly_performance":
                float(
                    monthly_performance
                ),
        })
        .eq(
            "id",
            card_id,
        )
        .execute()
    )

    return response.data


def delete_card(card_id):
    supabase = get_supabase()

    response = (
        supabase
        .table("cards")
        .delete()
        .eq("id", card_id)
        .execute()
    )

    return response.data


# =========================
# 카테고리
# =========================

def get_categories(transaction_type=None):
    supabase = get_supabase()

    query = (
        supabase
        .table("categories")
        .select("*")
    )

    if transaction_type:
        query = query.eq(
            "transaction_type",
            transaction_type,
        )

    response = (
        query
        .order("name")
        .execute()
    )

    return response.data


def add_category(
    transaction_type,
    name,
    parent_id=None,
):
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("categories")
        .insert({
            "family_id": family_id,
            "transaction_type": transaction_type,
            "name": name.strip(),
            "parent_id": parent_id,
        })
        .execute()
    )

    return response.data

def get_main_categories(
    transaction_type,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("categories")
        .select("*")
        .eq(
            "transaction_type",
            transaction_type,
        )
        .is_(
            "parent_id",
            "null",
        )
        .order("name")
        .execute()
    )

    return response.data

def get_subcategories(
    parent_id,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("categories")
        .select("*")
        .eq(
            "parent_id",
            parent_id,
        )
        .order("name")
        .execute()
    )

    return response.data

def delete_category(category_id):
    supabase = get_supabase()

    response = (
        supabase
        .table("categories")
        .delete()
        .eq("id", category_id)
        .execute()
    )

    return response.data

def ensure_default_categories():
    supabase = get_supabase()
    family_id = get_family_id()

    # ----------------------------------------------
    # 기본 카테고리 구조
    # ----------------------------------------------

    default_categories = {
        "지출": {
            "생활비": [
                "식비",
                "생필품",
                "외식",
                "카페",
            ],

            "고정비": [
                "보험",
                "통신비",
                "관리비",
                "구독",
            ],

            "차량유지": [
                "주유",
                "주차",
                "정비",
                "자동차보험",
                "자동차세",
            ],

            "꾸밈": [
                "의류",
                "화장품",
                "미용",
            ],

            "운동": [
                "헬스",
                "골프",
                "기타운동",
            ],

            "경조사": [
                "축의금",
                "부의금",
                "선물",
            ],

            "여행": [
                "교통",
                "숙박",
                "식비",
                "관광",
                "쇼핑",
            ],

            "의료": [
                "병원",
                "약국",
                "건강검진",
            ],

            "교육": [],
            "주거": [],
            "취미": [],
            "기타": [],
        },

        "수입": {
            "월급": [],
            "상여금": [],
            "부수입": [],
            "이자": [],
            "배당금": [],
            "환급": [],
            "기타수입": [],
        },
    }

    # ----------------------------------------------
    # 현재 카테고리 조회
    # ----------------------------------------------

    response = (
        supabase
        .table("categories")
        .select("*")
        .eq("family_id", family_id)
        .execute()
    )

    existing_categories = response.data or []

    # ----------------------------------------------
    # 대분류 생성
    # ----------------------------------------------

    for transaction_type, main_categories in (
        default_categories.items()
    ):

        for main_name, subcategory_names in (
            main_categories.items()
        ):

            existing_main = next(
                (
                    category
                    for category
                    in existing_categories
                    if (
                        category["transaction_type"]
                        == transaction_type
                        and
                        category["name"]
                        == main_name
                        and
                        category.get("parent_id")
                        is None
                    )
                ),
                None,
            )

            if existing_main is None:

                insert_response = (
                    supabase
                    .table("categories")
                    .insert({
                        "family_id":
                            family_id,

                        "transaction_type":
                            transaction_type,

                        "name":
                            main_name,

                        "parent_id":
                            None,
                    })
                    .execute()
                )

                existing_main = (
                    insert_response.data[0]
                )

                existing_categories.append(
                    existing_main
                )

            main_id = existing_main["id"]

            # --------------------------------------
            # 소분류 생성
            # --------------------------------------

            for sub_name in (
                subcategory_names
            ):

                existing_sub = next(
                    (
                        category
                        for category
                        in existing_categories
                        if (
                            category[
                                "transaction_type"
                            ]
                            == transaction_type
                            and
                            category["name"]
                            == sub_name
                            and
                            category.get(
                                "parent_id"
                            )
                            == main_id
                        )
                    ),
                    None,
                )

                if existing_sub is None:

                    try:

                        insert_response = (
                            supabase
                            .table(
                                "categories"
                            )
                            .insert({
                                "family_id":
                                    family_id,

                                "transaction_type":
                                    transaction_type,

                                "name":
                                    sub_name,

                                "parent_id":
                                    main_id,
                            })
                            .execute()
                        )

                        if insert_response.data:

                            existing_categories.append(
                                insert_response.data[0]
                            )

                    except Exception:
                        # 기존에 같은 이름의 카테고리가
                        # 다른 위치에 존재할 수 있으므로
                        # 앱 전체를 중단시키지는 않음
                        pass

    # ==================================================
# 목적자금
# ==================================================

def get_funds():
    supabase = get_supabase()

    response = (
        supabase
        .table("funds")
        .select("*")
        .order("created_at")
        .execute()
    )

    return response.data


def add_fund(
    name,
    monthly_target=0,
    memo="",
):
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("funds")
        .insert({
            "family_id": family_id,
            "name": name.strip(),
            "monthly_target": monthly_target,
            "memo": memo,
        })
        .execute()
    )

    return response.data


def update_fund(
    fund_id,
    name,
    monthly_target,
    memo="",
):
    supabase = get_supabase()

    response = (
        supabase
        .table("funds")
        .update({
            "name": name.strip(),
            "monthly_target": monthly_target,
            "memo": memo,
        })
        .eq("id", fund_id)
        .execute()
    )

    return response.data


def delete_fund(fund_id):
    supabase = get_supabase()

    response = (
        supabase
        .table("funds")
        .delete()
        .eq("id", fund_id)
        .execute()
    )

    return response.data


# ==================================================
# 목적자금 입출금
# ==================================================

def get_fund_transactions(fund_id=None):
    supabase = get_supabase()

    query = (
        supabase
        .table("fund_transactions")
        .select("*")
    )

    if fund_id is not None:
        query = query.eq(
            "fund_id",
            fund_id,
        )

    response = (
        query
        .order(
            "transaction_date",
            desc=True,
        )
        .execute()
    )

    return response.data


def add_fund_transaction(
    fund_id,
    transaction_date,
    transaction_type,
    amount,
    memo="",
):
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("fund_transactions")
        .insert({
            "family_id": family_id,
            "fund_id": fund_id,
            "transaction_date": str(
                transaction_date
            ),
            "transaction_type": transaction_type,
            "amount": amount,
            "memo": memo,
        })
        .execute()
    )

    return response.data


def delete_fund_transaction(
    transaction_id,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("fund_transactions")
        .delete()
        .eq("id", transaction_id)
        .execute()
    )

    return response.data


def get_fund_balance(fund_id):
    transactions = (
        get_fund_transactions(
            fund_id
        )
    )

    total = 0

    for transaction in transactions:

        amount = float(
            transaction["amount"]
        )

        if (
            transaction[
                "transaction_type"
            ]
            == "적립"
        ):
            total += amount

        elif (
            transaction[
                "transaction_type"
            ]
            == "사용"
        ):
            total -= amount

    return total

# ==================================================
# 가계 운영 설정
# ==================================================

def get_household_settings():
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("household_settings")
        .select("*")
        .eq("family_id", family_id)
        .execute()
    )

    if response.data:
        return response.data[0]

    return {
        "family_id": family_id,
        "my_allowance": 0,
        "spouse_allowance": 0,
        "my_investment_budget": 0,
        "spouse_investment_budget": 0,
    }


def save_household_settings(
    my_allowance,
    spouse_allowance,
    my_investment_budget=0,
    spouse_investment_budget=0,
):
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("household_settings")
        .upsert(
            {
                "family_id": family_id,
                "my_allowance": my_allowance,
                "spouse_allowance": spouse_allowance,
                "my_investment_budget": my_investment_budget,
                "spouse_investment_budget": spouse_investment_budget,
            },
            on_conflict="family_id",
        )
        .execute()
    )

    return response.data

def get_current_user():

    access_token = (
        st.session_state.get(
            "access_token"
        )
    )

    if not access_token:
        return None


    supabase = get_supabase()


    try:

        # access token을 서버에서 검증
        response = (
            supabase.auth.get_user(
                access_token
            )
        )

        return response.user

    except Exception:

        return None

def get_family_id():

    # 매 DB 호출마다 family_members를
    # 조회하지 않도록 Streamlit 세션에 보관
    if st.session_state.get(
        "family_id"
    ):

        return st.session_state[
            "family_id"
        ]


    user = get_current_user()

    if not user:

        raise Exception(
            "로그인된 사용자가 없습니다."
        )


    supabase = get_supabase()


    response = (
        supabase
        .table("family_members")
        .select("family_id")
        .eq(
            "user_id",
            user.id,
        )
        .single()
        .execute()
    )


    family_id = (
        response.data[
            "family_id"
        ]
    )


    st.session_state[
        "family_id"
    ] = family_id


    return family_id

# ==================================================
# 투자 계좌
# ==================================================

def get_investment_accounts():
    supabase = get_supabase()

    response = (
        supabase
        .table("investment_accounts")
        .select("*")
        .order("owner")
        .order("account_type")
        .order("name")
        .execute()
    )

    return response.data


def add_investment_account(
    owner,
    account_type,
    name,
    memo="",
):
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("investment_accounts")
        .insert({
            "family_id": family_id,
            "owner": owner,
            "account_type": account_type,
            "name": name.strip(),
            "memo": memo,
        })
        .execute()
    )

    return response.data


def update_investment_account(
    account_id,
    owner,
    account_type,
    name,
    memo="",
):
    supabase = get_supabase()

    response = (
        supabase
        .table("investment_accounts")
        .update({
            "owner": owner,
            "account_type": account_type,
            "name": name.strip(),
            "memo": memo,
        })
        .eq("id", account_id)
        .execute()
    )

    return response.data


def delete_investment_account(
    account_id,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("investment_accounts")
        .delete()
        .eq("id", account_id)
        .execute()
    )

    return response.data


# ==================================================
# 투자 거래
# ==================================================

def get_investment_transactions(
    account_id=None,
):
    supabase = get_supabase()

    query = (
        supabase
        .table("investment_transactions")
        .select("*")
    )

    if account_id is not None:
        query = query.eq(
            "account_id",
            account_id,
        )

    response = (
        query
        .order(
            "transaction_date",
            desc=True,
        )
        .order(
            "id",
            desc=True,
        )
        .execute()
    )

    return response.data


def add_investment_transaction(
    account_id,
    transaction_date,
    transaction_type,
    symbol=None,
    asset_name=None,
    quantity=None,
    price=None,
    amount=None,
    fee=0,
    memo="",
    currency="KRW",
    exchange_rate=None,
):
    supabase = get_supabase()
    family_id = get_family_id()

    response = (
        supabase
        .table("investment_transactions")
        .insert({
            "family_id": family_id,
            "account_id": account_id,
            "transaction_date": str(
                transaction_date
            ),
            "transaction_type":
                transaction_type,
            "symbol":
                symbol.strip()
                if symbol
                else None,
            "asset_name":
                asset_name.strip()
                if asset_name
                else None,
            "quantity": quantity,
            "price": price,
            "amount": amount,
            "fee": fee or 0,
            "memo": memo,
            "currency": currency,
            "exchange_rate":
                exchange_rate,
        })
        .execute()
    )

    return response.data


def delete_investment_transaction(
    transaction_id,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("investment_transactions")
        .delete()
        .eq(
            "id",
            transaction_id,
        )
        .execute()
    )

    return response.data

def update_investment_transaction(
    transaction_id,
    transaction_date,
    transaction_type,
    symbol=None,
    asset_name=None,
    quantity=None,
    price=None,
    amount=None,
    fee=0,
    memo="",
    currency="KRW",
    exchange_rate=None,
):
    supabase = get_supabase()

    response = (
        supabase
        .table("investment_transactions")
        .update({
            "transaction_date": str(
                transaction_date
            ),
            "transaction_type":
                transaction_type,
            "symbol":
                symbol.strip()
                if symbol
                else None,
            "asset_name":
                asset_name.strip()
                if asset_name
                else None,
            "quantity": quantity,
            "price": price,
            "amount": amount,
            "fee": fee or 0,
            "memo": memo,
            "currency": currency,
            "exchange_rate":
                exchange_rate,
        })
        .eq(
            "id",
            transaction_id,
        )
        .execute()
    )

    return response.data