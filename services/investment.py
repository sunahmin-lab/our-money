import json
import urllib.parse
import urllib.request
import FinanceDataReader as fdr

import yfinance as yf
# ==================================================
# 현재가 조회
# ==================================================

def get_current_price(symbol):
    """
    Yahoo Finance 기준 최신 조회 가격.

    예:
    삼성전자        005930.KS
    KOSDAQ 종목     XXXXX.KQ
    미국주식        AAPL
    """

    if not symbol:
        return None

    symbol = symbol.strip()

    try:
        ticker = yf.Ticker(symbol)

        fast_info = ticker.fast_info

        try:
            price = fast_info["last_price"]

            if price is not None:
                return float(price)

        except Exception:
            pass

    except Exception:
        pass


    try:
        ticker = yf.Ticker(symbol)

        history = ticker.history(
            period="5d",
            interval="1d",
        )

        if history.empty:
            return None

        close_prices = (
            history["Close"]
            .dropna()
        )

        if close_prices.empty:
            return None

        return float(
            close_prices.iloc[-1]
        )

    except Exception:
        return None


# ==================================================
# 종목별 보유현황
# ==================================================

def calculate_holdings(
    transactions,
):
    """
    이동평균법 기준 보유수량 계산.

    해외주식은 매수 당시 환율을 사용해
    KRW 원가도 별도로 저장한다.
    """

    holdings = {}


    sorted_transactions = sorted(
        transactions,
        key=lambda x: (
            x["transaction_date"],
            x["id"],
        ),
    )


    for tx in sorted_transactions:

        tx_type = tx.get(
            "transaction_type"
        )


        if tx_type not in [
            "매수",
            "매도",
        ]:
            continue


        symbol = (
            tx.get("symbol")
            or ""
        ).strip()


        if not symbol:
            continue


        currency = (
            tx.get("currency")
            or "KRW"
        ).upper()


        quantity = float(
            tx.get("quantity")
            or 0
        )


        price = float(
            tx.get("price")
            or 0
        )


        fee = float(
            tx.get("fee")
            or 0
        )


        exchange_rate = float(
            tx.get("exchange_rate")
            or (
                1
                if currency == "KRW"
                else 0
            )
        )


        if quantity <= 0:
            continue


        if currency != "KRW" and (
            exchange_rate <= 0
        ):
            continue


        if symbol not in holdings:

            holdings[symbol] = {
                "symbol":
                    symbol,

                "asset_name":
                    (
                        tx.get(
                            "asset_name"
                        )
                        or symbol
                    ),

                "currency":
                    currency,

                "quantity":
                    0.0,

                "cost_basis_local":
                    0.0,

                "cost_basis_krw":
                    0.0,

                "average_price":
                    0.0,

                "average_price_krw":
                    0.0,
            }


        holding = holdings[
            symbol
        ]


        # ==========================================
        # 매수
        # ==========================================

        if tx_type == "매수":

            local_cost = (
                quantity
                * price
                + fee
            )


            krw_cost = (
                local_cost
                * exchange_rate
            )


            holding[
                "quantity"
            ] += quantity


            holding[
                "cost_basis_local"
            ] += local_cost


            holding[
                "cost_basis_krw"
            ] += krw_cost


            if holding[
                "quantity"
            ] > 0:

                holding[
                    "average_price"
                ] = (
                    holding[
                        "cost_basis_local"
                    ]
                    / holding[
                        "quantity"
                    ]
                )


                holding[
                    "average_price_krw"
                ] = (
                    holding[
                        "cost_basis_krw"
                    ]
                    / holding[
                        "quantity"
                    ]
                )


        # ==========================================
        # 매도
        # ==========================================

        elif tx_type == "매도":

            current_quantity = (
                holding[
                    "quantity"
                ]
            )


            if current_quantity <= 0:
                continue


            sell_quantity = min(
                quantity,
                current_quantity,
            )


            local_average = (
                holding[
                    "average_price"
                ]
            )


            krw_average = (
                holding[
                    "average_price_krw"
                ]
            )


            holding[
                "quantity"
            ] -= sell_quantity


            holding[
                "cost_basis_local"
            ] -= (
                local_average
                * sell_quantity
            )


            holding[
                "cost_basis_krw"
            ] -= (
                krw_average
                * sell_quantity
            )


            if holding[
                "quantity"
            ] <= 0:

                holding[
                    "quantity"
                ] = 0

                holding[
                    "cost_basis_local"
                ] = 0

                holding[
                    "cost_basis_krw"
                ] = 0

                holding[
                    "average_price"
                ] = 0

                holding[
                    "average_price_krw"
                ] = 0


    return {
        symbol: holding

        for symbol, holding
        in holdings.items()

        if holding[
            "quantity"
        ] > 0
    }


