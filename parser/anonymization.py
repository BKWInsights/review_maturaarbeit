import pandas as pd
import glob, os

# folder paths
input_folder = r"D:\Maturaarbeit\all_MS_U13_parts_real_names"
output_folder = r"D:\Maturaarbeit\all_MS_U13_parts"
os.makedirs(output_folder, exist_ok=True)

# mapping dicts
club_map = {}
player_map = {}
club_counter = 1
player_counter = 1

# main loop
for file in glob.glob(os.path.join(input_folder, "*.xlsx")):
    df = pd.read_excel(file)

    # Clubs anonymisieren
    for club in df['Club'].unique():
        if club not in club_map:
            club_map[club] = f"Club{club_counter}"
            club_counter += 1
    df['Club'] = df['Club'].map(club_map)

    # Spielernamen anonymisieren
    for player in df['Name'].unique():
        if player not in player_map:
            player_map[player] = f"Player{player_counter}"
            player_counter += 1
    df['Name'] = df['Name'].map(player_map)

    # save
    filename = os.path.basename(file)
    df.to_excel(os.path.join(output_folder, filename), index=False)

print("Finished.")
