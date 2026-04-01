import argparse
from pathlib import Path
import pandas as pd

def collect_csvs(folder: Path):
    return sorted(folder.glob("*.csv"))

def merge_csvs(csv_files, output_file: Path):
    if not csv_files:
        raise FileNotFoundError("No CSV files found to merge.")
    
    frames = []
    for f in csv_files:
        print(f"[INFO] Reading {f}")
        frames.append(pd.read_csv(f))

    merged = pd.concat(frames, ignore_index=True)
    merged.to_csv(output_file, index=False)

    print(f"[INFO] Merged rows: {len(merged)}")
    print(f"[INFO] Output written to: {output_file}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fra-dir", required=True)
    parser.add_argument("--output-file", required=True)
    args = parser.parse_args()

    fra_dir = Path(args.fra_dir)
    output_file = Path(args.output_file)

    csv_files = collect_csvs(fra_dir)
    print(f"[INFO] Found {len(csv_files)} CSV files")

    merge_csvs(csv_files, output_file)

if __name__ == "__main__":
    main()