# ==================================================
# 계좌 현금 계산
# ==================================================

# ==================================================
# 계좌 현금 계산
# ==================================================

def calculate_account_cash(
    transactions,
):
    """
    투자계좌 내부의 현금 잔액을 KRW 기준으로 계산한다.

    원화 거래:
        그대로 KRW 계산

    외화 거래:
        거래 당시 exchange_rate를 적용해서
        KRW 기준으로 환산

    계산:
        입금 +
        매도 +
        배당 +

        매수 -
        출금 -
    """

    cash_krw = 0.0


    for tx in transactions:

        tx_type = (
            tx.get(
                "transaction_type"
            )
        )


        currency = (
            tx.get(
                "currency"
            )
            or "KRW"
        ).upper()


        quantity = float(
            tx.get(
                "quantity"
            )
            or 0
        )


        price = float(
            tx.get(
                "price"
            )
            or 0
        )


        amount = float(
            tx.get(
                "amount"
            )
            or 0
        )


        fee = float(
            tx.get(
                "fee"
            )
            or 0
        )


        # ==========================================
        # 적용 환율
        # ==========================================

        if currency == "KRW":

            exchange_rate = 1.0

        else:

            exchange_rate = float(
                tx.get(
                    "exchange_rate"
                )
                or 0
            )


        # 외화 거래인데 환율이 없으면
        # 잘못된 현금 계산을 방지하기 위해 제외
        if (
            currency != "KRW"
            and exchange_rate <= 0
        ):

            continue


        # ==========================================
        # 입금
        # ==========================================

        if tx_type == "입금":

            cash_krw += (
                amount
                * exchange_rate
            )


        # ==========================================
        # 출금
        # ==========================================

        elif tx_type == "출금":

            cash_krw -= (
                amount
                * exchange_rate
            )


        # ==========================================
        # 매수
        # ==========================================

        elif tx_type == "매수":

            local_cost = (
                quantity
                * price
                + fee
            )


            cash_krw -= (
                local_cost
                * exchange_rate
            )


        # ==========================================
        # 매도
        # ==========================================

        elif tx_type == "매도":

            local_proceeds = (
                quantity
                * price
                - fee
            )


            cash_krw += (
                local_proceeds
                * exchange_rate
            )


        # ==========================================
        # 배당
        # ==========================================

        elif tx_type == "배당":

            cash_krw += (
                amount
                * exchange_rate
            )


    return cash_krw


# ==================================================
# 외부 투자금 계산
# ==================================================

# ==================================================
# 외부 투자금 계산
# ==================================================

