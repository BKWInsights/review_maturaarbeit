import pandas as pd

# Read Excel file
df = pd.read_excel("d:/Maturaarbeit/all_MS_U13.xlsx")

# Normalize group names
df['Group'] = df['Group'].str.strip().str.upper()

# Mapping: Groups -> Position in 16-player knockout bracket
# Numbers which are not included are empty places in the main draw
group_to_pos = {
    'A': 1,
    'B': 16,
    'C': 12,
    'D': 5,
    'E': 7,
    'F': 10,
    'G': 3,
    'H': 14,
    'I': 9,
    'J': 8,
    'K': 13
}

df['Pos'] = df['Group'].map(group_to_pos)

# Quarter and half assignment
def get_quarter(pos):
    if 1 <= pos <= 4:
        return 'Q1'
    elif 5 <= pos <= 8:
        return 'Q2'
    elif 9 <= pos <= 12:
        return 'Q3'
    elif 13 <= pos <= 16:
        return 'Q4'
    else:
        return None

def get_half(pos):
    if 1 <= pos <= 8:
        return 'top'
    elif 9 <= pos <= 16:
        return 'bottom'
    else:
        return None

df['Quarter'] = df['Pos'].apply(get_quarter)
df['Half'] = df['Pos'].apply(get_half)

# Analysis functions
def analyse_halften_viertel(df):
    """Checks per draw and club whether ALL players are in the same half or the same quarter."""
    results = []
    for file, gruppe in df.groupby('File'):
        for club, club_df in gruppe.groupby('Club'):
            if len(club_df) > 1:
                halves = club_df['Half'].dropna().unique()
                quarters = club_df['Quarter'].dropna().unique()
                results.append({
                    'File': file,
                    'Club': club,
                    'Number_of_players': len(club_df),
                    'Halves': list(halves),
                    'Quarters': list(quarters),
                    'Only_one_half': len(halves) == 1,
                    'Only_one_quarter': len(quarters) == 1
                })
    return pd.DataFrame(results)

# Run analysis
half_quarter_check = analyse_halften_viertel(df)

half_conflicts = half_quarter_check[half_quarter_check['Only_one_half']]
quarter_conflicts = half_quarter_check[half_quarter_check['Only_one_quarter']]

# Output results
print("=== Conflicts: All players of a club in the same half ===")
print(half_conflicts[['File', 'Club', 'Halves']])

print("\n=== Conflicts: All players of a club in the same quarter ===")
print(quarter_conflicts[['File', 'Club', 'Quarters']])

print("\n=== Statistics ===")
print(f"Total draws: {df['File'].nunique()}")
print(f"Half conflicts: {len(half_conflicts)}")
print(f"Quarter conflicts: {len(quarter_conflicts)}")

# Same checks, but now only 2 Persons from the same club
min2_half_conflicts = []
min2_quarter_conflicts = []

for file, gruppe in df.groupby('File'):
    for club, club_df in gruppe.groupby('Club'):
        if len(club_df) > 1:
            # Count players per half
            half_counts = club_df['Half'].value_counts()
            if (half_counts >= 2).any():
                min2_half_conflicts.append({
                    'File': file,
                    'Club': club,
                    'Half_counts': half_counts.to_dict()
                })
            # Count players per quarter
            quarter_counts = club_df['Quarter'].value_counts()
            if (quarter_counts >= 2).any():
                min2_quarter_conflicts.append({
                    'File': file,
                    'Club': club,
                    'Quarter_counts': quarter_counts.to_dict()
                })

# Convert to DataFrames
min2_half_df = pd.DataFrame(min2_half_conflicts)
min2_quarter_df = pd.DataFrame(min2_quarter_conflicts)

print("\n=== At least 2 players of a club in the same half ===")
print(min2_half_df)

print("\n=== At least 2 players of a club in the same quarter ===")
print(min2_quarter_df)

print("\n=== Statistics (at least 2 in same section) ===")
print(f"At least 2 half conflicts: {len(min2_half_df)}")
print(f"At least 2 quarter conflicts: {len(min2_quarter_df)}")
