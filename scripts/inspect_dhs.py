"""One-off inspector: list relevant indicators across every DHS CSV."""
from pathlib import Path
import pandas as pd
import sys

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "dhs_subnational"

# Keywords to spot indicators relevant to our features.
TOPICS = {
    "stunting":      ["stunt"],
    "wasting":       ["wast"],
    "underweight":   ["underweight"],
    "anemia":        ["anemia", "anaemia"],
    "education":     ["education", "schooling", "literacy", "literate"],
    "water":         ["water", "improved drinking", "drinking water"],
    "sanitation":    ["sanitation", "toilet"],
    "wealth":        ["wealth", "poorest", "poor", "richest"],
    "antenatal":     ["antenatal", "anc"],
    "skilled birth": ["skilled provider", "skilled birth", "skilled attend"],
    "insurance":     ["insurance"],
    "malaria":       ["malaria", "parasit"],
    "facilities":    ["facility", "facilities", "providers", "health worker"],
    "fertility":     ["total fertility", "fertility rate", "tfr"],
    "urban":         ["urban", "place of residence"],
}

def main() -> None:
    counts = {t: [] for t in TOPICS}
    for csv in sorted(RAW.glob("*.csv")):
        try:
            df = pd.read_csv(csv, encoding="utf-8", encoding_errors="replace",
                              usecols=["Indicator", "CharacteristicCategory", "SurveyYear"])
        except Exception:
            continue
        if "Indicator" not in df.columns:
            continue
        for ind in df["Indicator"].dropna().unique():
            low = ind.lower()
            for topic, kws in TOPICS.items():
                if any(kw in low for kw in kws):
                    counts[topic].append((csv.name, ind))
                    break

    for topic, hits in counts.items():
        if not hits: continue
        print(f"\n=== {topic.upper()} ===")
        seen = set()
        for csv, ind in hits:
            key = (csv, ind)
            if key in seen: continue
            seen.add(key)
            print(f"  [{csv:55s}] {ind}")


if __name__ == "__main__":
    main()
