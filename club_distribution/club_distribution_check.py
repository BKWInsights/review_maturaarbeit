import pandas as pd
import os


output_folder = os.getcwd()
# Read Excel file
df = pd.read_excel(r"D:\Maturaarbeit\all_MS_U13_parts\all_MS_U13.xlsx")

# Normalize group names
df['Group'] = df['Group'].str.strip().str.upper()

# Mapping: Groups -> Position in 16-player knockout bracket
group_to_pos = {
    'A': 1, 'B': 16, 'C': 12, 'D': 5,
    'E': 7, 'F': 10, 'G': 3, 'H': 14,
    'I': 9, 'J': 8, 'K': 13
}
df['Pos'] = df['Group'].map(group_to_pos)

# Players without assigned position
missing_pos = df[df['Pos'].isna()]
missing_pos.to_excel(os.path.join(output_folder, "missing_position.xlsx"), index=False)

# Quarter and half assignment
def get_quarter(pos):
    if 1 <= pos <= 4: return 'Q1'
    elif 5 <= pos <= 8: return 'Q2'
    elif 9 <= pos <= 12: return 'Q3'
    elif 13 <= pos <= 16: return 'Q4'
    else: return None

def get_half(pos):
    if 1 <= pos <= 8: return 'top'
    elif 9 <= pos <= 16: return 'bottom'
    else: return None

df['Quarter'] = df['Pos'].apply(get_quarter)
df['Half'] = df['Pos'].apply(get_half)

def half_conflict_func(group):
    if len(group) < 2:
        return False
    counts = group['Half'].value_counts()
    valid_halves = group['Half'].notna().sum()   
    # Conflict: if all players are in the same half or if there are ≥8 players in the same half.
    return valid_halves == len(group) and (
        counts.max() == valid_halves or counts.max() >= 8
    )

def quarter_conflict_func(group):
    if len(group) < 2:
        return False
    counts = group['Quarter'].value_counts()
    valid_quarters = group['Quarter'].notna().sum()
    # Conflict: if all players are in the same quarter or if ≥4 players are in the same quarter.
    return valid_quarters == len(group) and (
        counts.max() == valid_quarters or counts.max() >= 4
    )


conflicts = df.groupby(['File', 'Club']).agg(
    player_count=('Name', 'count')
)
conflicts['half_conflict'] = df.groupby(['File', 'Club']).apply(half_conflict_func, include_groups=False).values
conflicts['quarter_conflict'] = df.groupby(['File', 'Club']).apply(quarter_conflict_func, include_groups=False).values


# Near Misses (60%)
near_misses = []

for (file, club), group in df.groupby(['File', 'Club']):
    if len(group) > 1:
        total_players = len(group)
        half_counts = group['Half'].value_counts()
        quarter_counts = group['Quarter'].value_counts()

        for half, count in half_counts.items():
            if count / total_players >= 0.6 and count < total_players and count < 8:
                near_misses.append({
                    'File': file,
                    'Club': club,
                    'Type': 'Half',
                    'Section': half,
                    'Count': count,
                    'Total_players': total_players
                })

        for quarter, count in quarter_counts.items():
            if count / total_players >= 0.6 and count < total_players and count < 4:
                near_misses.append({
                    'File': file,
                    'Club': club,
                    'Type': 'Quarter',
                    'Section': quarter,
                    'Count': count,
                    'Total_players': total_players
                })

near_misses_df = pd.DataFrame(near_misses)
near_misses_df.to_excel(os.path.join(output_folder, "near_misses.xlsx"), index=False)



# Save summary 
conflicts.to_excel(os.path.join(output_folder, "club_conflicts_summary.xlsx"))



# total conflict count
total_half_conflicts = conflicts['half_conflict'].sum()
total_quarter_conflicts = conflicts['quarter_conflict'].sum()

print("Konflikt-Übersicht")
print(f"Gesamtanzahl Halbkonflikte:   {total_half_conflicts}")
print(f"Gesamtanzahl Viertelkonflikte:{total_quarter_conflicts}")

# Overview
print("Conflict Overview")
print(f"Total number of half conflicts:    {total_half_conflicts}")
print(f"Total number of quarter conflicts: {total_quarter_conflicts}")
print()


# Near Misses Overview
near_half = near_misses_df[near_misses_df['Type'] == 'Half']
near_quarter = near_misses_df[near_misses_df['Type'] == 'Quarter']


total_events_half = len(near_half)                
total_players_involved_half = near_half['Count'].sum()  
total_events_quarter = len(near_quarter)
total_players_involved_quarter = near_quarter['Count'].sum()

print("Near Misses Summary")
print(f"Near Miss Events (Half): {total_events_half}")
print(f"Sum of players involved in Half Near Misses: {total_players_involved_half}")
print(f"Average players per Half-Near-Miss event: {near_half['Count'].mean():.2f}\n")

print(f"Near Miss Events (Quarter): {total_events_quarter}")
print(f"Sum of players involved in Quarter Near Misses: {total_players_involved_quarter}")
print(f"Average players per Quarter-Near-Miss event: {near_quarter['Count'].mean():.2f}")
print()

# Conflict per club
conflicts_per_club = conflicts.groupby('Club')[['half_conflict','quarter_conflict']].sum().sort_values(by='half_conflict', ascending=False)

print("Conflict per group")
print(conflicts_per_club[['half_conflict','quarter_conflict']])
print()

# Near misses per club (half)
events_per_club = near_half.groupby('Club').size().sort_values(ascending=False)
players_per_club = near_half.groupby('Club')['Count'].sum().sort_values(ascending=False)

print("Near Misses Events by club (half):")
print(events_per_club)
print("\nTop Clubs nach Spielern in Near-Misses (Half):")
print(players_per_club)

# check
print("\nKONSISTENZ-CHECK")
print("Summe players_per_club == total_players_involved_half ->",
      players_per_club.sum() == total_players_involved_half)

# near misses per club (quarter)
events_per_club_quarter = near_quarter.groupby('Club').size().sort_values(ascending=False)
players_per_club_quarter = near_quarter.groupby('Club')['Count'].sum().sort_values(ascending=False)

print("Top Clubs nach Near-Miss Events (Quarter):")
print(events_per_club_quarter)
print("\nTop Clubs nach Spielern in Near-Misses (Quarter):")
print(players_per_club_quarter)

# check
print("\nKONSISTENZ-CHECK (Quarter)")
print("Summe players_per_club_quarter == total_players_involved_quarter ->",
      players_per_club_quarter.sum() == total_players_involved_quarter)


print("\nFertig.")
