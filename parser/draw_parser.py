import pandas as pd
import os
import glob
import re


def extract_seed(cell_value):
    if isinstance(cell_value, str):
        match = re.search(r"\[(\d+(?:/\d+)?)\]", cell_value)
        if match:
            return match.group(1)
        return None

def extract_number(filename):
    match = re.search(r"Ausl_(\d+)", filename)
    return match.group(1) if match else filename

# configure paths
folder_path = r"D:\Maturaarbeit\Draws\docs"
output_folder = r"D:\Maturaarbeit"
os.makedirs(output_folder, exist_ok=True)

# Find all Excel files in the folder
excel_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
excel_files = sorted(excel_files, key=lambda x: int(extract_number(os.path.basename(x))))

# Results
all_results = []
chunk_size = 200 # save file after this many draws
chunk_counter = 1 # for file name
file_counter = 0 

for file_path in excel_files:
    file_counter += 1
    print(f"Processing file: {os.path.basename(file_path)}")

    try:
        df = pd.read_excel(file_path, sheet_name="HE U13-Hauptfeld", header=None)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        continue

    # Extract only group blocks
    groups = {}
    current_group = None
    for i, row in df.iterrows():

        if isinstance(row[0], str) and row[0].startswith("HE U13 - Group"):
            current_group = row[0].split()[-1]  # A, B, C, D
            groups[current_group] = []
        elif current_group and pd.notna(row[3]) and str(row[3]).strip() != "" and str(row[3]).strip() != "0":
            name = str(row[3]).strip()

            # Skip unwanted entries
            if name in ["WC", "St.", "Standings", "0", "Pl."]:
                continue

            # Get and detect seed from column 3
            seed = None
            if len(row) > 3 and pd.notna(row[3]):
                seed = extract_seed(str(row[3]))

            # Extract club
            club = str(row[2]).strip() if pd.notna(row[2]) else None

            groups[current_group].append({
                "Club": club,
                "Name": name,
                "Seed": seed 
            })

    # Save results of this file
    results = []
    for group, players in groups.items():
        for p in players:
            results.append({
                "File": extract_number(os.path.basename(file_path)),
                "Group": group,
                "Club": p["Club"],
                "Name": p["Name"],
                "Seed": p["Seed"],
            })

    all_results.extend(results)

    # save File every chunk_size
    if file_counter % chunk_size == 0 or file_counter == len(excel_files):
        df_chunk = pd.DataFrame(all_results)
        out_path = os.path.join(output_folder, f"all_MS_U13_part{chunk_counter}.xlsx")
        df_chunk.to_excel(out_path, index=False)
        print(f"Saved {out_path}")
        all_results = []  # empty list for next round
        chunk_counter += 1

print("Done! All chunks have been saved.")