def calculate_net_contribution(
    transactions,
):
    """
    가계에서 투자계좌로 실제 이동한 순투자금을
    KRW 기준으로 계산한다.

    입금 - 출금

    매수/매도/배당은 계좌 내부 거래이므로 제외한다.
    """

    total_deposit_krw = 0.0
    total_withdrawal_krw = 0.0


    for tx in transactions:

        tx_type = (
            tx.get(
                "transaction_type"
            )
        )


        if tx_type not in [
            "입금",
            "출금",
        ]:

            continue


        currency = (
            tx.get(
                "currency"
            )
            or "KRW"
        ).upper()


        amount = float(
            tx.get(
                "amount"
            )
            or 0
        )


        if currency == "KRW":

            exchange_rate = 1.0

        else:

            exchange_rate = float(
                tx.get(
                    "exchange_rate"
                )
                or 0
            )


        if (
            currency != "KRW"
            and exchange_rate <= 0
        ):

            continue


        amount_krw = (
            amount
            * exchange_rate
        )


        if tx_type == "입금":

            total_deposit_krw += (
                amount_krw
            )


        elif tx_type == "출금":

            total_withdrawal_krw += (
                amount_krw
            )


    return {
        "total_deposit":
            total_deposit_krw,

        "total_withdrawal":
            total_withdrawal_krw,

        "net_contribution":
            (
                total_deposit_krw
                - total_withdrawal_krw
            ),
    }


# ==================================================
# 보유종목 평가
# ==================================================

def evaluate_holdings(
    holdings,
    price_map=None,
    exchange_rate_map=None,
):
    """
    현재 주가와 현재 환율로
    원화 평가액/수익률을 계산한다.

    원가는 매수 당시 환율 기준.
    """

    results = []


    for symbol, holding in (
        holdings.items()
    ):

        currency = (
            holding.get(
                "currency"
            )
            or "KRW"
        ).upper()


        # ==========================================
        # 현재가
        # ==========================================

        if (
            price_map
            and symbol in price_map
        ):

            current_price = (
                price_map[symbol]
            )

        else:

            current_price = (
                get_current_price(
                    symbol
                )
            )


        # ==========================================
        # 현재 환율
        # ==========================================

        if currency == "KRW":

            current_exchange_rate = 1.0


        elif (
            exchange_rate_map
            and currency
            in exchange_rate_map
        ):

            current_exchange_rate = (
                exchange_rate_map[
                    currency
                ]
            )


        else:

            current_exchange_rate = (
                get_current_exchange_rate(
                    currency,
                    "KRW",
                )
            )


        quantity = float(
            holding[
                "quantity"
            ]
        )


        cost_basis_local = float(
            holding[
                "cost_basis_local"
            ]
        )


        cost_basis_krw = float(
            holding[
                "cost_basis_krw"
            ]
        )


        if (
            current_price is None
            or
            current_exchange_rate
            is None
        ):

            market_value_local = None
            market_value_krw = None
            profit_krw = None
            return_rate = None


        else:

            market_value_local = (
                quantity
                * current_price
            )


            market_value_krw = (
                market_value_local
                * current_exchange_rate
            )


            profit_krw = (
                market_value_krw
                - cost_basis_krw
            )


            if cost_basis_krw > 0:

                return_rate = (
                    profit_krw
                    / cost_basis_krw
                    * 100
                )

            else:

                return_rate = 0


        results.append({
            **holding,

            "current_price":
                current_price,

            "current_exchange_rate":
                current_exchange_rate,

            "market_value_local":
                market_value_local,

            "market_value":
                market_value_krw,

            "profit":
                profit_krw,

            "return_rate":
                return_rate,
        })


    return results

# ==================================================
# 계좌 전체 요약
# ==================================================

