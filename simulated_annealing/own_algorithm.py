import pandas as pd
import numpy as np
import random
import math
from itertools import combinations
from collections import defaultdict, Counter
from tqdm import tqdm
import os


# for reporducability
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

rng = np.random.default_rng(seed=SEED)


# Switch between manual or automatic temperatur 
USE_MANUAL_T_START = True       
MANUAL_T_START = 5.0       
MANUAL_COOLING = 0.999   
MANUAL_T_END = 0.01   

if USE_MANUAL_T_START:
    
    T_start = MANUAL_T_START
    cooling_rate = MANUAL_COOLING
    T_end = MANUAL_T_END
    print(f"[Config] Using MANUAL T_start={T_start}, cooling_rate={cooling_rate}")
else:
    # starting values for later calibration
    T_start = 0.5       
    cooling_rate = 0.99
    T_end = 0.01

# Parameters
n_groups = 11
group_sizes = [3, 3, 3, 3, 3, 3, 4, 3, 3, 3, 3]  # group G with 4 places

# Number of iterations per SA run
MAX_ITER = 200


# Number of simulations
n_sim = 100

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

input_file = r"D:\Maturaarbeit\players.xlsx"

base_dir = os.getcwd()
penalty_file = os.path.join(base_dir, "penalty_history.csv")
csv_file     = os.path.join(base_dir, "draws_temp.csv")
excel_file   = os.path.join(base_dir, "own_draws.xlsx")

# check for Club NaN
df = pd.read_excel(input_file, engine="openpyxl")
df["Club"] = df["Club"].fillna("UNKNOWN").astype(str).str.strip()
clubs = dict(zip(df["Name"], df["Club"]))


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



players = df["Name"].tolist()
# Separate seeded and unseeded players
seeded = df[df["Seed"].notna()].to_dict("records")
unseeded = df[df["Seed"].isna()]["Name"].tolist()

# check if sum of group size is correct
assert sum(group_sizes) == len(df), "Sum of group size is not the same as the player count!"

# Prüfen Seeds
seed_counts = df['Seed'].astype(str).value_counts()
assert seed_counts.get('1', 0) == 1, "There must be exactly one Seed 1!"
assert seed_counts.get('2', 0) == 1, "There must be exactly one Seed 2!"
assert seed_counts.get('3/4', 0) == 2, "There must be exactly 2 seeds of type 3/4!"
assert seed_counts.get('5/8', 0) == 4, "There must be exactly 4 seeds of type 5/8!"


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

# Prepare CSV
if os.path.exists(csv_file):
    os.remove(csv_file)


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
def random_assignment(max_tries=5000):
    for _ in range(max_tries):
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
    raise RuntimeError("No valid start assignment was found.")
    
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
    
    return assignment  # if nothing works, return the original


# Simulated Annealing / Boltzmann Optimization
def simulated_annealing(max_iter=MAX_ITER, sim_nr=None, log_all=None):
    assignment = random_assignment()
    T = T_start

    # save current score
    current_score = score(assignment)

    # Log the initial (random) score
    if sim_nr is not None and log_all is not None:
        log_all.append({
            "Simulation": sim_nr,
            "Iteration": 0,
            "Penalty": current_score
        })
        

    for step in range(1, max_iter + 1):
        new_assign = neighbor(assignment)
        if valid_assignment(new_assign):
            s_old = current_score
            s_new = score(new_assign)
            delta = s_new - s_old
            if delta < 0 or random.random() < math.exp(-delta / T):
                assignment = new_assign
                current_score = s_new

            # log current penalty after each SA iteration
            if sim_nr is not None and log_all is not None:
                log_all.append({
                    "Simulation": sim_nr,
                    "Iteration": step,
                    "Penalty": current_score
                })
        
        else:
            # no valid neighbor: cool temperature, no logging
            pass
            
        T = max(T_end, T * cooling_rate)

    return assignment, score(assignment)




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

