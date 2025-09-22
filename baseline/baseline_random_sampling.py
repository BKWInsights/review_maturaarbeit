import pandas as pd
import random
import os

# Testing
df = pd.read_excel(r"D:\Maturaarbeit\players.xlsx")

seed_map = df.set_index("Name")["Seed"].apply(lambda x: None if pd.isna(x) else x).to_dict() # seed_map: {"Player1": 1, "Player2": 2, ..., "PlayerX": None}
clubs = df.set_index("Name")["Club"].to_dict()                                               # clubs: {"Player1": "Club1", ..., "PlayerX": "ClubX"}

# Checks if a draw is valid
def check_valid(draw, seed_map, clubs, full_slots):
    # 1) Seed check first
    for player, group in draw.items():
        seed = seed_map[player]
        if seed is not None:
            if seed == 1 and group != "A": return False
            if seed == 2 and group != "B": return False
            if seed == "3/4" and group not in ("C", "D"): return False
            if seed == "5/8" and group not in ("E", "F", "G", "H"): return False

    # 2) Group size and club rule
    group_counts = {g: 0 for g in full_slots}
    group_clubs = {}
    for player, group in draw.items():
        group_counts[group] += 1
        if group_counts[group] > full_slots[group]:
            return False

        c = clubs[player]
        if group not in group_clubs:
            group_clubs[group] = set()
        if c in group_clubs[group]:
            return False
        group_clubs[group].add(c)

    return True

# Full slot allocation per group
def get_full_slots(free_slots):
    full_slots = {g: 3 for g in free_slots}  # By default 3 spots
    full_slots["G"] = 4                      # Exception: Group G
    return full_slots


# Rejection sampling with progress saving
def monte_carlo_random(seed_map, free_slots, clubs, n_sim, progress_file="progress.csv"):
    full_slots = get_full_slots(free_slots)
    
    # Check for sufficient slots
    total_players = len(seed_map)
    if sum(full_slots.values()) < total_players:
        raise ValueError(f"Too few slots ({sum(full_slots.values())}) for {total_players} players")

    players = list(seed_map.keys())

    # Load already saved results (if available)
    if os.path.exists(progress_file):
        df_existing = pd.read_csv(progress_file)
        rows = df_existing.to_dict(orient="records")
        valid_draws = df_existing["Simulation"].max() + 1
        print(f"Progress loaded: {valid_draws} valid draws already present")
    else:
        rows = []
        valid_draws = 0

    attempts = 0
    max_attempts = n_sim * 1000  # Safety brake

    try:
        while valid_draws < n_sim:
            attempts += 1

            # 1) Random group assignment
            slots = []
            for g, k in full_slots.items():
                slots.extend([g] * k)

            random.shuffle(players)
            random.shuffle(slots)
            draw = {p: slots[i] for i, p in enumerate(players)}

            # 2) Check rules
            if check_valid(draw, seed_map, clubs, full_slots):
                for p, g in draw.items():
                    rows.append({"Player": p, "Group": g, "Simulation": valid_draws})
                valid_draws += 1

                # Progress output
                if valid_draws % 10 == 0:
                    print(f"{valid_draws} valid draws reached after {attempts} attempts")

                # Save progress every 100 draws
                if valid_draws % 100 == 0:
                    pd.DataFrame(rows).to_csv(progress_file, index=False)
                    

            # Safety stop if max_attempts exceeded
            # if attempts > max_attempts:
                # print(f"WARNING: Max attempts ({max_attempts}) reached. Simulation aborted.")
                # break

    except KeyboardInterrupt:
        print("Interrupt detected, saving last state...")

    # Save final result
    pd.DataFrame(rows).to_csv(progress_file, index=False)
    print(f"Simulation finished: {valid_draws} valid draws after {attempts} attempts")
    return pd.DataFrame(rows)


# Testing

free_slots = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]
monte_carlo_random(seed_map, free_slots, clubs, n_sim=100)

required_cols = {"Name", "Seed", "Club"}
if not required_cols.issubset(df.columns):
    raise ValueError("Excel file must contain columns: Name, Seed, Club")
