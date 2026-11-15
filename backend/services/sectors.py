import re

UNCLASSIFIED = "Unclassified"
OVERSEAS = "Overseas"

_MACRO: dict[str, list[str]] = {
    "Financial Services": [
        "Banks", "Capital Markets", "Finance", "Financial Technology (Fintech)", "Insurance", "Financial Services",
        "Financials",
    ],
    "Information Technology": [
        "IT - Software", "IT - Services", "IT - Hardware", "IT Enabled Services", "Software Products",
        "Computers - Software & Consulting", "Computers Hardware & Equipments", "Application Software",
        "IT Consulting & Other Services", "Computer Software: Programming, Data Processing",
        "Computer Software: Prepackaged Software", "Technology", "IT",
    ],
    "Healthcare": [
        "Pharmaceuticals & Biotechnology", "Healthcare Services", "Healthcare Equipment & Supplies", "Pharma",
        "Healthcare",
    ],
    "Consumer Discretionary": [
        "Consumer Durables", "Retailing", "Automobiles", "Auto Components", "Leisure Services", "Textiles & Apparels",
        "Entertainment", "Movies & Entertainment", "Other Consumer Services", "Internet & Direct Marketing Retail",
        "Catalog/Specialty Distribution", "Realty", "Consumer Cyclical", "Automobile",
    ],
    "FMCG": [
        "Diversified FMCG", "Personal Products", "Beverages", "Food Products", "Agricultural Food & Other Products",
        "Cigarettes & Tobacco Products", "Household Products", "Consumer Defensive", "FMCG",
    ],
    "Commodities": [
        "Ferrous Metals", "Non - Ferrous Metals", "Chemicals & Petrochemicals", "Cement & Cement Products",
        "Minerals & Mining", "Metals & Minerals Trading", "Diversified Metals", "Fertilizers & Agrochemicals",
        "Paper, Forest & Jute Products", "Precious Metals", "Basic Materials", "Metals", "Cement",
    ],
    "Energy": ["Oil", "Gas", "Petroleum Products", "Consumable Fuels", "Energy"],
    "Industrials": [
        "Aerospace & Defense", "Electrical Equipment", "Industrial Manufacturing", "Industrial Products", "Construction",
        "Agricultural, Commercial & Construction Vehicles", "Electrodes & Refractories", "Engineering Services",
        "Industrials", "Infrastructure",
    ],
    "Services": ["Transport Services", "Transport Infrastructure", "Commercial Services & Supplies"],
    "Telecommunication": ["Telecom - Services", "Telecom - Equipment & Accessories", "Telecom"],
    "Utilities": ["Power", "Other Utilities", "Utilities"],
    "Diversified": ["Diversified"],
}


def _key(label: str) -> str:
    return re.sub(r"[^a-z0-9]", "", label.lower())


_LOOKUP = {_key(industry): (macro, industry) for macro, industries in _MACRO.items() for industry in industries}


def clean(label: str | None) -> str | None:
    if not label:
        return None
    return re.sub(r"\s*#+\s*$", "", label).strip() or None


def classify(label: str | None) -> tuple[str, str]:
    cleaned = clean(label)
    if cleaned is None:
        return UNCLASSIFIED, UNCLASSIFIED
    return _LOOKUP.get(_key(cleaned), (UNCLASSIFIED, cleaned))