def debug_score_breakdown(assignment):
    # DIESE FUNKTION IST NUR ZUM DEBUGGEN DA
    
    breakdown = {
        "Total_Penalty": 0.0,
        "A_PlayerGroup": 0.0,
        "B_PairHistory_Sq": 0.0,
        "C_TripleHistory": 0.0,
        "D_QuadHistory": 0.0,
        "E_HalfClub_Weighted": 0.0,
        "F_QuarterClub_Weighted": 0.0,
    }
    
    # 1. Player group distribution
    for g, group in enumerate(assignment):
        for p in group:
            breakdown["A_PlayerGroup"] += history[p][g]
    
    # 2. History Pairs (squared)
    for group in assignment:
        for comb2 in combinations(group, 2):
            p1, p2 = sorted(comb2)
            breakdown["B_PairHistory_Sq"] += pair_history.get((p1, p2), 0) ** 2

    # 3. Triple History
    for group in assignment:
        for comb3 in combinations(group, 3):
            triple_history_key = tuple(sorted(comb3))
            breakdown["C_TripleHistory"] += triple_history.get(triple_history_key, 0)
            
    # 4. Quad History
    for group in assignment:
        for comb4 in combinations(group, 4):
            quadruple_history_key = tuple(sorted(comb4))
            breakdown["D_QuadHistory"] += quadruple_history.get(quadruple_history_key, 0) / 2
            
    # 5. Club Penalties
    club_half_counts = defaultdict(lambda: Counter())
    club_quarter_counts = defaultdict(lambda: Counter())

    for gi, group in enumerate(assignment):
        half = HALF_BY_INDEX[gi]
        quarter = QUARTER_BY_INDEX[gi]
        for p in group:
            club = clubs[p]
            club_half_counts[club][half] += 1
            club_quarter_counts[club][quarter] += 1
            
    half_pen = sum(max(0, c - 1) for club, cnt in club_half_counts.items() for c in cnt.values())
    quarter_pen = sum(max(0, c - 1) for club, cnt in club_quarter_counts.items() for c in cnt.values())

    breakdown["E_HalfClub_Weighted"] = W_HALF * half_pen
    breakdown["F_QuarterClub_Weighted"] = W_QUARTER * quarter_pen
    
    # Final Total Penalty
    breakdown["Total_Penalty"] = (
        breakdown["A_PlayerGroup"] +
        breakdown["B_PairHistory_Sq"] +
        breakdown["C_TripleHistory"] +
        breakdown["D_QuadHistory"] +
        breakdown["E_HalfClub_Weighted"] +
        breakdown["F_QuarterClub_Weighted"]
    )
    
    return breakdown



############################################################
# ===== Kurztest verschiedener Starttemperaturen ==========
############################################################
def sa_test(T_start, max_iter=50):
    # ... (Testfunktion aus dem Snippet hier einfügen) ...
    """Kurzer SA-Lauf: gibt (akzeptanzrate, beste_penalty) zurück"""
    assign = random_assignment()
    best = assign
    best_score = score(assign)
    T = T_start
    accepted_worse = 0
    worse_moves = 0

    for step in range(max_iter):
        new_assign = neighbor(assign)
        if not valid_assignment(new_assign):
            continue
        s_old = score(assign)
        s_new = score(new_assign)
        delta = s_new - s_old
        if delta > 0:
            worse_moves += 1
            # prüfen ob trotz Verschlechterung angenommen
            if random.random() < math.exp(-delta / T):
                accepted_worse += 1
        # Standard SA–Update
        if delta < 0 or random.random() < math.exp(-delta / T):
            assign = new_assign
            if s_new < best_score:
                best = new_assign
                best_score = s_new
        # lineares Abkühlen für den kurzen Test
        T *= 0.99
    return (accepted_worse / worse_moves if worse_moves else 0.0, best_score)

tests = [0.08, 0.16, 0.33, 0.5]
results = []
for T in tests:
    print(f"\nTesting T_start={T}")
    acc_rates = []
    bests = []
    for run in tqdm(range(5), desc=f"T={T}"):
        acc, best = sa_test(T_start=T, max_iter=50)
        acc_rates.append(acc)
        bests.append(best)
    print(f"Ø akzeptierte schlechtere Moves: {np.mean(acc_rates):.2f}")
    print(f"Ø beste Penalty nach 50 Iterationen: {np.mean(bests):.2f}")
    results.append((T, np.mean(acc_rates), np.mean(bests)))

print("\nSummary:")
for T, acc, best in results:
    print(f"T={T}:  Acceptance rate ≈{acc:.2f},  best penalty≈{best:.2f}")
############################################################



# Warm-up parameters
WARMUP_RUNS = 10

# 1) Warm-up simulations
print(f"[Warm-up] Starting {WARMUP_RUNS} warm-up simulations to fill histories...")
for sim in tqdm(range(1, WARMUP_RUNS + 1), desc="Warm-up running"):
    assignment, sc = simulated_annealing(max_iter=MAX_ITER, sim_nr=sim)



# 2) Calibration after warm-up
if not USE_MANUAL_T_START:      
    T_start, cooling_rate = calibrate_temperature(
        samples=300, p_target=0.7,
        max_iter=MAX_ITER, factor=4.0, min_cooling=0.985
    )
    print(f"[Using] T_start = {T_start:.3f}, cooling_rate = {cooling_rate:.6f}")
