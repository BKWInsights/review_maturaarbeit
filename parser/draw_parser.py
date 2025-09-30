import pandas as pd
import os
import glob
import re
import pathlib
from tqdm import tqdm
import argparse

# Utility functions

# extract seed from player names
def extract_seed(cell_value):
    if isinstance(cell_value, str):
        match = re.search(r"\[(\d+(?:/\d+)?)\]", cell_value)
        if match:
            return match.group(1)
    return None


def clean_name(cell_value):
    if isinstance(cell_value, str):
        return re.sub(r"\s*\[(\d+(?:/\d+)?)\]\s*$", "", cell_value).strip()
    return cell_value


def natkey(path):
    s = pathlib.Path(path).stem
    parts = re.split(r"(\d+)", s)
    return [int(p) if p.isdigit() else p for p in parts]


def parse_file(file_path, stop_words, sheet_name):
    
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    except Exception as e:
        tqdm.write(f"Error reading {file_path}: {e}")
        return []

    # Find group headers and propagate them down
    df_group = df[0].where(df[0].str.startswith("HE U13 - Group", na=False))
    df["Group"] = df_group.ffill()

    # Extract player rows
    player_rows = df[pd.notna(df["Group"]) & pd.notna(df[3])]
    results = []

    for _, row in player_rows.iterrows():
        raw_name = str(row[3]).strip()
        seed = extract_seed(raw_name)
        name = clean_name(raw_name)
        club = str(row[2]).strip() if pd.notna(row[2]) else "UNKNOWN"

        if name in stop_words:
            continue

        group_letter = row["Group"].split()[-1]
        results.append({
            "File": re.search(r"Ausl_(\d+)", os.path.basename(file_path)).group(1)
                    if re.search(r"Ausl_(\d+)", os.path.basename(file_path)) else os.path.basename(file_path),
            "Group": group_letter,
            "Club": club,
            "Name": name,
            "Seed": seed
        })

    return results


def main():
    # Argument parser
    parser = argparse.ArgumentParser(description="Parse U13 draw Excel files.") 
    parser.add_argument("--input_folder", default=r"D:\Maturaarbeit\Draws\docs", help="Folder with Excel files")
    parser.add_argument("--output_folder", default=r"D:\Maturaarbeit\all_MS_U13_parts_real_names", help="Folder to save output")
    parser.add_argument("--sheet_name", default="HE U13-Hauptfeld", help="Excel sheet name to parse")
    parser.add_argument("--chunk_size", type=int, default=200, help="Number of files per chunk")
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    stop_words = ["WC", "St.", "Standings", "0", "Pl.", "BYE", "Freilos"]

    excel_files = sorted(glob.glob(os.path.join(args.input_folder, "*.xlsx")), key=natkey)

    all_results = []
    chunk_counter = 1
    file_counter = 0

    # Process files with tqdm progress bar
    for file_path in tqdm(excel_files, desc="Processing files", ncols=100):
        file_counter += 1
        if file_counter % 50 == 0 or file_counter == len(excel_files):
            tqdm.write(f"Processing file: {os.path.basename(file_path)}")  # print every 50 files

        file_results = parse_file(file_path, stop_words, args.sheet_name)
        all_results.extend(file_results)

        # Save chunk
        if file_counter % args.chunk_size == 0 or file_counter == len(excel_files):
            df_chunk = pd.DataFrame(all_results)
            out_path = os.path.join(args.output_folder, f"all_MS_U13_part{chunk_counter}.xlsx")
            df_chunk.to_excel(out_path, index=False)
            tqdm.write(f"Saved chunk: {out_path}")
            all_results = []
            chunk_counter += 1

    # Create master file 
    parts = sorted(glob.glob(os.path.join(args.output_folder, "all_MS_U13_part*.xlsx")), key=natkey)
    if parts:
        master_df = pd.concat((pd.read_excel(p) for p in parts), ignore_index=True)
        master_out = os.path.join(args.output_folder, "all_MS_U13.xlsx")
        tqdm.write(f"Master file created: {master_out}")
        master_df.to_excel(master_out, index=False)

    tqdm.write("Done! All chunks and master file saved.")


if __name__ == "__main__":
    main()
