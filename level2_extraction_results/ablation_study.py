#!/usr/bin/env python3
"""
Ablation study for the FINAL Gemma3 drug-indication validation output.

This script DOES NOT call UMLS, DrugCentral, DailyMed, openFDA, or LabeledIn again.
Instead, it uses the frozen evidence columns already stored in:
    all_relations_validation_FINAL_one_step.csv

This is useful for a reproducible component-ablation analysis because every
configuration is evaluated on exactly the same 2,110 relations and the same
evidence snapshot.

Ablation configurations
----------------------
A. Exact DrugCentral string matching only
B. A + accepted UMLS CUI matching in DrugCentral
C. B + same-drug DrugCentral CUI disambiguation
D. C + regulatory / same-SETID evidence
E. D + non-therapeutic safety gate

Output
------
ablation_study_results.csv
"""

from pathlib import Path
import argparse
import pandas as pd


def as_bool(series):
    """Convert common CSV boolean representations safely."""
    if series.dtype == bool:
        return series.fillna(False)
    return (
        series.fillna(False)
        .astype(str)
        .str.strip()
        .str.casefold()
        .isin({"true", "1", "yes", "y"})
    )


def find_input_file(user_path=None):
    """Find the final all-relations CSV in common locations."""
    if user_path:
        p = Path(user_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"Input file not found: {p}")

    here = Path(__file__).resolve().parent
    candidates = [
        here / "all_relations_validation_FINAL_one_step.csv",
        here / "validation_FINAL_one_step" / "all_relations_validation_FINAL_one_step.csv",
        here.parent / "validation_FINAL_one_step" / "all_relations_validation_FINAL_one_step.csv",
    ]

    for p in candidates:
        if p.exists():
            return p

    raise FileNotFoundError(
        "Could not find all_relations_validation_FINAL_one_step.csv.\n"
        "Pass it explicitly with:\n"
        "  python ablation_study.py --input PATH_TO_CSV"
    )


def require_columns(df, columns):
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(
            "The input CSV is missing required columns:\n  - "
            + "\n  - ".join(missing)
        )


def main():
    parser = argparse.ArgumentParser(
        description="Run cumulative component ablation on the frozen FINAL validation evidence."
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Path to all_relations_validation_FINAL_one_step.csv",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory. Default: beside the input CSV in ablation_study/",
    )
    args = parser.parse_args()

    input_file = find_input_file(args.input)
    output_dir = (
        Path(args.output_dir)
        if args.output_dir
        else input_file.parent / "ablation_study"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Input:  {input_file.resolve()}")
    print(f"Output: {output_dir.resolve()}")
    print()

    df = pd.read_csv(input_file)

    required = [
        "relation_id",
        "drugbank_id",
        "drug_name",
        "gemma_disease",
        "validation_status",
        "text_grounded",
        "drugcentral_exact",
        "drugcentral_cui_match",
        "drugcentral_disambiguated_cui_match",
        "regulatory_exact",
        "labeledin_support_same_drug_setid",
        "non_therapeutic_final_flag",
    ]
    require_columns(df, required)

    total = len(df)

    # ------------------------------------------------------------------
    # Evidence flags from the frozen FINAL run
    # ------------------------------------------------------------------
    dc_exact = as_bool(df["drugcentral_exact"])
    dc_cui = as_bool(df["drugcentral_cui_match"])
    dc_disambig = as_bool(df["drugcentral_disambiguated_cui_match"])
    regulatory = as_bool(df["regulatory_exact"])
    labeledin = as_bool(df["labeledin_support_same_drug_setid"])
    nonther = as_bool(df["non_therapeutic_final_flag"])

    # ------------------------------------------------------------------
    # Cumulative ablation configurations
    # ------------------------------------------------------------------
    #
    # A: normalized exact DrugCentral disease string only.
    mask_A = dc_exact

    # B: add concept-level UMLS CUI matching against same-drug DrugCentral.
    mask_B = mask_A | dc_cui

    # C: add same-drug DrugCentral resolution of ambiguous UMLS CUIs.
    mask_C = mask_B | dc_disambig

    # D: add DailyMed/openFDA exact regulatory evidence and same-SETID LabeledIn.
    # In the current final data, LabeledIn does not create a unique additional
    # confirmation beyond the other evidence, but we retain it for completeness.
    mask_D = mask_C | regulatory | labeledin

    # E: full framework. Safety gate has highest priority and removes
    # diagnostic/imaging/non-therapeutic uses from automatic therapeutic insertion.
    mask_E = mask_D & ~nonther

    configs = [
        ("A. Exact string only", mask_A),
        ("B. + UMLS unique CUI", mask_B),
        ("C. + DrugCentral CUI disambiguation", mask_C),
        ("D. + DailyMed/openFDA + same-SETID LabeledIn", mask_D),
        ("E. + non-therapeutic safety gate", mask_E),
    ]

    rows = []
    previous_confirmed = 0

    for i, (name, mask) in enumerate(configs):
        confirmed = int(mask.sum())

        # Before the final safety gate, everything not auto-confirmed is simply
        # "not auto-confirmed at this stage". At the final stage, blocked cases
        # are explicitly counted.
        blocked = (
            int((mask_D & nonther).sum())
            if name.startswith("E.")
            else 0
        )

        review = total - confirmed

        delta = confirmed - previous_confirmed if i > 0 else confirmed

        rows.append({
            "configuration": name,
            "auto_confirmed_n": confirmed,
            "auto_confirmed_pct": round(100 * confirmed / total, 2),
            "not_auto_confirmed_n": review,
            "not_auto_confirmed_pct": round(100 * review / total, 2),
            "non_therapeutic_blocked_n": blocked,
            "net_change_vs_previous_n": delta,
            "net_change_vs_previous_pp": round(100 * delta / total, 2),
        })

        previous_confirmed = confirmed

    ablation = pd.DataFrame(rows)

    # ------------------------------------------------------------------
    # Sanity checks against the published final run
    # ------------------------------------------------------------------
    final_confirmed_expected = 1074
    final_manual_expected = 1036

    final_confirmed_observed = int(mask_E.sum())
    final_manual_observed = total - final_confirmed_observed

    print("=" * 92)
    print("ABLATION RESULTS")
    print("=" * 92)
    print(ablation.to_string(index=False))
    print()

    print("Sanity checks")
    print("-" * 92)
    print(f"Total relations:                 {total}")
    print(f"Final auto-confirmed observed:   {final_confirmed_observed}")
    print(f"Final manual/review observed:    {final_manual_observed}")
    print(f"Expected final confirmed:        {final_confirmed_expected}")
    print(f"Expected final review:           {final_manual_expected}")

    if total != 2110:
        print("WARNING: total relation count is not 2,110.")
    if final_confirmed_observed != final_confirmed_expected:
        print("WARNING: reconstructed final confirmation count is not 1,074.")
    if final_manual_observed != final_manual_expected:
        print("WARNING: reconstructed final review count is not 1,036.")

    # ------------------------------------------------------------------
    # Save ablation table
    # ------------------------------------------------------------------
    ablation_file = output_dir / "ablation_study_results.csv"
    ablation.to_csv(ablation_file, index=False, encoding="utf-8-sig")

    print("Files written")
    print("-" * 92)
    print(ablation_file.resolve())


if __name__ == "__main__":
    main()
