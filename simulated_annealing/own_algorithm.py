import pandas as pd
import numpy as np
import random
import math
from itertools import combinations
from collections import defaultdict, Counter
from tqdm import tqdm
import os

# Parameters
n_groups = 11
group_sizes = [3]*10 + [4]

# Number of iterations per SA run
MAX_ITER = 200

# Temperature parameters for Boltzmann
T_start = 5
T_end = 0.01
cooling_rate = 0.999

# Number of simulations
n_sim = 100

# Store penalty progression
penalty_history = []

# Lightly weighted penalty weights
W_HALF = 0.05      # for bracket half
W_QUARTER = 0.03   # for bracket quarter

# Fixed: order of your 11 groups (A..K)
GROUP_ORDER = list("ABCDEFGHIJK")

# Mapping group -> position
# Positions that do not occur are empty, meaning they meet the next opponent one round later
GROUP_TO_POS = {
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
    'K': 13,
}

def pos_to_half(pos):
    return 'top' if 1 <= pos <= 8 else 'bottom'

def pos_to_quarter(pos):
    if   1 <= pos <= 4:  return 'Q1'
    elif 5 <= pos <= 8:  return 'Q2'
    elif 9 <= pos <= 12: return 'Q3'
    elif 13 <= pos <= 16:return 'Q4'
    return None

# Precompute: for group index (0..10) the Pos/Half/Quarter
POS_BY_INDEX     = [GROUP_TO_POS[g] for g in GROUP_ORDER]
HALF_BY_INDEX    = [pos_to_half(p) for p in POS_BY_INDEX]
QUARTER_BY_INDEX = [pos_to_quarter(p) for p in POS_BY_INDEX]

# Logging mode: best or all (for visualization)
# best = only best_score per simulation, all = all scores per iteration
log_mode = "all"

input_file = r"D:\Maturaarbeit\players.xlsx"
csv_file = r"D:\Maturaarbeit\draws_temp.csv"
excel_file = r"D:\Maturaarbeit\own_draws.xlsx"
penalty_file = r"D:\Maturaarbeit\penalty_history.csv"

# Load player list
df = pd.read_excel(input_file, engine="openpyxl")

players = df["Name"].tolist()
# Separate seeded and unseeded players
seeded = df[df["Seed"].notna()].to_dict("records")
unseeded = df[df["Seed"].isna()]["Name"].tolist()
clubs = dict(zip(df["Name"], df["Club"]))

# Define groups
groups = {g: [] for g in list("ABCDEFGHIJK")}

# Define rules for seeded players
three_by_four_groups = ["C", "D"]
five_by_eight_groups = ["E", "F", "G", "H"]

random.shuffle(three_by_four_groups)
random.shuffle(five_by_eight_groups)

# Distribute seeds according to rules
for s in seeded:
    name, seed = s["Name"], str(s["Seed"])

    if seed == "1":
        groups["A"].append(name)
    elif seed == "2":
        groups["B"].append(name)
    elif seed == "3/4":
        groups[three_by_four_groups.pop()].append(name)
    elif seed == "5/8":
        groups[five_by_eight_groups.pop()].append(name)

# Remember seeded players (must stay in the assigned group)
fixed_players = set([s["Name"] for s in seeded])

# History from previous tournaments
# Format: dict[player][group] = frequency
history = {p: {g: 0 for g in range(n_groups)} for p in players}

# Pair history
pair_history = defaultdict(int)
triple_history = defaultdict(int)
quadruple_history = defaultdict(int)

# No players from the same club
def valid_assignment(assignment):
    for group in assignment:
        seen_clubs = set()
        seed_count = 0
        for p in group:
            if clubs[p] in seen_clubs:
                return False
            seen_clubs.add(clubs[p])

            if p in fixed_players:
                seed_count += 1
        
        if seed_count > 1:
            return False
    return True

