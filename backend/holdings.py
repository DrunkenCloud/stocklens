import datetime as dt

from services.exposure import look_through
from services.ledger import growth_series, positions, xirr

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
MF_SECTOR = "Mutual funds"
SPARK_POINTS = 30

STOCK_LEDGER_SQL = """
SELECT symbol, broker, kind, quantity AS units, quantity * price AS amount, date, created_at
FROM stock_transactions WHERE user_id = %s
"""
MF_LEDGER_SQL = """
SELECT code, broker, kind, units, amount, date, created_at
FROM mf_transactions WHERE user_id = %s
"""


def load_ledger(conn, scope: str) -> list[dict]:
    txs = []
    if scope != "mf":
        txs += [{**r, "key": ("st", r["symbol"], r["broker"])} for r in conn.execute(STOCK_LEDGER_SQL, (DEFAULT_USER_ID,))]
    if scope != "stocks":
        txs += [{**r, "key": ("mf", r["code"], r["broker"])} for r in conn.execute(MF_LEDGER_SQL, (DEFAULT_USER_ID,))]
    return txs


def scheme_label(s: dict) -> str:
    return f"{s['name']} ({s['plan']})" if s.get("plan") else s["name"]


def _recent_prices(conn, symbols: list[str], codes: list[int]) -> dict[tuple, list[tuple[dt.date, float]]]:
    out: dict[tuple, list] = {}
    if symbols:
        for r in conn.execute(
            """
            SELECT symbol, date, close::float AS price FROM (
                SELECT symbol, date, close, row_number() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
                FROM daily_prices WHERE symbol = ANY(%s)
            ) t WHERE rn <= %s ORDER BY symbol, date
            """,
            (symbols, SPARK_POINTS),
        ):
            out.setdefault(("st", r["symbol"]), []).append((r["date"], r["price"]))
    if codes:
        for r in conn.execute(
            """
            SELECT code, date, nav::float AS price FROM (
                SELECT code, date, nav, row_number() OVER (PARTITION BY code ORDER BY date DESC) AS rn
                FROM mf_nav WHERE code = ANY(%s)
            ) t WHERE rn <= %s ORDER BY code, date
            """,
            (codes, SPARK_POINTS),
        ):
            out.setdefault(("mf", r["code"]), []).append((r["date"], r["price"]))
    return out


def _flows(txs: list[dict]) -> list[tuple[dt.date, float]] | None:
    if any(t["date"] is None for t in txs):
        return None
    return [(t["date"], -float(t["amount"]) if t["kind"] == "buy" else float(t["amount"])) for t in txs]


def holding_rows(conn, scope: str) -> tuple[list[dict], dict]:
    txs = load_ledger(conn, scope)
    book = positions(txs)
    by_key: dict[tuple, list[dict]] = {}
    for t in txs:
        by_key.setdefault(t["key"], []).append(t)

    symbols = sorted({k[1] for k in book if k[0] == "st"})
    codes = sorted({k[1] for k in book if k[0] == "mf"})
    companies = {c["symbol"]: c for c in conn.execute(
        "SELECT symbol, name, sector, kind, asset_class, exchange FROM companies WHERE symbol = ANY(%s)", (symbols,)
    )} if symbols else {}
    schemes = {s["code"]: s for s in conn.execute("SELECT * FROM mf_schemes WHERE code = ANY(%s)", (codes,))} if codes else {}
    recent = _recent_prices(conn, symbols, codes)
    today = dt.date.today()

    rows, all_flows, dated_value, dated_invested, total_invested = [], [], 0.0, 0.0, 0.0
    for key, pos in sorted(book.items(), key=lambda kv: str(kv[0])):
        kind, asset, broker = key
        series = recent.get((kind, asset), [])
        close = series[-1][1] if series else None
        value = pos["units"] * close if close is not None else None
        flows = _flows(by_key[key])
        holding_xirr = None
        if flows is not None and value is not None:
            holding_xirr = xirr(flows + [(today, value)])
            all_flows += flows
            all_flows.append((today, value))
            dated_value += value
            dated_invested += pos["invested"]
        total_invested += pos["invested"]
        base = {
            "quantity": pos["units"],
            "invested": pos["invested"],
            "realized": pos["realized"],
            "broker": broker,
            "source": "manual",
            "close": close,
            "prev_close": series[-2][1] if len(series) > 1 else None,
            "price_date": series[-1][0] if series else None,
            "spark": [p for _, p in series],
            "xirr": holding_xirr,
            "dated": flows is not None,
        }
        if kind == "st":
            c = companies[asset]
            rows.append({**base, "id": f"st:{asset}:{broker}", "symbol": asset, "name": c["name"], "sector": c["sector"],
                         "kind": c["kind"], "asset_class": c["asset_class"], "exchange": c["exchange"], "category": None})
        else:
            s = schemes[asset]
            rows.append({**base, "id": f"mf:{asset}:{broker}", "symbol": str(asset), "name": scheme_label(s),
                         "sector": MF_SECTOR, "kind": "mf", "asset_class": s["asset_class"], "exchange": None,
                         "category": s["category"]})

    overall = {
        "xirr": xirr(all_flows) if all_flows else None,
        "xirr_coverage_pct": dated_invested / total_invested * 100 if total_invested else None,
    }
    return rows, overall


