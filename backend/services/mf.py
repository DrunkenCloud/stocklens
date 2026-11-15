import datetime as dt

EPSILON = 1e-6


def mf_positions(transactions: list[dict]) -> dict[tuple[int, str], dict]:
    ordered = sorted(transactions, key=lambda t: (t["date"] or dt.date.min, t["created_at"]))
    book: dict[tuple[int, str], dict] = {}
    for t in ordered:
        key = (t["code"], t["broker"])
        pos = book.setdefault(key, {"units": 0.0, "invested": 0.0, "realized": 0.0})
        units, amount = float(t["units"]), float(t["amount"])
        if t["kind"] == "buy":
            pos["units"] += units
            pos["invested"] += amount
            continue
        if units > pos["units"] + EPSILON:
            raise ValueError(f"sell of {units} units is more units than held ({pos['units']:.4f}) at {t['broker']}")
        cost = pos["invested"] * units / pos["units"]
        pos["invested"] -= cost
        pos["realized"] += amount - cost
        pos["units"] -= units
    return {
        key: {k: round(v, 6) for k, v in pos.items()}
        for key, pos in book.items()
        if pos["units"] > EPSILON
    }
