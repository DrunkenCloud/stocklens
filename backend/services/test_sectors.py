from services.sectors import UNCLASSIFIED, classify

CASES = {
    "Banks": ("Financial Services", "Banks"),
    "Capital Markets": ("Financial Services", "Capital Markets"),
    "Financial Technology (Fintech)": ("Financial Services", "Financial Technology (Fintech)"),
    "IT - Software": ("Information Technology", "IT - Software"),
    "It - Software": ("Information Technology", "IT - Software"),
    "IT-Hardware": ("Information Technology", "IT - Hardware"),
    "Computer Software: Prepackaged Software ##": ("Information Technology", "Computer Software: Prepackaged Software"),
    "Pharmaceuticals & Biotechnology": ("Healthcare", "Pharmaceuticals & Biotechnology"),
    "Consumer Durables": ("Consumer Discretionary", "Consumer Durables"),
    "Retailing": ("Consumer Discretionary", "Retailing"),
    "Realty": ("Consumer Discretionary", "Realty"),
    "Movies & Entertainment ##": ("Consumer Discretionary", "Movies & Entertainment"),
    "Diversified Fmcg": ("FMCG", "Diversified FMCG"),
    "Consumer Defensive": ("FMCG", "Consumer Defensive"),
    "Ferrous Metals": ("Commodities", "Ferrous Metals"),
    "Chemicals & Petrochemicals": ("Commodities", "Chemicals & Petrochemicals"),
    "Gas": ("Energy", "Gas"),
    "Aerospace & Defense": ("Industrials", "Aerospace & Defense"),
    "Transport Services": ("Services", "Transport Services"),
    "Telecom - Services": ("Telecommunication", "Telecom - Services"),
    "Power": ("Utilities", "Power"),
    "Diversified": ("Diversified", "Diversified"),
}


def test_every_industry_label_seen_maps_to_a_macro_sector():
    for label, expected in CASES.items():
        assert classify(label) == expected, (label, classify(label))


def test_unknown_or_missing_labels_are_unclassified_not_dropped():
    assert classify("Something New") == (UNCLASSIFIED, "Something New")
    assert classify(None) == (UNCLASSIFIED, UNCLASSIFIED)


if __name__ == "__main__":
    for name, t in list(globals().items()):
        if name.startswith("test_"):
            t()
            print(f"ok  {name}")
