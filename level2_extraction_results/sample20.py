#!/usr/bin/env python3
"""
Draw the random sample of 20 automatically confirmed relations used for the
manual precision check in the paper.

Simple random sampling without replacement from the 1,074 relations with
add_to_kg == "YES" (pandas DataFrame.sample, random_state = 42).

Usage:
    python sample20.py --input drug_disease_relations_validated_SHAREABLE.csv

Output:
    confirmed_sample_20.csv  (relation IDs, drug, extracted disease, status)
"""

import argparse
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--input", default="drug_disease_relations_validated_SHAREABLE.csv")
parser.add_argument("--output", default="confirmed_sample_20.csv")
args = parser.parse_args()

df = pd.read_csv(args.input)
confirmed = df[df["add_to_kg"] == "YES"]
assert len(confirmed) == 1074, f"Expected 1,074 confirmed relations, found {len(confirmed)}"

sample = confirmed.sample(n=20, random_state=42)
cols = ["relation_id", "drugbank_id", "drug_name", "gemma_disease", "validation_status"]
sample[cols].to_csv(args.output, index=False)

print(sample[cols].to_string(index=False))
print(f"\nSaved: {args.output}")