else:
    print(f"[Manual] Keeping T_start = {T_start:.3f}, cooling_rate = {cooling_rate:.6f}")

print(f"[Seed] Using global random seed = {SEED}")


# Main simulations for multiple MAX_HISTORY scenarios
history_settings = [0, 1, 2, 3, 4, 5]  # 0 = no history, 1-5 = number of tournaments in history

# Struktur, um alle Auslosungen für die Visualisierung zu speichern
all_assignments_history = {mh: [] for mh in history_settings}
all_assignments_history["full"] = []  # für den zusätzlichen Lauf mit voller History

for max_hist in history_settings:
    # Reset penalty_history for this MAX_HISTORY
    penalty_history_all = []

    print(f"\n[Main Simulations] Running with MAX_HISTORY = {max_hist}")

    # Reset history and queues for each scenario
    history = {p: {g: 0 for g in range(n_groups)} for p in players}
    pair_history.clear()
    triple_history.clear()
    quadruple_history.clear()
    history_queue = []

    # Prepare CSV for this MAX_HISTORY
    run_csv = csv_file.replace(".csv", f"_hist{max_hist}.csv")
    if os.path.exists(run_csv):
        os.remove(run_csv)

    # Run simulations
    for sim in tqdm(range(1, n_sim + 1), desc=f"Simulations MAX_HISTORY={max_hist}"):
        assignment, sc = simulated_annealing(max_iter=MAX_ITER, sim_nr=sim, log_all=penalty_history_all)

        # Save the draw
        all_assignments_history[max_hist].append([list(g) for g in assignment])

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
        df_rows.to_csv(run_csv, mode="a", index=False, header=(sim == 1))
        
        if max_hist > 0:
            history_queue.append(assignment)
            needs_rebuild = False
            if len(history_queue) > max_hist:
                # complete restart
                history = {p: {g: 0 for g in range(n_groups)} for p in players}
                pair_history.clear()
                triple_history.clear()
                quadruple_history.clear()
                
                # starting penalty 0
                history_queue = []           
            

            else:
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



            if max_hist > 0 and sim % (max_hist + 1) == 0:
                if max_hist > 0 and sim % (max_hist + 1) == 0:
                    # Use the current assignment from this simulation for debugging
                    breakdown = debug_score_breakdown(assignment)

                    print(f"\n[DEBUG] History-Check after SIM {sim} (Reset point)")
                    print(f"Current Penalty: {breakdown['Total_Penalty']:.2f}")
                    print(f"A_PlayerGroup: {breakdown['A_PlayerGroup']:.2f}")
                    print(f"B_PairHistory^2: {breakdown['B_PairHistory_Sq']:.2f}")
                    print(f"C_TripleHistory: {breakdown['C_TripleHistory']:.2f}")
                    print(f"D_QuadHistory: {breakdown['D_QuadHistory']:.2f}")
                    print(f"E_HalfClub_Weighted: {breakdown['E_HalfClub_Weighted']:.2f}")
                    print(f"F_QuarterClub_Weighted: {breakdown['F_QuarterClub_Weighted']:.2f}")
 

    # Save penalty history CSV for this MAX_HISTORY
    df_all = pd.DataFrame(penalty_history_all)
    df_all.to_csv(penalty_file.replace(".csv", f"_all_hist{max_hist}.csv"), index=False)



    print(f"[Done] All simulations with MAX_HISTORY={max_hist} saved to {run_csv}")

# extra run: every single draw gets saved in history to show the change
print("\n[Full History Run] Saving every simulation in cumulative history")
history = {p: {g: 0 for g in range(n_groups)} for p in players}
pair_history.clear()
triple_history.clear()
quadruple_history.clear()

run_csv_full = csv_file.replace(".csv", "_full_history.csv")
if os.path.exists(run_csv_full):
    os.remove(run_csv_full)

# Reset penalty_history for full history
penalty_history_all_full = []

# Define penalty CSV file for full history
penalty_file_full = penalty_file.replace(".csv", "_full_history.csv")
if os.path.exists(penalty_file_full):
    os.remove(penalty_file_full)


for sim in tqdm(range(1, n_sim + 1), desc="Full history simulations"):
    assignment, sc = simulated_annealing(max_iter=MAX_ITER, sim_nr=sim, log_all=penalty_history_all_full)
    all_assignments_history["full"].append([list(g) for g in assignment])

    # update history
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

    # write CSV
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
    df_rows.to_csv(run_csv_full, mode="a", index=False, header=(sim == 1))

