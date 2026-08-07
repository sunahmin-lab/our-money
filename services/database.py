import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)


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
    interest_rate=None,
    memo=""
):
    supabase = get_supabase()

    family_id = get_family_id()

    response = (
        supabase
        .table("debts")
        .insert({
            "family_id": family_id,
            "name": name,
            "debt_type": debt_type,
            "owner": owner,
            "balance": balance,
            "interest_rate": interest_rate,
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
    interest_rate=None,
    memo=""
):
    supabase = get_supabase()

    response = (
        supabase
        .table("debts")
        .update({
            "name": name,
            "debt_type": debt_type,
            "owner": owner,
            "balance": balance,
            "interest_rate": interest_rate,
            "memo": memo,
        })
        .eq("id", debt_id)
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
    memo=""
):
    supabase = get_supabase()

    family_id = get_family_id()

    response = (
        supabase
        .table("transactions")
        .insert({
            "family_id": family_id,
            "transaction_date": str(transaction_date),
            "transaction_type": transaction_type,
            "category": category,
            "owner": owner,
            "amount": amount,
            "memo": memo,
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
    memo=""
):
    supabase = get_supabase()

    response = (
        supabase
        .table("transactions")
        .update({
            "transaction_date": str(transaction_date),
            "transaction_type": transaction_type,
            "category": category,
            "owner": owner,
            "amount": amount,
            "memo": memo,
        })
        .eq("id", transaction_id)
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

def login(email, password):
    supabase = get_supabase()

    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password,
    })

    return response


def logout():
    supabase = get_supabase()
    supabase.auth.sign_out()

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