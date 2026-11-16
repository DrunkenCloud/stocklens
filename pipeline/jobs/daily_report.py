import datetime as dt
import html as htmllib
import json
import os
import smtplib
import sys
import urllib.request
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from pipeline.db import connect
from pipeline.run import SKIPPED_EXIT

API = os.environ.get("STOCKLENS_API", "http://127.0.0.1:8000/api")
SITE = "https://investlens.duckdns.org"
SOON_DAYS = 14
TOP = 3
GAIN, LOSS = "#15803d", "#b91c1c"


def inr(x: float, sign: bool = False) -> str:
    n = round(abs(x))
    s = str(n)
    if len(s) > 3:
        head, groups = s[:-3], []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        s = ",".join(([head] if head else []) + groups) + "," + s[-3:]
    prefix = "−" if x < 0 and n else ("+" if sign and n else "")
    return f"{prefix}₹{s}"


def pct(x: float | None) -> str:
    if x is None:
        return "–"
    return f"{'+' if x > 0 else '−' if x < 0 else ''}{abs(x):.1f}%"


def should_send(status: dict, today: dt.date, sent_today: bool) -> bool:
    return status.get("prices_as_of") == today.isoformat() and not sent_today


def _day(iso: str) -> str:
    return dt.date.fromisoformat(iso).strftime("%-d %b")


def sections(data: dict, today: dt.date) -> tuple[str, list[tuple[str, list[tuple[str, str, float]]]]]:
    totals = data["portfolio"]["totals"]
    indices = data["benchmarks"]["indices"]
    headline = f"{inr(totals['value'])}   {inr(totals['day_change'], sign=True)} ({pct(totals['day_change_pct'])})"
    out = []

    market = [(" · ".join(f"{i['name']} {pct(i['day_pct'])}" for i in indices[:2]), "", 0)]
    if totals.get("xirr") is not None:
        line = f"Your XIRR {pct(totals['xirr']).lstrip('+')}"
        if indices and indices[0].get("xirr") is not None:
            line += f" · same money in {indices[0]['name']}: XIRR {pct(indices[0]['xirr']).lstrip('+')}"
        market.append((line, "", 0))
    out.append(("Market", market))

    today_rows = [x for x in data["portfolio"]["holdings"]
                  if x["kind"] != "mf" and x.get("price_date") == today.isoformat() and x.get("day_change")]
    up = sorted((x for x in today_rows if x["day_change"] > 0), key=lambda x: -x["day_change"])[:TOP]
    down = sorted((x for x in today_rows if x["day_change"] < 0), key=lambda x: x["day_change"])[:TOP]
    moves = [(x["name"], f"{inr(x['day_change'], sign=True)} ({pct(x['day_change_pct'])})", x["day_change"]) for x in up + down]
    if moves:
        out.append(("Today's biggest moves (stocks and ETFs; funds at last NAV)", moves))

    soon = [u for u in data["tax"]["upcoming"] if u["days_left"] <= SOON_DAYS]
    if soon:
        out.append((f"Turning long-term in the next {SOON_DAYS} days", [
            (f"{u['name']} ({u['broker']}) on {_day(u['long_term_on'])}", f"gain {inr(u['gain'], sign=True)}" if u.get("gain") is not None else "", 0)
            for u in soon
        ]))

    movers = data["insights"]["movers"]
    month = [(m["name"], inr(m["change"], sign=True), m["change"]) for m in movers["up"][:TOP] + movers["down"][:TOP]]
    if month:
        out.append(("This month so far", month))
    return headline, out


def render(data: dict, today: dt.date) -> tuple[str, str, str]:
    totals = data["portfolio"]["totals"]
    subject = f"StockLens · {today.strftime('%a %-d %b')} · {inr(totals['value'])} ({pct(totals['day_change_pct'])})"
    headline, parts = sections(data, today)

    text = [headline, ""]
    for title, rows in parts:
        text.append(title)
        text += [f"  {label}  {amount}".rstrip() for label, amount, _ in rows]
        text.append("")
    text.append(SITE)

    def colour(v: float) -> str:
        return GAIN if v > 0 else LOSS if v < 0 else "inherit"

    esc = htmllib.escape
    body = [f'<p style="font-size:20px;margin:0 0 16px">{esc(headline)}</p>']
    for title, rows in parts:
        body.append(f'<p style="margin:16px 0 4px;color:#6b7280;font-size:12px;text-transform:uppercase">{esc(title)}</p><table style="border-collapse:collapse">')
        for label, amount, v in rows:
            body.append(f'<tr><td style="padding:2px 16px 2px 0">{esc(label)}</td>'
                        f'<td style="padding:2px 0;text-align:right;color:{colour(v)}">{esc(amount)}</td></tr>')
        body.append("</table>")
    body.append(f'<p style="margin-top:20px"><a href="{SITE}">Open StockLens</a></p>')
    html = ('<div style="font-family:system-ui,sans-serif;font-size:14px;color:#111827;font-variant-numeric:tabular-nums">'
            + "".join(body) + "</div>")
    return subject, "\n".join(text), html


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{API}{path}", timeout=60) as r:
        return json.load(r)


def _sent_today(today: dt.date) -> bool:
    with connect() as conn:
        return conn.execute(
            """
            SELECT 1 FROM job_runs WHERE job = 'daily_report' AND status = 'done' AND trigger = 'cron'
            AND (started_at AT TIME ZONE 'Asia/Kolkata')::date = %s LIMIT 1
            """,
            (today,),
        ).fetchone() is not None


def send(subject: str, text: str, html: str) -> None:
    user = os.environ["GMAIL"]
    msg = EmailMessage()
    msg["From"] = f"StockLens <{user}>"
    msg["To"] = user
    msg["Subject"] = subject
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(user, os.environ["GMAIL_PASSWORD"].replace(" ", ""))
        s.send_message(msg)


def main() -> None:
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
    status = _get("/status")
    if "--force" not in sys.argv and not should_send(status, today, _sent_today(today)):
        print(f"skipped: no new prices for {today} or already sent today")
        sys.exit(SKIPPED_EXIT)
    data = {
        "status": status,
        "portfolio": _get("/portfolio?scope=all"),
        "benchmarks": _get("/portfolio/benchmarks"),
        "tax": _get("/tax"),
        "insights": _get("/portfolio/insights"),
    }
    subject, text, html = render(data, today)
    send(subject, text, html)
    print(f"sent: {subject}")


if __name__ == "__main__":
    main()