df_all_full = pd.DataFrame(penalty_history_all_full)
df_all_full.to_csv(penalty_file.replace(".csv", "_all_full_history.csv"), index=False)

print(f"[Done] Full history saved to {run_csv_full}")





def analyze_assignment_uniformity(file_path, max_hist):
    """
    Analyzes the uniformity of group assignments across all simulations
    for a given MAX_HISTORY scenario.
    """
    try:
        df_assign = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return

    # Count how often each player was in each group
    group_counts = df_assign.groupby(['Name', 'Group']).size().unstack(fill_value=0)
    
    # Calculate the standard deviation of group assignments for EACH player
    # The standard deviation measures how much the group counts vary for each player.
    player_std_devs = group_counts.std(axis=1)
    
    # Summary
    median_std = player_std_devs.median()
    mean_std = player_std_devs.mean()
    
    print(f"\n--- Uniformity Analysis (MAX_HISTORY={max_hist}) ---")
    print(f"Basis: {df_assign['File'].max()} simulations.")
    print(f"Median standard deviation of group assignments per player: {median_std:.2f}")
    print(f"Average standard deviation of group assignments per player: {mean_std:.2f}")
    print("---------------------------------------------------------")
    print("Interpretation: Lower values mean more uniform distribution (lower predictability).")
    
    return median_std, mean_std

# Example call for your scenarios (must be executed after the simulation)
# Replace 'draws_temp' with the actual prefix you are using.

all_uniformity_results = []
file_prefix = "draws_temp" # This should match the 'csv_file' path

for max_hist in history_settings:
    run_file = file_prefix + f"_hist{max_hist}.csv"
    median_std, mean_std = analyze_assignment_uniformity(run_file, max_hist)
    all_uniformity_results.append({
        "MAX_HISTORY": max_hist,
        "Median_Std_Dev": median_std,
        "Mean_Std_Dev": mean_std
    })

# Summarize the results to see the effect of MAX_HISTORY
df_uniformity = pd.DataFrame(all_uniformity_results)

# Import 'fixed_players' and 'players' from the main script
# (These variables are already defined in your global scope)

def analyze_segmented_uniformity(file_path, players, fixed_players, max_hist):
    """
    Analyzes uniformity separately for seeded and all players.
    """
    try:
        df_assign = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return 0, 0, 0, 0

    # Player group counts (all players)
    group_counts_all = df_assign.groupby(['Name', 'Group']).size().unstack(fill_value=0)
    
    # 1. Analysis of ALL players
    all_std_devs = group_counts_all.std(axis=1)
    median_all = all_std_devs.median()
    mean_all = all_std_devs.mean()

    # 2. Analysis of UNSEEDED players
    unseeded_players = [p for p in players if p not in fixed_players]
    
    # Filter the group counts only for unseeded players
    if not unseeded_players:
        print(f"[Analysis] No unseeded players found.")
        return median_all, mean_all, 0, 0
    
    group_counts_unseeded = group_counts_all.loc[unseeded_players]
    unseeded_std_devs = group_counts_unseeded.std(axis=1)
    
    median_unseeded = unseeded_std_devs.median()
    mean_unseeded = unseeded_std_devs.mean()
    
    print(f"\n--- Segmented Analysis (MAX_HISTORY={max_hist}) ---")
    print(f"Median Std Dev (All Players): {median_all:.2f}")
    print(f"Median Std Dev (Unseeded Players): {median_unseeded:.2f}")
    print("---------------------------------------------------------")

    return median_all, mean_all, median_unseeded, mean_unseeded


# Run segmented analysis for all history settings
segmented_results = []

for max_hist in history_settings:
    run_file = csv_file.replace(".csv", f"_hist{max_hist}.csv") # Path to assignment file
    
    median_all, mean_all, median_unseeded, mean_unseeded = analyze_segmented_uniformity(
        run_file, players, fixed_players, max_hist
    )
    
    segmented_results.append({
        "MAX_HISTORY": max_hist,
        "Median_All": median_all,
        "Mean_All": mean_all,
        "Median_Unseeded": median_unseeded,
        "Mean_Unseeded": mean_unseeded
    })

# Output the final comparison table
df_segmented_uniformity = pd.DataFrame(segmented_results)

print("\n\n=== COMPARISON: UNSEEDED PLAYERS vs. ALL PLAYERS ===")
print("  (Lower value = more uniform distribution / less predictable)")
print(df_segmented_uniformity.to_markdown(index=False, floatfmt=".2f"))
