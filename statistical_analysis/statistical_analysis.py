import pandas as pd
import numpy as np
from scipy.stats import chisquare, ttest_1samp, ttest_ind, f
import math, random, glob, os
# from vergleichsbasis_random import monte_carlo_random, get_full_slots

# Folder with all evaluation files
input_folder = "D:\Maturaarbeit\evaluations"

# Output folder
output_folder = r"D:\Maturaarbeit\analysis_results"
os.makedirs(output_folder, exist_ok=True)

# Collect all Excel files
excel_files = glob.glob(os.path.join(input_folder, "*.xlsx"))

for file in excel_files:
    print(f"Processing: {os.path.basename(file)}")

    # Load 6th sheet
    try:
        df_all = pd.read_excel(file, sheet_name=5, engine="openpyxl")
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
    clubs = df_all.set_index("Name")["Club"].to_dict()

    # Create seed map
    seed_map = {
        name: parser_seed(df_all.loc[df_all["Name"] == name, "Seed"].dropna().unique()[0])
        if len(df_all.loc[df_all["Name"] == name, "Seed"].dropna().unique()) else None
        for name in grouped.index
    }

    # Helper function: allowed groups by seed
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

    # Monte Carlo with MRV (slightly shortened)
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

            # MUST CHANGE
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

    # Main loop
    total_draws = df_all["Count"].sum() / df_all["Name"].nunique()
    n_sim = int(total_draws)
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

    for player in grouped.index:
        counts_obs = grouped.loc[player].values
        total = counts_obs.sum()
        seed_vals = df_all.loc[df_all["Name"] == player, "Seed"].dropna().unique()
        seed_norm = parser_seed(seed_vals[0]) if len(seed_vals) else None
        expected_exact = np.array(expected_distribution(total, seed_norm, all_groups, p_unseeded))
        if seed_norm not in [1, 2, "3/4", "5/8"]:
            expected_sim = probabilities_all.loc[player].values
            var_sim = expected_sim * (1 - expected_sim)
            std_sim = np.sqrt(var_sim)
            counts_per_group = np.random.binomial(
                n=total,
                p=expected_sim,
                size=(n_sim, len(all_groups))
            )
            lower = np.percentile(counts_per_group, 2.5, axis=0)
            upper = np.percentile(counts_per_group, 97.5, axis=0)
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
                sim_counts = counts_per_group[:, i]  # from the existing simulation

                # t-test: checks if the mean of the simulation = observed value
                t_stat, p_t = ttest_1samp(sim_counts, counts_obs[i])

                # F-test: checks if the variance of the simulation = variance of the observation
                # (here as ratio of variances; observation is only 1 value, so modeled as deviation from expected value)
                var_sim_i = np.var(sim_counts, ddof=1)
                var_obs_i = (counts_obs[i] - expected_sim_counts[i])**2  # squared deviation as "variance" for 1 observation
                f_stat = var_sim_i / (var_obs_i if var_obs_i != 0 else 1e-10)

                # p-value for F-test (two-sided)
                dfn = len(sim_counts) - 1
                dfd = 1  # observation = 1 value
                p_f = 2 * min(f.cdf(f_stat, dfn, dfd), 1 - f.cdf(f_stat, dfn, dfd))
                
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
                    "95%_min": int(lower[i]),
                    "95%_max": int(upper[i]),
                    "Within": "Yes" if lower[i] <= counts_obs[i] <= upper[i] else "No",
                    "t_stat": t_stat,
                    "p_t": p_t,
                    "f_stat": f_stat
                })
            yes_count = sum(lower[i] <= counts_obs[i] <= upper[i] for i in range(len(all_groups)))
            pct_in = yes_count / len(all_groups) * 100

            # t- and F-test against the theoretical expectation
            # Observed frequencies in all groups
            obs_count = counts_obs.astype(float)
            # Expected frequencies (theoretical)
            exp_counts = expected_exact.astype(float)

            # F-test: variance comparison
            var_obs = np.var(obs_count, ddof=1)
            var_exp = np.var(exp_counts, ddof=1)
            if var_obs > var_exp:
                f_stat = var_obs / var_exp
                dfn, dfd = len(obs_count) - 1, len(exp_counts) - 1
            else:
                f_stat = var_exp / var_obs
                dfn, dfd = len(exp_counts) - 1, len(obs_count) - 1
            p_f = 2 * min(f.cdf(f_stat, dfn, dfd), 1 - f.cdf(f_stat, dfn, dfd))

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
                "f_stat": f_stat,
                "p_f": p_f
            })

    # Export
    df_detail = pd.DataFrame(detail_rows)
    df_summary = pd.DataFrame(summary_rows)

    # Generateoutput file path
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