# Evaluate draw
def score(assignment):
    penalty = 0

    # Player group distribution
    for g, group in enumerate(assignment):
        for p in group:
            penalty += history[p][g]  # Higher penalty if player has been here often

    for group in assignment:
        # 2-player pairs
        for comb2 in combinations(group, 2):
            p1, p2 = sorted(comb2)
            penalty += pair_history[(p1, p2)] ** 2

        # 3-player pairs (lightly weighted)
        for comb3 in combinations(group, 3):
            triple_history_key = tuple(sorted(comb3))
            penalty += triple_history[triple_history_key]  # Weight 1

        # 4-player pairs (even lighter)
        for comb4 in combinations(group, 4):
            quadruple_history_key = tuple(sorted(comb4))
            penalty += quadruple_history[quadruple_history_key] / 2  # Weight 0.5

    # Very lightly weighted penalty term for club clustering in the knockout bracket
    # Count per club: half and quarter occupancy across all groups
    club_half_counts = defaultdict(lambda: Counter())
    club_quarter_counts = defaultdict(lambda: Counter())

    for gi, group in enumerate(assignment):
        half = HALF_BY_INDEX[gi]
        quarter = QUARTER_BY_INDEX[gi]
        for p in group:
            club = clubs[p]
            club_half_counts[club][half] += 1
            club_quarter_counts[club][quarter] += 1

    # Penalize excess (>= 2) in same half/quarter lightly
    # Example: counts [3,0] in halves -> (3-1)=2 excess; in quarters [2,1,0,0] -> (2-1)=1 excess
    half_pen = 0.0
    for club, cnt in club_half_counts.items():
        half_pen += sum(max(0, c - 1) for c in cnt.values())
    quarter_pen = 0.0
    for club, cnt in club_quarter_counts.items():
        quarter_pen += sum(max(0, c - 1) for c in cnt.values())

    penalty += W_HALF * half_pen + W_QUARTER * quarter_pen

    return penalty


# Create a random, valid draw
def random_assignment():
    while True:
        assignment = [list(groups[g]) for g in groups]
        
        shuffled = unseeded[:]
        random.shuffle(shuffled)

        index = 0
        for i, size in enumerate(group_sizes):
            free_slots = size - len(assignment[i])  # How many spots are still free in the group
            assignment[i].extend(shuffled[index:index+free_slots])
            index += free_slots

        if valid_assignment(assignment):
            return assignment
    
# Neighbor state by swapping 2 players for Simulated Annealing
def neighbor(assignment, max_attempts=200):
    new = [list(g) for g in assignment]

    for _ in range(max_attempts):
        g1, g2 = random.sample(range(n_groups), 2)
        if not new[g1] or not new[g2]:
            continue

        i_candidates = [i for i in range(len(new[g1])) if new[g1][i] not in fixed_players]
        j_candidates = [j for j in range(len(new[g2])) if new[g2][j] not in fixed_players]

        if not i_candidates or not j_candidates:
            continue
        
        i = random.choice(i_candidates)
        j = random.choice(j_candidates)

        new[g1][i], new[g2][j] = new[g2][j], new[g1][i]
        return new
    
    return new  # if nothing works, return the original


# Simulated Annealing / Boltzmann Optimization
def simulated_annealing(max_iter=MAX_ITER, sim_nr=None):
    assignment = random_assignment()
    best = assignment
    best_score = score(assignment)

    T = T_start

    # Log starting value
    if log_mode == "all" and sim_nr is not None:
        penalty_history.append({
            "Simulation": sim_nr,
            "Iteration": 0,
            "Penalty": best_score
        })

    for step in range(1, max_iter+1):
        new_assign = neighbor(assignment)

        if valid_assignment(new_assign):
            s_old = score(assignment)
            s_new = score(new_assign)
            delta = s_new - s_old

            if delta < 0 or random.random() < math.exp(-delta / T):
                assignment = new_assign

            if s_new < best_score:
                best, best_score = new_assign, s_new
        else:
            # no valid neighbor → score remains the same
            s_new = score(assignment)

        # Lower temperature
        T = max(T_end, T * cooling_rate)

        # Always log – even if nothing changed
        if log_mode == "all" and sim_nr is not None:
            penalty_history.append({
                "Simulation": sim_nr,
                "Iteration": step,
                "Penalty": score(assignment)
            })

    # If only best should be logged
    if log_mode == "best" and sim_nr is not None:
        penalty_history.append({
            "Simulation": sim_nr,
            "Iteration": max_iter,
            "Penalty": best_score
        })

    return best, best_score


# Prepare CSV
if os.path.exists(csv_file):
    os.remove(csv_file)

