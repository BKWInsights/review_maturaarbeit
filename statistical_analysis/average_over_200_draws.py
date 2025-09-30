import pandas as pd
import glob
import os

# folder path
folder_path = r"D:\Maturaarbeit\analysis_results"

# find all Excel files
files = glob.glob(os.path.join(folder_path, "analysis_evaluation_all_MS_U13_part*.xlsx"))

print(f"{len(files)} Files found.")

# read files
dfs = []
for f in files:
    df = pd.read_excel(f)
    df["source_file"] = os.path.basename(f)  
    dfs.append(df)

# join
data = pd.concat(dfs, ignore_index=True)

print("Columns:", data.columns.tolist())
print("Shape:", data.shape)

# Overall average across all numerical columnsSpalten
mean_values = data.mean(numeric_only=True)
mean_df = mean_values.to_frame(name="Average")

# average per player and group
mean_per_player_group = (
    data.groupby(["Player", "Group"])
        .mean(numeric_only=True)
        .reset_index()
)

# average per player over all groups
mean_per_player = (
    data.groupby("Player")
        .mean(numeric_only=True)
        .reset_index()
)

# Create Excel file
output_path = r"D:\Maturaarbeit\analysis_results\analysis_summary.xlsx"
with pd.ExcelWriter(output_path) as writer:
    data.to_excel(writer, sheet_name="All Data", index=False)
    mean_df.to_excel(writer, sheet_name="Overall average", index=True)
    mean_per_player_group.to_excel(writer, sheet_name="player_group", index=False)
    mean_per_player.to_excel(writer, sheet_name="player", index=False)

print(f"Results saved under: {output_path}")