def growth(conn, scope: str, since: dt.date) -> dict:
    txs = load_ledger(conn, scope)
    undated_keys = {t["key"] for t in txs if t["date"] is None}
    dated = [t for t in txs if t["key"] not in undated_keys]
    excluded = positions([t for t in txs if t["key"] in undated_keys])

    first = min((t["date"] for t in dated), default=None)
    prices: dict[tuple, list[tuple[dt.date, float]]] = {}
    if first:
        symbols = sorted({t["key"][1] for t in dated if t["key"][0] == "st"})
        codes = sorted({t["key"][1] for t in dated if t["key"][0] == "mf"})
        by_asset: dict[tuple, list] = {}
        if symbols:
            for r in conn.execute(
                "SELECT symbol, date, close::float AS p FROM daily_prices WHERE symbol = ANY(%s) AND date >= %s ORDER BY date",
                (symbols, first - dt.timedelta(days=10)),
            ):
                by_asset.setdefault(("st", r["symbol"]), []).append((r["date"], r["p"]))
        if codes:
            for r in conn.execute(
                "SELECT code, date, nav::float AS p FROM mf_nav WHERE code = ANY(%s) AND date >= %s ORDER BY date",
                (codes, first - dt.timedelta(days=10)),
            ):
                by_asset.setdefault(("mf", r["code"]), []).append((r["date"], r["p"]))
        for t in dated:
            prices[t["key"]] = by_asset.get((t["key"][0], t["key"][1]), [])

    series = [p for p in growth_series(dated, prices) if p["date"] >= since]
    return {
        "series": series,
        "excluded_count": len(excluded),
        "excluded_invested": round(sum(p["invested"] for p in excluded.values()), 2),
    }


TOP_COMPANIES = 100


def _load_portfolios(conn, pids: list[str]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    if not pids:
        return out
    for r in conn.execute(
        """
        SELECT portfolio_id, isin, name, holding_type, industry, pct_nav::float AS pct_nav
        FROM fund_portfolio_holdings WHERE portfolio_id = ANY(%s) ORDER BY portfolio_id, position
        """,
        (pids,),
    ):
        out.setdefault(r["portfolio_id"], []).append(r)
    return out


def _attach_links(conn, entries: list[dict]) -> None:
    isins = sorted({e["isin"] for e in entries if e["isin"]})
    links = {r["isin"]: r for r in conn.execute(
        """
        SELECT s.isin, coalesce(c.symbol, s.nse_symbol, s.bse_symbol) AS symbol, c.symbol IS NOT NULL AS tracked
        FROM securities s LEFT JOIN companies c ON c.isin = s.isin WHERE s.isin = ANY(%s)
        """,
        (isins,),
    )} if isins else {}
    for e in entries:
        link = links.get(e["isin"])
        e["symbol"] = link["symbol"] if link else None
        e["tracked"] = bool(link and link["tracked"])


def exposure_breakdown(conn, rows: list[dict], key: str) -> dict:
    entry = _look_through_rows(conn, rows)[0]["breakdown"].get(key) or {"value": 0.0, "holdings": [], "items": []}
    _attach_links(conn, entry["items"])
    return {"key": key, **entry}


def exposure_from_rows(conn, rows: list[dict]) -> dict:
    result, as_of = _look_through_rows(conn, rows)
    result.pop("breakdown")
    top = result["companies"][:TOP_COMPANIES]
    _attach_links(conn, top)
    result["companies_count"] = len(result["companies"])
    result["companies"] = top
    result["as_of"] = sorted(d.isoformat() for d in as_of)
    return result


def _look_through_rows(conn, rows: list[dict]) -> tuple[dict, set]:
    priced = [{**r, "value": r["quantity"] * r["close"]} for r in rows if r["close"] is not None]
    symbols = sorted({r["symbol"] for r in priced if r["kind"] != "mf"})
    codes = sorted({int(r["symbol"]) for r in priced if r["kind"] == "mf"})
    stock_info = {c["symbol"]: c for c in conn.execute(
        """
        SELECT c.symbol, c.isin, s.portfolio_id, s.portfolio_as_of
        FROM companies c LEFT JOIN mf_schemes s ON s.isin = c.isin AND c.kind = 'etf'
        WHERE c.symbol = ANY(%s)
        """,
        (symbols,),
    )} if symbols else {}
    fund_info = {s["code"]: s for s in conn.execute(
        "SELECT code, portfolio_id, portfolio_as_of FROM mf_schemes WHERE code = ANY(%s)", (codes,)
    )} if codes else {}

    items: dict[tuple, dict] = {}
    as_of = set()
    for r in priced:
        if r["kind"] == "mf":
            info = fund_info.get(int(r["symbol"]), {})
            key, kind, isin = ("mf", r["symbol"]), "mf", None
        else:
            info = stock_info.get(r["symbol"], {})
            key, kind, isin = ("st", r["symbol"]), ("etf" if r["kind"] == "etf" else "stock"), info.get("isin")
        if info.get("portfolio_as_of"):
            as_of.add(info["portfolio_as_of"])
        item = items.setdefault(key, {
            "label": r["name"] if kind != "etf" else r["symbol"], "kind": kind, "isin": isin, "value": 0.0,
            "portfolio": info.get("portfolio_id"), "sector": r["sector"], "asset_class": r["asset_class"],
        })
        item["value"] += r["value"]

    portfolios = _load_portfolios(conn, sorted({i["portfolio"] for i in items.values() if i["portfolio"]}))
    stock_isins = [i["isin"] for i in items.values() if i["kind"] == "stock" and i["isin"]]
    industry_by_isin = {r["isin"]: r["industry"] for r in conn.execute(
        """
        SELECT DISTINCT ON (isin) isin, industry FROM fund_portfolio_holdings
        WHERE isin = ANY(%s) AND industry IS NOT NULL ORDER BY isin, as_of DESC
        """,
        (stock_isins,),
    )} if stock_isins else {}

    return look_through(list(items.values()), portfolios, industry_by_isin), as_of