# Automatic calibration of T_start and cooling_rate
def calibrate_temperature(samples=300, p_target=0.7, max_iter=MAX_ITER, factor=4.0, min_cooling=0.985):
    assign = random_assignment()
    deltas_pos = []
    attempts = 0
    max_attempts = samples * 10

    while len(deltas_pos) < samples and attempts < max_attempts:
        attempts += 1
        new_assign = neighbor(assign)
        if not valid_assignment(new_assign):
            continue
        s_old = score(assign)
        s_new = score(new_assign)
        delta = s_new - s_old
        if delta > 0:
            deltas_pos.append(delta)
        # small random walk so it doesn’t always stay at the same point
        if delta < 0 or random.random() < 0.5:
            assign = new_assign
    
    if not deltas_pos:
        print("[Calibration] No positive ΔE found – T_start remains unchanged.")
        return T_start, cooling_rate
    
    median_delta = float(np.median(deltas_pos))
    # Make sure temperature and cooling rate are high enough, else it turn into a greedy algorithm only accepting better results
    factor = 4.0
    p_target = 0.7
    min_cooling = 0.985
    # Formula: T_start for desired acceptance p_target
    T_suggest = factor * median_delta / math.log(1.0 / (1.0 - p_target))
    # Calculate cooling_rate so that after max_iter we end at T_end
    cooling_suggest = max(min_cooling, (T_end / T_suggest) ** (1.0 / max_iter))

    print(f"[Calibration] Median ΔE⁺: {median_delta:.3f}")
    print(f"[Calibration] Target acceptance: {p_target*100:.1f}%")
    print(f"[Calibration] Suggested T_start: {T_suggest:.3f}")
    print(f"[Calibration] Suggested cooling_rate: {cooling_suggest:.6f}")

    return T_suggest, cooling_suggest

# Run calibration
print(f"[Using] T_start = {T_start:.3f}, cooling_rate = {cooling_rate:.6f}")


# Warm-up parameters
WARMUP_RUNS = 5

# 1) Warm-up simulations
print(f"[Warm-up] Starting {WARMUP_RUNS} warm-up simulations to fill histories...")
for sim in tqdm(range(1, WARMUP_RUNS + 1), desc="Warm-up running"):
    assignment, sc = simulated_annealing(max_iter=MAX_ITER, sim_nr=sim)

    # Update history
    for gi, group in enumerate(assignment):
        for p in group:
            history[p][gi] += 1
        for comb2 in combinations(group, 2):
            p1, p2 = sorted(comb2)
            pair_history[(p1, p2)] += 1
        for comb3 in combinations(group, 3):
            triple_history[tuple(sorted(comb3))] += 1
        for comb4 in combinations(group, 4):
            quadruple_history[tuple(sorted(comb4))] += 1

# 2) Calibration after warm-up
T_start, cooling_rate = calibrate_temperature(samples=300, p_target=0.7, max_iter=MAX_ITER, factor=4.0, min_cooling=0.985)
print(f"[Using] T_start = {T_start:.3f}, cooling_rate = {cooling_rate:.6f}")

# 3) Main simulations
for sim in tqdm(range(WARMUP_RUNS + 1, n_sim + 1), desc="Simulations running"):
    assignment, sc = simulated_annealing(max_iter=MAX_ITER, sim_nr=sim)

    # Update history
    for gi, group in enumerate(assignment):
        for p in group:
            history[p][gi] += 1
        for comb2 in combinations(group, 2):
            p1, p2 = sorted(comb2)
            pair_history[(p1, p2)] += 1
        for comb3 in combinations(group, 3):
            triple_history[tuple(sorted(comb3))] += 1
        for comb4 in combinations(group, 4):
            quadruple_history[tuple(sorted(comb4))] += 1

    # Write CSV
    rows = []
    for gi, group in enumerate(assignment):
        for p in group:
            rows.append({
                "File": sim,
                "Group": chr(65+gi),
                "Club": clubs[p],
                "Name": p,
                "Seed": df.loc[df["Name"] == p, "Seed"].values[0] if p in fixed_players else ""
            })
    df_rows = pd.DataFrame(rows)
    df_rows.to_csv(csv_file, mode="a", index=False, header=(sim == WARMUP_RUNS + 1))

    # Append CSV (duplicate block kept as in original)
    rows = []
    for gi, group in enumerate(assignment):
        for p in group:
            rows.append({
                "File": sim,
                "Group": chr(65+gi),
                "Club": clubs[p],
                "Name": p,
                "Seed": df.loc[df["Name"] == p, "Seed"].values[0] if p in fixed_players else ""
            })
    df_rows = pd.DataFrame(rows)
    df_rows.to_csv(csv_file, mode="a", index=False, header=(sim == 1))
        

df_penalty = pd.DataFrame(penalty_history)
df_penalty.to_csv(penalty_file, index=False)
print(f"Penalty progression saved in {penalty_file}")

# Finally CSV to Excel
df_final = pd.read_csv(csv_file)
df_final.to_excel(excel_file, index=False, engine="openpyxl")
print(f"All simulations saved to Excel: {excel_file}")
