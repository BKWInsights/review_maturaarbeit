import pandas as pd
from collections import defaultdict
from itertools import combinations
import re
import glob 
import os



def longest_consecutive_run(nums):
    """nums: list of ints or None"""
    nums = sorted(set(int(n) for n in nums if pd.notna(n)))
    if not nums:
        return 0
    longest = current = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1] + 1:
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest

def format_draw_display(nums):
    nums = sorted(set(int(n) for n in nums if pd.notna(n)))
    return ", ".join(f"Draw_{n}" for n in nums)

# Distribution across groups
def group_distribution(df):
    dist = df.groupby(["Group", "Name"]).size().unstack(fill_value=0)
    return dist

def group_distribution_for_chi_test(df):
    return df.groupby(["Group", "Name", "Seed", "Club"], dropna=False).size().reset_index(name="Count")

# Pairs of 2
def count_pairs(df):
    pair_counter = defaultdict(list)

    for file_value, sub in df.groupby("File"):
        draw_nr = sub["draw_nr"].iat[0]
        if pd.isna(draw_nr):
            draw_nr = str(file_value)
        for _, group_df in sub.groupby("Group"):
            players = list(group_df["Name"])
            for combo in combinations(players, 2):
                pair = tuple(sorted(combo))
                pair_counter[pair].append(draw_nr)
    
    return pair_counter

# Check if there are further, unused combinations
def find_unpaired(df, pair_counter):
    all_players = sorted(df["Name"].unique())
    all_combos = set(combinations(all_players, 2))
    never_together = all_combos - set(pair_counter.keys())

    infos = df.drop_duplicates(subset="Name")[["Name", "Seed", "Club"]].set_index("Name")

    rows = []
    for a, b in never_together:
        seed_a = infos.loc[a, "Seed"]
        seed_b = infos.loc[b, "Seed"]
        club_a = infos.loc[a, "Club"]
        club_b = infos.loc[b, "Club"]

        # If both are seeded or from the same club -> remove
        if pd.notna(seed_a) and pd.notna(seed_b):
            continue
        if pd.notna(club_a) and pd.notna(club_b) and club_a == club_b:
            continue

        rows.append({
            "Player 1": a,
            "Seed 1": infos.loc[a, "Seed"],
            "Club 1": infos.loc[a, "Club"],
            "Player 2": b,
            "Seed 2": infos.loc[b, "Seed"],
            "Club 2": infos.loc[b, "Club"],
            "Count": pair_counter.get((a, b), 0)
        })
    
    return pd.DataFrame(rows)

# Triplets (3)
def count_triplets(df):
    triplet_tracker = defaultdict(list)

    for file_value, sub in df.groupby("File"):
        draw_nr = sub["draw_nr"].iat[0]
        if pd.isna(draw_nr):
            draw_nr = str(file_value)
        for _, group_df in sub.groupby("Group"):
            players = list(group_df["Name"])
            for combo in combinations(players, 3):
                triple = tuple(sorted(combo))
                triplet_tracker[triple].append(draw_nr)

    return triplet_tracker

# Quadruplets (4)
def count_quadruplets(df):
    quadruplets_tracker = defaultdict(list)

    for file_value, sub in df.groupby("File"):
        draw_nr = sub["draw_nr"].iat[0]
        if pd.isna(draw_nr):
            draw_nr = str(file_value)
        for _, group_df in sub.groupby("Group"):
            players = list(group_df["Name"])
            for combo in combinations(players, 4):
                quadruplets = tuple(sorted(combo))
                quadruplets_tracker[quadruplets].append(draw_nr)

    return quadruplets_tracker


input_folder = r"D:\Maturaarbeit\all_MS_U13_parts"
output_folder = r"D:\Maturaarbeit\evaluations"
os.makedirs(output_folder, exist_ok=True)

excel_files = glob.glob(os.path.join(input_folder, "*.xlsx"))

for file in excel_files:
    print(f"Processing file: {os.path.basename(file)}")

    # Load prepared Excel
    df = pd.read_excel(file)

     # Extract draw number
    df["file_str"] = df["File"].astype(str)
    df["draw_nr"] = pd.to_numeric(
        df["file_str"].str.extract(r"Ausl_(\d+)_", expand=False),
        errors="coerce"
    ).astype("Int64")

    dist = group_distribution(df)
    pair_counter = count_pairs(df)
    never_df = find_unpaired(df, pair_counter)
    triplet_counter = count_triplets(df)
    quadruplets_counter = count_quadruplets(df)
    dist_chi_test = group_distribution_for_chi_test(df)

    # Convert pairs of 2 into DataFrame
    pair_df = pd.DataFrame([
        {"Player 1": a,
        "Player 2": b,
        "Count": len(files),
        "Max consecutive": longest_consecutive_run(files),
        "Draw numbers": format_draw_display(files)
        }
        for (a, b), files in pair_counter.items()
    ])
    pair_df = pair_df.sort_values(by="Count", ascending=False)

    # Convert triplets into DataFrame
    triplet_df = pd.DataFrame([
        {
            "Player 1": a,
            "Player 2": b,
            "Player 3": c,
            "Count": len(files),
            "Max consecutive": longest_consecutive_run(files),
            "Draw numbers": format_draw_display(files)
        }
        for (a, b, c), files in triplet_counter.items()
    ])
    triplet_df = triplet_df.sort_values(by="Count", ascending=False)

    # Convert quadruplets into DataFrame
    quadruplet_df = pd.DataFrame([
        {
            "Player 1": a,
            "Player 2": b,
            "Player 3": c,
            "Player 4": d,
            "Count": len(files),
            "Max consecutive": longest_consecutive_run(files),
            "Draw numbers": ", ".join(map(str, set(files)))
        }
        for (a, b, c, d), files in quadruplets_counter.items()
    ])
    quadruplet_df = quadruplet_df.sort_values(by="Count", ascending=False)

    base_name = os.path.splitext(os.path.basename(file))[0]
    output_file = os.path.join(output_folder, f"evaluation_{base_name}.xlsx")

    # Create new Excel
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        dist.to_excel(writer, sheet_name="Group distribution")
        pair_df.to_excel(writer, sheet_name="Pairs of 2", index=False)
        never_df.to_excel(writer, sheet_name="Never together", index=False)
        triplet_df.to_excel(writer, sheet_name="Triplets", index=False)
        quadruplet_df.to_excel(writer, sheet_name="Quadruplets", index=False)
        dist_chi_test.to_excel(writer, sheet_name="Chi2 preparation", index=False)

print("Done")