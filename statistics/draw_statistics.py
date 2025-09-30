import pandas as pd
from collections import defaultdict
from itertools import combinations
import re
import glob 
import os
from pathlib import Path
from tqdm import tqdm



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

def count_combinations(df, k: int):
    tracker = defaultdict(list)
    for _, sub in df.groupby("File"):
        draw_nr = sub["draw_nr"].iat[0]
        if pd.isna(draw_nr):
            # Debug
            fname = sub["File"].iat[0] if "File" in sub.columns else "<unknown>"
            print(f"[DEBUG] Skip group because draw_nr missing – File: {fname}")
            continue  # skip if draw_nr missing
        for _, g in sub.groupby("Group"):
            players = [p for p in g["Name"] if pd.notna(p)]
            if len(players) < k:
                continue
            for combo in combinations(sorted(players), k):
                tracker[combo].append(int(draw_nr))
    return tracker


# Check if there are further, unused combinations
def find_never_together(df, pair_counter):
    player_draws = {p: set(sub["draw_nr"].dropna()) for p, sub in df.groupby("Name")}
    all_players = sorted(df["Name"].dropna().unique())
    all_combos = set(combinations(all_players, 2))
    observed_pairs = set(pair_counter.keys())
    never_together = []
    infos = df.drop_duplicates(subset="Name")[["Name","Seed","Club"]].set_index("Name")

    for a,b in all_combos:
        if player_draws[a] & player_draws[b]:  # were in same draw at least once
            if (a,b) not in observed_pairs:
                seed_a, seed_b = infos.loc[a,"Seed"], infos.loc[b,"Seed"]
                club_a, club_b = infos.loc[a,"Club"], infos.loc[b,"Club"]
                if pd.notna(seed_a) and pd.notna(seed_b): continue
                if pd.notna(club_a) and pd.notna(club_b) and club_a==club_b: continue
                never_together.append({
                    "Player 1": a, "Seed 1": seed_a, "Club 1": club_a,
                    "Player 2": b, "Seed 2": seed_b, "Club 2": club_b,
                    "Count": 0
                })
    return pd.DataFrame(never_together)




input_folder = r"D:\Maturaarbeit\all_MS_U13_parts"
output_folder = r"D:\Maturaarbeit\evaluations"
os.makedirs(output_folder, exist_ok=True)

def natkey(s): 
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', s)]

excel_files = sorted(glob.glob(os.path.join(input_folder, "*.xlsx")), key=natkey)




# Main loop
for file in tqdm(excel_files, desc="Processing files", ncols=100):
    base_name = os.path.basename(file)
    tqdm.write(f"Processing file: {base_name}")

    # Load prepared Excel
    df = pd.read_excel(file)

    # Extract draw number
    df["draw_nr"] = pd.to_numeric(
        df["File"].astype(str)
                .map(lambda p: Path(p).stem)           
                .str.extract(r"(\d+)", expand=False), 
        errors="coerce"
    ).astype("Int64")

    if df["draw_nr"].isna().any():
        raise ValueError(
            f"draw_nr could not be extracet in all files: {file}"
        )

    dist = group_distribution(df)
    pair_counter = count_combinations(df, 2)
    triplet_counter = count_combinations(df, 3)
    quadruplets_counter = count_combinations(df, 4)
    never_df = find_never_together(df, pair_counter)

    dist_chi_test = group_distribution_for_chi_test(df)

    # Convert pairs of 2 into DataFrame
    pair_df = pd.DataFrame([
        {"Player 1": a,
        "Player 2": b,
        "Count": len(draws),
        "Max consecutive": longest_consecutive_run(draws),
        "Draw numbers": format_draw_display(draws)
        }
        for (a, b), draws in pair_counter.items()
    ])
    pair_df = pair_df.sort_values(by="Count", ascending=False)

    # Convert triplets into DataFrame
    triplet_df = pd.DataFrame([
        {
            "Player 1": a,
            "Player 2": b,
            "Player 3": c,
            "Count": len(draws),
            "Max consecutive": longest_consecutive_run(draws),
            "Draw numbers": format_draw_display(draws)
        }
        for (a, b, c), draws in triplet_counter.items()
    ])
    triplet_df = triplet_df.sort_values(by="Count", ascending=False)

    # Convert quadruplets into DataFrame
    quadruplet_df = pd.DataFrame([
        {
            "Player 1": a,
            "Player 2": b,
            "Player 3": c,
            "Player 4": d,
            "Count": len(draws),
            "Max consecutive": longest_consecutive_run(draws),
            "Draw numbers": format_draw_display(draws)

        }
        for (a, b, c, d), draws in quadruplets_counter.items()
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