def calculate_account_summary(
    transactions,
    evaluated_holdings,
):
    """
    계좌 전체 평가:

    주식 평가액
    + 계좌 내 현금
    = 현재 계좌 평가액

    현재 평가액
    - 순입금액
    = 총 손익
    """

    contribution = (
        calculate_net_contribution(
            transactions
        )
    )


    cash_balance = (
        calculate_account_cash(
            transactions
        )
    )


    stock_value = sum(
        holding["market_value"]

        for holding
        in evaluated_holdings

        if (
            holding["market_value"]
            is not None
        )
    )


    account_value = (
        stock_value
        + cash_balance
    )


    net_contribution = (
        contribution[
            "net_contribution"
        ]
    )


    total_profit = (
        account_value
        - net_contribution
    )


    if net_contribution > 0:

        return_rate = (
            total_profit
            / net_contribution
            * 100
        )

    else:

        return_rate = 0


    return {
        "total_deposit":
            contribution[
                "total_deposit"
            ],

        "total_withdrawal":
            contribution[
                "total_withdrawal"
            ],

        "net_contribution":
            net_contribution,

        "cash_balance":
            cash_balance,

        "stock_value":
            stock_value,

        "account_value":
            account_value,

        "profit":
            total_profit,

        "return_rate":
            return_rate,
    }

# ==================================================
# 환율 조회
# ==================================================

def get_exchange_rate(
    from_currency,
    to_currency="KRW",
):
    """
    Frankfurter 기준 최근 일일 환율.

    예:
    USD -> KRW
    """

    from_currency = (
        from_currency
        .strip()
        .upper()
    )

    to_currency = (
        to_currency
        .strip()
        .upper()
    )


    if (
        from_currency
        == to_currency
    ):
        return 1.0


    url = (
        "https://api.frankfurter.dev/v2/rates"
        f"?base={from_currency}"
        f"&quotes={to_currency}"
    )


    try:

        with urllib.request.urlopen(
            url,
            timeout=10,
        ) as response:

            data = json.loads(
                response.read()
            )


        if not data:
            return None


        for item in data:

            if (
                item.get("base")
                == from_currency
                and
                item.get("quote")
                == to_currency
            ):

                return float(
                    item["rate"]
                )


        return None

    except Exception:

        return None

# ==================================================
# 현재 환율
# ==================================================

def get_current_exchange_rate(
    from_currency,
    to_currency="KRW",
):
    from_currency = (
        from_currency
        .strip()
        .upper()
    )

    to_currency = (
        to_currency
        .strip()
        .upper()
    )

    if from_currency == to_currency:
        return 1.0


    url = (
        "https://api.frankfurter.dev/v2/rate/"
        f"{from_currency}/"
        f"{to_currency}"
    )


    try:

        with urllib.request.urlopen(
            url,
            timeout=10,
        ) as response:

            data = json.loads(
                response.read()
                .decode("utf-8")
            )


        rate = data.get(
            "rate"
        )


        if rate is None:
            return None


        return float(rate)


    except Exception:

        return None

# ==================================================
# 과거 환율
# ==================================================

def get_historical_exchange_rate(
    transaction_date,
    from_currency,
    to_currency="KRW",
):
    from_currency = (
        from_currency
        .strip()
        .upper()
    )

    to_currency = (
        to_currency
        .strip()
        .upper()
    )


    if from_currency == to_currency:
        return 1.0


    date_text = str(
        transaction_date
    )


    params = urllib.parse.urlencode({
        "base": from_currency,
        "symbols": to_currency,
    })


    url = (
        "https://api.frankfurter.dev/v1/"
        f"{date_text}"
        f"?{params}"
    )


    try:

        with urllib.request.urlopen(
            url,
            timeout=10,
        ) as response:

            data = json.loads(
                response.read()
                .decode("utf-8")
            )


        rates = data.get(
            "rates",
            {}
        )


        rate = rates.get(
            to_currency
        )


        if rate is None:
            return None


        return float(rate)


    except Exception:

        return None

# ==================================================
# 종목 검색
# ==================================================

# ==================================================
# 통합 종목 검색
# ==================================================

