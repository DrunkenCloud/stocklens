import datetime as dt
import re

from pipeline.securities import etf_asset_class

_CATEGORY = re.compile(r"^(?:Open|Close|Interval)[^(]*\((.*)\)\s*$")


def category_asset_class(category: str, name: str) -> str:
    c = category.lower()
    by_name = etf_asset_class(name)
    if by_name in ("gold", "silver"):
        return by_name
    if "gold" in c:
        return "gold"
    if "debt" in c or "gilt" in c or c.startswith("income"):
        return "debt"
    if "hybrid" in c or "solution oriented" in c or "life cycle" in c or "children" in c or "retirement" in c:
        return "hybrid"
    if "equity" in c or "elss" in c or "index fund" in c or "overseas" in c:
        return "equity"
    if "etf" in c or "fof" in c or "fund of funds" in c:
        return by_name
    return "other"


def _plan(value: str) -> str | None:
    value = value.strip()
    value = value[: -len("Plan")].strip() if value.lower().endswith("plan") else value
    return value.title() if value else None


def _option(value: str) -> str | None:
    upper = value.strip().upper()
    if not upper:
        return None
    if "GROWTH" in upper:
        return "Growth"
    if "IDCW" in upper or "DIVIDEND" in upper:
        return "IDCW"
    return value.strip()


def parse_navall(text: str) -> list[dict]:
    rows, category, amc = [], "", ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("Scheme Code;"):
            continue
        if ";" not in line:
            match = _CATEGORY.match(line)
            if match:
                category = match.group(1).strip()
            else:
                amc = line
            continue
        parts = line.split(";")
        if len(parts) < 8:
            continue
        code, isin, isin_reinvest, name, plan, option, nav, date = (p.strip() for p in parts[:8])
        try:
            nav_value = float(nav)
            nav_date = dt.datetime.strptime(date, "%d-%b-%Y").date()
            code_value = int(code)
        except ValueError:
            continue
        rows.append({
            "code": code_value,
            "name": name,
            "amc": amc,
            "category": category,
            "plan": _plan(plan),
            "option": _option(option),
            "isin": isin if isin not in ("", "-") else None,
            "isin_reinvest": isin_reinvest if isin_reinvest not in ("", "-") else None,
            "nav": nav_value,
            "nav_date": nav_date,
            "asset_class": category_asset_class(category, name),
        })
    return rows
