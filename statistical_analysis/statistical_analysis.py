import pandas as pd
import numpy as np
from scipy.stats import chisquare
from scipy.stats import beta as beta_dist, norm
from scipy.stats import binomtest
import math, random, glob, os, re


rng = np.random.default_rng(seed=42)
random.seed(42)
n_boot = 10000


# from vergleichsbasis_random import monte_carlo_random, get_full_slots

# Folder with all evaluation files
input_folder = "D:\Maturaarbeit\evaluations"

# Output folder
output_folder = r"D:\Maturaarbeit\analysis_results"
os.makedirs(output_folder, exist_ok=True)

# Collect all Excel files
def sort_key(s):
    # split string in text and number blocks
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

excel_files = sorted(glob.glob(os.path.join(input_folder, "*.xlsx")), key=sort_key)

def wilson_interval(x, n, alpha=0.05):
    if n == 0:
        return (0.0, 0.0)
    p_hat = x / n
    z = norm.ppf(1 - alpha/2) 
    denom = 1 + z*z/n
    center = (p_hat + z*z/(2*n)) / denom
    half = (z/denom) * math.sqrt(p_hat*(1-p_hat)/n + z*z/(4*n*n))
    return max(0.0, center - half), min(1.0, center + half)

def jeffreys_interval(x, n, alpha=0.05):
    if n == 0:
        return (0.0, 0.0)
    a = x + 0.5
    b = n - x + 0.5
    lo = 0.0 if x == 0 else float(beta_dist.ppf(alpha/2, a, b))
    hi = 1.0 if x == n else float(beta_dist.ppf(1 - alpha/2, a, b))
    return lo, hi