def search_investment_symbols(
    query,
    max_results=30,
):
    """
    국내 + 해외 통합 검색.

    1. KRX 국내 종목 검색
    2. Yahoo Finance 검색
    3. 중복 제거
    """

    if not query:
        return []

    query = query.strip()

    if not query:
        return []

    results = []


    # ==================================================
    # 1. 국내 KRX 검색
    # ==================================================

    korean_results = (
        search_korean_symbols(
            query,
            max_results=max_results,
        )
    )


    results.extend(
        korean_results
    )


    # ==================================================
    # 2. Yahoo 검색
    # ==================================================

    try:

        search = yf.Search(
            query,
            max_results=max_results,
            news_count=0,
            lists_count=0,
            include_cb=False,
            include_nav_links=False,
            include_research=False,
            enable_fuzzy_query=True,
            raise_errors=False,
        )


        quotes = (
            search.quotes
            or []
        )


        for item in quotes:

            symbol = (
                item.get(
                    "symbol"
                )
                or ""
            ).strip()


            if not symbol:
                continue


            name = (
                item.get(
                    "longname"
                )
                or
                item.get(
                    "shortname"
                )
                or
                item.get(
                    "name"
                )
                or
                symbol
            )


            exchange = (
                item.get(
                    "exchange"
                )
                or
                item.get(
                    "exchDisp"
                )
                or
                ""
            )


            currency = (
                item.get(
                    "currency"
                )
                or ""
            ).upper()


            if not currency:

                if symbol.endswith(
                    (
                        ".KS",
                        ".KQ",
                    )
                ):

                    currency = "KRW"

                else:

                    currency = "USD"


            results.append({
                "symbol":
                    symbol,

                "code":
                    symbol.split(
                        "."
                    )[0],

                "name":
                    name,

                "exchange":
                    exchange,

                "currency":
                    currency,

                "quote_type":
                    (
                        item.get(
                            "quoteType"
                        )
                        or ""
                    ),

                "source":
                    "Yahoo",
            })


    except Exception:

        pass


    # ==================================================
    # 3. 중복 제거
    # ==================================================

    unique_results = []

    seen_symbols = set()


    for item in results:

        symbol = item[
            "symbol"
        ]


        if symbol in seen_symbols:
            continue


        seen_symbols.add(
            symbol
        )


        unique_results.append(
            item
        )


    # 국내 검색 결과를 우선 표시
    unique_results.sort(
        key=lambda item: (
            0
            if item.get(
                "source"
            ) == "KRX"
            else 1
        )
    )


    return unique_results[
        :max_results
    ]

# ==================================================
# 국내 KRX 종목 검색
# ==================================================

# ==================================================
# 국내 KRX 종목 검색
# ==================================================

