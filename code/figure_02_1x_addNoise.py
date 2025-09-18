#!/usr/bin/env python3
"""
Script to duplicate brain render data groups with Gaussian noise.
- Reads dataFrameForBrainRender.csv
- Determines number of regions by unique acronym
- Duplicates ALL regions by a user-specified number of extra groups (new mids)
- For each duplicate, adds Gaussian noise to density, diffuseFluo, energy, intensity
- Source values per region are taken from a chosen input group (mid)
- Noise hyperparameters are user-configurable (global and per-column)
- Saves combined data to dataFrameForBrainRender_addNoise.csv
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Duplicate region groups with Gaussian noise"
    )
    parser.add_argument(
        "--input-file",
        default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData/dataFrameForBrainRender.csv",
        help="Path to input CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--output-file",
        default="/data/SegPNN_CR/_ymz/20250917_Figure02_dataAnalysis/src/analysisData/dataFrameForBrainRender_addNoise.csv",
        help="Path to output CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--num-extra-groups",
        type=int,
        default=10,
        help=(
            "Number of extra groups to add for ALL regions. "
            "For example, 1 means add one new mid for every acronym."
        ),
    )
    parser.add_argument(
        "--source-mid",
        type=int,
        default=None,
        help=(
            "Existing mid to use as the source values for all regions. "
            "If not provided, the smallest existing mid per acronym will be used."
        ),
    )
    parser.add_argument(
        "--noise-std",
        type=float,
        default=0.1,
        help="Global Gaussian noise std applied multiplicatively to all value columns (default: 0.01)",
    )
    parser.add_argument(
        "--std-density",
        type=float,
        default=None,
        help="Override std for density (default: use --noise-std)",
    )
    parser.add_argument(
        "--std-diffuseFluo",
        type=float,
        default=None,
        help="Override std for diffuseFluo (default: use --noise-std)",
    )
    parser.add_argument(
        "--std-energy",
        type=float,
        default=None,
        help="Override std for energy (default: use --noise-std)",
    )
    parser.add_argument(
        "--std-intensity",
        type=float,
        default=None,
        help="Override std for intensity (default: use --noise-std)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    return parser.parse_args()


def add_gaussian_noise(df: pd.DataFrame, std_map: dict) -> pd.DataFrame:
    noisy = df.copy()
    for col, std in std_map.items():
        if col in noisy.columns and std is not None and std > 0:
            noise = np.random.normal(loc=0.0, scale=std, size=len(noisy))
            noisy[col] = noisy[col] * (1.0 + noise)
    return noisy


def main() -> None:
    args = parse_args()

    np.random.seed(args.seed)

    input_file = args.input_file
    output_file = args.output_file

    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    print(f"Reading input: {input_file}")
    df = pd.read_csv(input_file)

    required_cols = {"group", "region", "density", "diffuseFluo", "energy", "intensity"}
    missing = required_cols.difference(df.columns)
    if missing:
        print(f"Error: Missing required columns in input: {sorted(missing)}")
        sys.exit(1)

    # Determine unique regions by region only
    num_regions = df["region"].nunique()
    unique_regions = sorted(df["region"].unique())
    unique_groups = sorted(df["group"].unique())
    print(f"Found {num_regions} regions based on unique region values")
    print(f"Existing groups: {unique_groups}")

    # Build std map with per-column overrides
    std_map = {
        "density": args.std_density if args.std_density is not None else args.noise_std,
        "diffuseFluo": args.std_diffuseFluo if args.std_diffuseFluo is not None else args.noise_std,
        "energy": args.std_energy if args.std_energy is not None else args.noise_std,
        "intensity": args.std_intensity if args.std_intensity is not None else args.noise_std,
    }

    # Number of new groups to add
    num_extra = max(0, int(args.num_extra_groups))
    if num_extra == 0:
        print("No extra groups requested; copying input to output.")
        df.to_csv(output_file, index=False)
        print(f"Saved: {output_file}")
        return

    # Choose source group per region
    source_group_global = args.source_mid
    if source_group_global is not None and source_group_global not in set(unique_groups):
        print(f"Warning: --source-mid {source_group_global} not found in data; will fallback per region.")

    # For each region, pick source row from the chosen group; if not present, fallback to the smallest group for that region
    base_rows = []
    for acr in unique_regions:
        rows = df[df["region"] == acr]
        row = None
        if source_group_global is not None:
            cand = rows[rows["group"] == source_group_global]
            if len(cand) > 0:
                row = cand.iloc[0]
        if row is None:
            # fallback: use the smallest group available for this region
            cand = rows.sort_values("group").iloc[0]
            row = cand
        base_rows.append(row)
    base_df = pd.DataFrame(base_rows).reset_index(drop=True)

    # Next group to assign
    next_group = int(df["group"].max()) + 1 if len(df) > 0 else 1

    all_parts = [df]

    print(
        f"Generating {num_extra} extra group(s) for each of the {num_regions} regions using source group: "
        f"{source_group_global if source_group_global is not None else 'per-region smallest group'} with stds {std_map}"
    )

    value_cols = ["density", "diffuseFluo", "energy", "intensity"]

    for extra_idx in range(1, num_extra + 1):
        # Take the base_df (one row per region), apply noise to value columns, and assign a new group
        noisy_chunk = add_gaussian_noise(base_df[value_cols], std_map)
        new_chunk = base_df.copy()
        for col in value_cols:
            new_chunk[col] = noisy_chunk[col].values
        new_chunk["group"] = next_group
        all_parts.append(new_chunk)
        print(f"  Added extra group {extra_idx} as group {next_group}: rows={len(new_chunk)}")
        next_group += 1

    df_out = pd.concat(all_parts, ignore_index=True)

    # Save
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_out.to_csv(output_file, index=False)

    # Summary
    print("Done.")
    print(f"Input rows: {len(df)}")
    print(f"Output rows: {len(df_out)}")
    print(f"Unique groups in output: {df_out['group'].nunique()}")
    print(f"Regions (unique regions) in output: {df_out['region'].nunique()}")


if __name__ == "__main__":
    main()
