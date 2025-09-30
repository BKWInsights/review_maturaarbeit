import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

output_folder = os.getcwd()

# Load conflict summary
conflicts = pd.read_excel(os.path.join(output_folder, "club_conflicts_summary.xlsx"))

# Clean Club names
conflicts['Club'] = conflicts['Club'].str.strip()

# Sum conflicts per club
half_conflicts_per_club = conflicts.groupby('Club')['half_conflict'].sum().sort_values(ascending=False)
quarter_conflicts_per_club = conflicts.groupby('Club')['quarter_conflict'].sum().sort_values(ascending=False)

plt.figure(figsize=(12,6))
sns.barplot(x=half_conflicts_per_club.values, y=half_conflicts_per_club.index, hue=half_conflicts_per_club.index, palette='Reds_r', legend=False)
plt.title('Total Half Conflicts per Club')
plt.xlabel('Number of Half Conflicts')
plt.ylabel('Club')
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "half_conflicts_per_club.png"))
plt.show()

plt.figure(figsize=(12,6))
sns.barplot(x=quarter_conflicts_per_club.values, y=quarter_conflicts_per_club.index, hue=quarter_conflicts_per_club.index, palette='Blues_r', legend=False)
plt.title('Total Quarter Conflicts per Club')
plt.xlabel('Number of Quarter Conflicts')
plt.ylabel('Club')
plt.tight_layout()
plt.savefig(os.path.join(output_folder, "quarter_conflicts_per_group.png"))
plt.show()

# Load near misses
near_misses = pd.read_excel(os.path.join(output_folder, "near_misses.xlsx"))
near_misses['Club'] = near_misses['Club'].str.strip()

# Near Misses für Half
near_misses_half = near_misses[near_misses['Type'] == 'Half']
near_misses_half_per_club = near_misses_half.groupby('Club')['Count'].sum().sort_values(ascending=False)

plt.figure(figsize=(12,6))
sns.barplot(x=near_misses_half_per_club.values, y=near_misses_half_per_club.index, hue=near_misses_half_per_club.index, palette='Oranges_r', legend=False)
plt.title('Near Misses per Club (Half, 60% rule)')
plt.xlabel('Number of Near Misses')
plt.ylabel('Club')
plt.tight_layout()
plt.savefig('near_misses_half_per_club.png')
plt.show()


# Near Misses für Quarter
near_misses_quarter = near_misses[near_misses['Type'] == 'Quarter']
near_misses_quarter_per_club = near_misses_quarter.groupby('Club')['Count'].sum().sort_values(ascending=False)

plt.figure(figsize=(12,6))
sns.barplot(x=near_misses_quarter_per_club.values, y=near_misses_quarter_per_club.index, hue=near_misses_quarter_per_club.index, palette='Purples_r', legend=False)
plt.title('Near Misses per Club (Quarter, 60% rule)')
plt.xlabel('Number of Near Misses')
plt.ylabel('Club')
plt.tight_layout()
plt.savefig('near_misses_quarter_per_club.png')
plt.show()

print("Finished")