def search_korean_symbols(
    query,
    max_results=30,
):
    """
    국내 ETF/주식 부분검색.

    검색 순서:
    1. ETF/KR
    2. KRX
    3. 실패해도 가능한 결과는 유지

    예:
    TIME
    미국나스닥
    TIME 미국 나스닥
    426030
    """

    if not query:
        return []

    query = query.strip()

    if not query:
        return []

    normalized_query = (
        query
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .lower()
    )

    query_tokens = [
        token
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .lower()

        for token in query.split()

        if token.strip()
    ]

    results = []
    seen_codes = set()


    # ==================================================
    # 목록 검색 공통 함수
    # ==================================================

    def search_listing(
        listing,
        source_name,
    ):
        local_results = []

        if (
            listing is None
            or listing.empty
        ):
            return local_results


        code_column = None
        name_column = None
        market_column = None


        for candidate in [
            "Code",
            "Symbol",
            "Ticker",
        ]:
            if candidate in listing.columns:
                code_column = candidate
                break


        for candidate in [
            "Name",
            "종목명",
        ]:
            if candidate in listing.columns:
                name_column = candidate
                break


        for candidate in [
            "Market",
            "시장구분",
        ]:
            if candidate in listing.columns:
                market_column = candidate
                break


        if (
            code_column is None
            or name_column is None
        ):
            return local_results


        for _, row in listing.iterrows():

            code = str(
                row[code_column]
            ).strip()


            name = str(
                row[name_column]
            ).strip()


            if not code or not name:
                continue


            normalized_name = (
                name
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
                .lower()
            )


            # ======================================
            # 검색 점수
            # ======================================

            score = 0


            if query == code:
                score = 1000


            elif (
                normalized_name
                == normalized_query
            ):
                score = 900


            elif (
                normalized_query
                in normalized_name
            ):
                score = 800


            elif (
                query_tokens
                and
                all(
                    token in normalized_name
                    for token in query_tokens
                )
            ):
                score = 700


            elif query_tokens:

                matched_tokens = sum(
                    1
                    for token in query_tokens
                    if token in normalized_name
                )

                if matched_tokens > 0:
                    score = (
                        400
                        + matched_tokens * 50
                    )


            if score == 0:
                continue


            market = ""

            if market_column:
                market = str(
                    row.get(
                        market_column,
                        "",
                    )
                ).upper()


            # ETF/KR은 기본적으로 KRX 상장 ETF
            if source_name == "ETF/KR":

                yahoo_symbol = (
                    f"{code}.KS"
                )

                quote_type = "ETF"


            else:

                if "KOSDAQ" in market:
                    yahoo_symbol = (
                        f"{code}.KQ"
                    )
                else:
                    yahoo_symbol = (
                        f"{code}.KS"
                    )

                quote_type = "STOCK"


            local_results.append({
                "symbol":
                    yahoo_symbol,

                "code":
                    code,

                "name":
                    name,

                "exchange":
                    (
                        market
                        if market
                        else "KRX"
                    ),

                "currency":
                    "KRW",

                "quote_type":
                    quote_type,

                "source":
                    source_name,

                "_search_score":
                    score,
            })


        return local_results


    # ==================================================
    # 1. 국내 ETF
    # ==================================================

    try:

        etf_listing = (
            fdr.StockListing(
                "ETF/KR"
            )
        )


        etf_results = (
            search_listing(
                etf_listing,
                "ETF/KR",
            )
        )


        for item in etf_results:

            code = item[
                "code"
            ]

            if code in seen_codes:
                continue

            seen_codes.add(
                code
            )

            results.append(
                item
            )


    except Exception:
        pass


    # ==================================================
    # 2. 국내 주식
    # ==================================================

    try:

        krx_listing = (
            fdr.StockListing(
                "KRX"
            )
        )


        stock_results = (
            search_listing(
                krx_listing,
                "KRX",
            )
        )


        for item in stock_results:

            code = item[
                "code"
            ]

            if code in seen_codes:
                continue

            seen_codes.add(
                code
            )

            results.append(
                item
            )


    except Exception:
        pass


    # ==================================================
    # 3. 확실히 알고 있는 종목 fallback
    #
    # 외부 목록 조회가 실패해도
    # 이 종목은 검색 가능하게 함
    # ==================================================

    fallback_assets = [
        {
            "code":
                "426030",

            "name":
                "TIME 미국나스닥100액티브",

            "symbol":
                "426030.KS",

            "exchange":
                "KRX",

            "currency":
                "KRW",

            "quote_type":
                "ETF",

            "source":
                "Fallback",
        },
    ]


    for asset in fallback_assets:

        normalized_name = (
            asset["name"]
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
            .lower()
        )


        matched = (
            normalized_query
            in normalized_name
        )


        if not matched and query_tokens:

            matched = all(
                token in normalized_name
                for token in query_tokens
            )


        if (
            matched
            and
            asset["code"]
            not in seen_codes
        ):

            results.append({
                **asset,
                "_search_score":
                    850,
            })

            seen_codes.add(
                asset["code"]
            )


    # ==================================================
    # 정렬
    # ==================================================

    results.sort(
        key=lambda item: (
            -item.get(
                "_search_score",
                0,
            ),
            len(
                item["name"]
            ),
            item["name"],
        )
    )


    for item in results:
        item.pop(
            "_search_score",
            None,
        )


    return results[
        :max_results
    ]