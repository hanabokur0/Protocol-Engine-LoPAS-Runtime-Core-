"""
Protocol Evolution Engine v0.1

Purpose:
Convert UNKNOWN cases into candidate protocols.

This is the learning layer of the Protocol Engine.
"""

import csv
from collections import defaultdict
from pathlib import Path

UNKNOWN_LOG = "unknown_errors.csv"


def load_unknowns(path=UNKNOWN_LOG):
    if not Path(path).exists():
        return []

    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def simple_cluster(records):
    clusters = defaultdict(list)

    for r in records:
        key = f"{r.get('domain')}|{r.get('classification_class')}"
        clusters[key].append(r)

    return clusters


def generate_candidates(min_count=3):
    records = load_unknowns()
    clusters = simple_cluster(records)

    candidates = []

    for key, group in clusters.items():
        if len(group) < min_count:
            continue

        candidates.append({
            "error_type": f"UNK_{hash(key) % 100000}",
            "count": len(group),
            "sample": group[0].get("input_state"),
            "status": "candidate"
        })

    return candidates


if __name__ == "__main__":
    print(generate_candidates())