for file in excel_files:
    print(f"Processing: {os.path.basename(file)}")

    # Load 6th sheet
    try:
        df_all = pd.read_excel(file, sheet_name="Chi2 preparation", engine="openpyxl")
    except Exception as e:
        print(f"Skipping {file}, error reading sheet: {e}")
        continue

    # Fixed free slots ONLY for unseeded players
    free_slots = {
        "A": 2, "B": 2, "C": 2, "D": 2,
        "E": 2, "F": 2, "G": 3, "H": 2,
        "I": 3, "J": 3, "K": 3
    }

    all_groups = list(free_slots.keys())

    # Global probabilities for unseeded players
    total_free = sum(free_slots.values())
    p_unseeded = np.array([free_slots[g] / total_free for g in all_groups])

    # Seed parser
    def parser_seed(val):
        if pd.isna(val):
            return None
        s = str(val).strip()
        if s in ["3/4"]:
            return "3/4"
        if s in ["5/8"]:
            return "5/8"
        try:
            return int(s)
        except ValueError:
            return None

    # Expected distribution (theoretical)
    def expected_distribution(total, seed, groups, p_unseeded):
        if seed == 1:
            return np.array([total if g == "A" else 0 for g in groups])
        if seed == 2:
            return np.array([total if g == "B" else 0 for g in groups])
        if seed == "3/4":
            return np.array([total/2 if g in ["C", "D"] else 0 for g in groups])
        if seed == "5/8":
            return np.array([total/4 if g in ["E", "F", "G", "H"] else 0 for g in groups])
        return total * p_unseeded

    # Observed distribution
    grouped = (
        df_all
        .groupby(["Name", "Group"])["Count"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=all_groups, fill_value=0)
    )

    # Clubs per player
    clubs = df_all.groupby("Name")["Club"].agg(
    lambda s: s.mode().iat[0] if not s.mode().empty else "UNKNOWN").to_dict()

    # Create seed map
    seed_map = {
        name: parser_seed(df_all.loc[df_all["Name"] == name, "Seed"].dropna().unique()[0])
        if len(df_all.loc[df_all["Name"] == name, "Seed"].dropna().unique()) else None
        for name in grouped.index
    }

    # allowed groups for seeded players
    def seed_allowed_groups(seed, groups):
        if seed == 1:
            return ["A"]
        if seed == 2:
            return ["B"]
        if seed == "3/4":
            return ["C", "D"]
        if seed == "5/8":
            return ["E", "F", "G", "H"]
        return groups

    # Monte Carlo with MRV
    def monte_carlo_mrv(seed_map, free_slots, clubs, n_sim, max_restarts=50):
        groups = list(free_slots.keys())
        def seed_allowed_groups(seed):
            if seed == 1: return ["A"]
            if seed == 2: return ["B"]
            if seed == "3/4": return ["C", "D"]
            if seed == "5/8": return ["E", "F", "G", "H"]
            return groups

        rows = []
        players_all = list(seed_map.keys())
        seed_priority = {1: 0, 2: 1, "3/4": 2, "5/8": 3}
        seeded_players = sorted([p for p, s in seed_map.items() if s is not None],
                                key=lambda p: seed_priority.get(seed_map[p], 99))

        for sim in range(n_sim):
            slots_left = free_slots.copy()
            seed_slots = {g: 1 for g in groups}
            group_clubs = {g: set() for g in groups}
            unseeded_players = [p for p, s in seed_map.items() if s is None]
            random.shuffle(unseeded_players)
            domains = {}
            for p in players_all:
                base = seed_allowed_groups(seed_map[p])
                if seed_map[p] is not None:
                    domains[p] = [g for g in base if seed_slots[g] > 0 and clubs[p] not in group_clubs[g]]
                else:
                    domains[p] = [g for g in base if slots_left[g] > 0 and clubs[p] not in group_clubs[g]]

            success = False
            for restart in range(max_restarts):
                assignment = {}
                slots = slots_left.copy()
                seeds = seed_slots.copy()
                gclubs = {g: set() for g in groups}
                dom = {p: list(d) for p, d in domains.items()}
                remaining = set(players_all)
                failed = False
                while remaining:
                    min_size = None
                    candidates = []
                    for p in remaining:
                        base = seed_allowed_groups(seed_map[p])
                        if seed_map[p] is not None:
                            cur_dom = [g for g in base if seeds[g] > 0 and clubs[p] not in gclubs[g]]
                        else:
                            cur_dom = [g for g in base if slots[g] > 0 and clubs[p] not in gclubs[g]]
                        if not cur_dom:
                            min_size = 0
                            candidates = [p]
                            break
                        if min_size is None or len(cur_dom) < min_size:
                            min_size = len(cur_dom)
                            candidates = [p]
                        elif len(cur_dom) == min_size:
                            candidates.append(p)
                    if min_size == 0:
                        failed = True
                        break
                    p_sel = random.choice(candidates)
                    base = seed_allowed_groups(seed_map[p_sel])
                    if seed_map[p_sel] is not None:
                        allowed = [g for g in base if seeds[g] > 0 and clubs[p_sel] not in gclubs[g]]
                    else:
                        allowed = [g for g in base if slots[g] > 0 and clubs[p_sel] not in gclubs[g]]
                    if seed_map[p_sel] is not None:
                        chosen = random.choice(allowed)
                    else:
                        weights = [slots[g] for g in allowed]
                        s_tot = sum(weights)
                        if s_tot == 0:
                            failed = True
                            break
                        r = random.random() * s_tot
                        cum = 0.0
                        chosen = allowed[-1]
                        for g, w in zip(allowed, weights):
                            cum += w
                            if r <= cum:
                                chosen = g
                                break
                    assignment[p_sel] = chosen
                    if seed_map[p_sel] is not None:
                        seeds[chosen] -= 1
                    else:
                        slots[chosen] -= 1
                    gclubs[chosen].add(clubs[p_sel])
                    remaining.remove(p_sel)
                if not failed and len(assignment) == len(players_all):
                    for p, g in assignment.items():
                        rows.append({"Player": p, "Group": g, "Simulation": sim})
                    success = True
                    break


            if not success:
                # fallback
                print(f"simulation {sim} has softer rules.")
                slots = slots_left.copy()
                seeds = seed_slots.copy()
                gclubs = {g: set() for g in groups}
                for p in seeded_players + unseeded_players:
                    base = seed_allowed_groups(seed_map[p])
                    allowed = [g for g in base if (seeds[g] if seed_map[p] is not None else slots[g]) > 0]
                    if not allowed:
                        continue
                    chosen = random.choice(allowed)
                    if seed_map[p] is not None:
                        seeds[chosen] -= 1
                    else:
                        slots[chosen] -= 1
                    gclubs[chosen].add(clubs[p])
                    rows.append({"Player": p, "Group": chosen, "Simulation": sim})
        return pd.DataFrame(rows)
        # Fallback never happend during testing


    # Main loop
    counts_per_player = df_all.groupby("Name")["Count"].sum()
    n_sim = int(counts_per_player.median())

    detail_rows = []
    summary_rows = []

    df_all_sims = monte_carlo_mrv(seed_map, free_slots, clubs, n_sim)
    #full_slots = get_full_slots(free_slots)
    #df_all_sims_random = monte_carlo_random(seed_map, full_slots, clubs, n_sim)

    # Pre-calculated frequencies & probabilities
    counts_all = df_all_sims.groupby(["Player", "Group"]).size().unstack(fill_value=0)
    probabilities_all = counts_all / n_sim

    #counts_random = df_all_sims_random.groupby(["Player", "Group"]).size().unstack(fill_value=0)
    #probabilities_random = counts_random / n_sim


    # Monte-Carlo 95 % confidence intervals
    if os.path.basename(file) == "evaluation_all_MS_U13.xlsx":
        n_series = 1
        sim_per_series = 10000
    else:
        n_series = 50 # to have enough samples
        sim_per_series = 200

    series_count = []

    for s in range(n_series):
        # Simulate sim_per_series Tournaments
        df_sim_subset = monte_carlo_mrv(seed_map, free_slots, clubs, sim_per_series)

        # Count per player per group, how much in each series
        counts_subset = (
            df_sim_subset
            .groupby(["Player", "Group"])
            .size()
            .unstack(fill_value=0)
        )
        series_count.append(counts_subset)

    # all series together
    all_series = pd.concat(series_count, keys=range(n_series), names=["Series", "Player"])

    # Calculate quantiles for min/max
    lower_mc_counts = all_series.groupby("Player").quantile(0.025)
    upper_mc_counts = all_series.groupby("Player").quantile(0.975)

    for player in grouped.index:
        counts_obs = grouped.loc[player].values
        total = counts_obs.sum()
        seed_vals = df_all.loc[df_all["Name"] == player, "Seed"].dropna().unique()
        seed_norm = parser_seed(seed_vals[0]) if len(seed_vals) else None
        expected_exact = np.array(expected_distribution(total, seed_norm, all_groups, p_unseeded))
        if seed_norm  in [1, 2, "3/4", "5/8"]:
            # # deterministic expectation, no simulation needed
            for i, g in enumerate(all_groups):
                    detail_rows.append({
                        "Player": player,
                        "Seed": seed_norm,
                        "Group": g,
                        "Observed": counts_obs[i],
                        "Expected_exact": expected_exact[i],
                        "Note": "deterministic"
                    })
            summary_rows.append({
                "Player": player,
                "Seed": seed_norm,
                "Total": int(total),
                "Chi2_theoretical": None,
                "p_theoretical": None,
                "Note": "deterministic"
            })            
        else:
            expected_sim = probabilities_all.loc[player].values
            var_sim = expected_sim * (1 - expected_sim)
            std_sim = np.sqrt(var_sim)
            
            sim_counts = rng.multinomial(int(total), expected_sim, size=n_boot)

            lower = np.percentile(sim_counts, 2.5, axis=0)
            upper = np.percentile(sim_counts, 97.5, axis=0)

            mask = expected_exact > 0
            chi2_theo, p_theo = chisquare(f_obs=counts_obs[mask], f_exp=expected_exact[mask])
            k = mask.sum()
            n = counts_obs[mask].sum()
            cramers_theo = math.sqrt(chi2_theo / (n * (k - 1))) if k > 1 and n > 0 else None

            expected_sim_counts = expected_sim * total
            # Scale only to realistically occupied groups
            mask_sim = expected_sim_counts > 0
            obs = counts_obs[mask_sim]
            exp = expected_sim_counts[mask_sim]

            # Match sums
            if exp.sum() > 0:
                exp *= obs.sum() / exp.sum()

            chi2_sim, p_sim = chisquare(f_obs=obs, f_exp=exp)
            k_sim = mask_sim.sum()
            n_sim_counts = obs.sum()
            cramers_sim = math.sqrt(chi2_sim / (n_sim_counts * (k_sim - 1))) if k_sim > 1 and n_sim_counts > 0 else None

            for i, g in enumerate(all_groups):
                # Simulation results for this group
                sim_counts_group = sim_counts[:, i] 

                p_value_binom = binomtest(
                    k=int(counts_obs[i]),
                    n=int(total),
                    p=float(expected_sim[i])
                ).pvalue

                
                 # Wilson and Jeffreys CI for observed portion
                wilson_lo, wilson_hi = wilson_interval(counts_obs[i], total)
                jeff_lo, jeff_hi = jeffreys_interval(counts_obs[i], total)

                detail_rows.append({
                    "Player": player,
                    "Seed": seed_norm,
                    "Group": g,
                    "Observed": counts_obs[i],
                    "Expected_exact": expected_exact[i],
                    "Expected_simulated_probability": expected_sim[i],
                    "Expected_simulated": expected_sim_counts[i],
                    "Variance_simulated": var_sim[i],
                    "Std_simulated": std_sim[i],
                    "95%_min_binom": int(lower[i]),
                    "95%_max_binom": int(upper[i]),
                    "95%_min_mc": int(lower_mc_counts.loc[player, g]),
                    "95%_max_mc": int(upper_mc_counts.loc[player, g]),
                    "Wilson_low": wilson_lo,
                    "Wilson_high": wilson_hi,
                    "Jeffreys_low": jeff_lo,
                    "Jeffreys_high": jeff_hi,
                    "Within": "Yes" if lower[i] <= counts_obs[i] <= upper[i] else "No",
                    "p_binom": p_value_binom
                })
            yes_count = sum(lower[i] <= counts_obs[i] <= upper[i] for i in range(len(all_groups)))
            pct_in = yes_count / len(all_groups) * 100

            # smallest binom p value
            min_binom_p = min(
                binomtest(
                    k=int(counts_obs[i]),
                    n=int(total),
                    p=float(expected_sim[i])
                ).pvalue
                for i in range(len(all_groups))
            )

            summary_rows.append({
                "Player": player,
                "Seed": seed_norm,
                "Total": int(total),
                "Chi2_theoretical": chi2_theo,
                "p_theoretical": p_theo,
                "CramersV_theoretical": cramers_theo,
                "Chi2_simulated": chi2_sim,
                "p_simulated": p_sim,
                "CramersV_simulated": cramers_sim,
                "Variance_simulated_avg": var_sim.mean(),
                "Within_95%": pct_in,
                "min_p_binom": min_binom_p
            })

    # Export
    df_detail = pd.DataFrame(detail_rows)
    df_summary = pd.DataFrame(summary_rows)

    # Generate output file path
    base_name = os.path.splitext(os.path.basename(file))[0]
    output_file = os.path.join(output_folder, f"analysis_{base_name}.xlsx")

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_detail.to_excel(writer, sheet_name="Detail", index=False)
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
    
    print(f"Saved: {output_file}")

"""
df_compare = probabilities_all.copy()
df_compare.columns = [f"{g}_MRV" for g in df_compare.columns]

for g in probabilities_random.columns:
    df_compare[f"{g}_Random"] = probabilities_random[g]

for g in probabilities_all.columns:
    df_compare[f"{g}_Diff"] = (probabilities_all[g] - probabilities_random[g]).abs()

df_compare.to_excel(r"D:\Maturaarbeit\compare_mrv_vs_random.xlsx", index=False)
"""

print("Finished")
