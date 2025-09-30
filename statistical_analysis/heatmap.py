import pandas as pd
import numpy as np
import plotly.graph_objects as go
import argparse
import os


parser = argparse.ArgumentParser(description="Generate heatmaps from simulation results.")
parser.add_argument(
    "input_file",
    nargs="?",
    default=r"D:\Maturaarbeit\analysis_results\analysis_evaluation_all_MS_U13.xlsx",
    help="Path to the Excel file with simulation results (default: standard file)"
)
parser.add_argument("--pairs_file", help="Optional Excel file with pairings (sheet 'Pairs of 2')", default=None)
parser.add_argument("--outdir", default=".", help="Output directory for saving plots")
args = parser.parse_args()


# Load Excel
required_cols = {"Player", "Group", "Observed", "Expected_exact", "Expected_simulated"}
xls = pd.ExcelFile(args.input_file)

df = None
for sheet_name in reversed(xls.sheet_names):
    tmp = pd.read_excel(args.input_file, sheet_name=sheet_name)
    if required_cols.issubset(tmp.columns):
        df = tmp
        print(f"Loaded data from sheet '{sheet_name}'")
        break

if df is None:
    raise ValueError(f"No sheet found containing required columns: {required_cols}")


# Heatmap 1: Observed players x groups
groups = sorted(df["Group"].unique())
obs_pivot = (
    df.pivot_table(index="Player", columns="Group", values="Observed",
                   aggfunc="sum", fill_value=0)
      .reindex(columns=groups, fill_value=0)
      .sort_index()
)
deterministic_players = df.loc[df["Seed"].notna(), "Player"].unique()

# Create matrices for unseeded and seeded players
obs_unseeded = obs_pivot.copy()
obs_unseeded.loc[deterministic_players, :] = np.nan  # seeded will not affect color

obs_seeded = obs_pivot.copy()
obs_seeded.loc[~obs_seeded.index.isin(deterministic_players), :] = np.nan  # keep only seeded

# Max value for unseeded players (for color scaling)
max_unseeded = np.nanmax(obs_unseeded.values)

# Hovertext
hover_text = np.empty(obs_pivot.shape, dtype=object)
for i, player in enumerate(obs_pivot.index):
    for j, group in enumerate(obs_pivot.columns):
        val = obs_pivot.iloc[i, j]
        if pd.isna(val):
            hover_text[i, j] = f"Player = {player}<br>Group = {group}<br>Observed = –"
        else:
            hover_text[i, j] = f"Player = {player}<br>Group = {group}<br>Observed = {val}"

display_text = np.empty(obs_pivot.shape, dtype=object)
for i, player in enumerate(obs_pivot.index):
    for j, group in enumerate(obs_pivot.columns):
        val = obs_pivot.iloc[i, j]
        display_text[i, j] = "" if pd.isna(val) else str(val)

fig = go.Figure()

# Layer 1: unseeded players
fig.add_trace(go.Heatmap(
    z=obs_unseeded.values,
    x=obs_unseeded.columns,
    y=obs_unseeded.index,
    colorscale="Blues",
    zmin=0,
    zmax=max_unseeded,
    colorbar=dict(title="Observed Count"),
    text=display_text.tolist(),
    texttemplate="%{text}",
    customdata=hover_text.tolist(),
    hovertemplate="%{customdata}<extra></extra>"
))

# Layer 2: seeded players
fig.add_trace(go.Heatmap(
    z=np.where(obs_seeded.notna(), 1, np.nan),
    x=obs_seeded.columns,
    y=obs_seeded.index,
    zmin=1, zmax=1,
    colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgb(245, 245, 220)']],
    text=None,
    texttemplate="%{text}",
    customdata=hover_text.tolist(),
    hovertemplate="%{customdata}<extra></extra>",
    showscale=False
))

fig.update_layout(title="Observed Distribution per Player (seeded players grey)")
fig.write_html(os.path.join(args.outdir, "heatmap_observed.html"), include_plotlyjs="cdn")

# Heatmaps 2 and 3: Residuals (common z-limit for consistent color scale)

resid_exact = df.assign(
    Residual=df["Observed"] - df["Expected_exact"]
).pivot(index="Player", columns="Group", values="Residual")

resid_sim = df.assign(
    Residual=df["Observed"] - df["Expected_simulated"]
).pivot(index="Player", columns="Group", values="Residual")

# compute common z-limit across both residual matrices
zlim = float(np.nanmax(np.abs([resid_exact.values, resid_sim.values])))

fig2 = go.Figure()

# Layer 1: unseeded players (residuals exact)
resid_exact_unseeded = resid_exact.copy()
resid_exact_unseeded.loc[deterministic_players, :] = np.nan  # mask seeded
fig2.add_trace(go.Heatmap(
    z=resid_exact_unseeded.values,
    x=resid_exact_unseeded.columns,
    y=resid_exact_unseeded.index,
    colorscale="RdBu",
    zmid=0,
    zmin=-zlim, zmax=zlim,     
    colorbar=dict(title="Residual (Obs - Exp Exact)"),
    text=resid_exact_unseeded.values,
    texttemplate="%{text:.0f}",
    hovertemplate="Player = %{y}<br>Group = %{x}<br>Residual = %{z}<extra></extra>"
))

# Layer 2: seeded players
resid_exact_seeded = resid_exact.copy()
resid_exact_seeded.loc[~resid_exact_seeded.index.isin(deterministic_players), :] = np.nan
resid_exact_seeded.loc[deterministic_players, :] = 1  # constant value
fig2.add_trace(go.Heatmap(
    z=np.where(resid_exact_seeded.notna(), 1, np.nan),
    x=resid_exact_seeded.columns,
    y=resid_exact_seeded.index,
    zmin=1, zmax=1,
    colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgb(245, 245, 220)']],
    showscale=False,
    hoverinfo="skip"
))

fig2.update_layout(title="Residuals: Observed - Expected (Exact)")
fig2.write_html(os.path.join(args.outdir, "heatmap_observed-expected.html"), include_plotlyjs="cdn")

# Heatmap 3: Observed vs Expected Simulated (residuals)
fig3 = go.Figure()

# Layer 1: unseeded players
resid_sim_unseeded = resid_sim.copy()
resid_sim_unseeded.loc[deterministic_players, :] = np.nan
fig3.add_trace(go.Heatmap(
    z=resid_sim_unseeded.values,
    x=resid_sim_unseeded.columns,
    y=resid_sim_unseeded.index,
    colorscale="RdBu",
    zmid=0,
    zmin=-zlim, zmax=zlim,     # use same common z-limit
    colorbar=dict(title="Residual (Obs - Exp Simulated)"),
    text=resid_sim_unseeded.values,
    texttemplate="%{text:.0f}",
    hovertemplate="Player = %{y}<br>Group = %{x}<br>Residual = %{z}<extra></extra>"
))

# Layer 2: seeded players
resid_sim_seeded = resid_sim.copy()
resid_sim_seeded.loc[~resid_sim_seeded.index.isin(deterministic_players), :] = np.nan
resid_sim_seeded.loc[deterministic_players, :] = 1
fig3.add_trace(go.Heatmap(
    z=np.where(resid_sim_seeded.notna(), 1, np.nan),
    x=resid_sim_seeded.columns,
    y=resid_sim_seeded.index,
    zmin=1, zmax=1,
    colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgb(245, 245, 220)']],
    showscale=False,
    hoverinfo="skip"
))

fig3.update_layout(title="Residuals: Observed - Expected (Simulated)")
fig3.write_html(os.path.join(args.outdir, "heatmap_observed-expected_simulated.html"), include_plotlyjs="cdn")

# Heatmap 4: Player x Player pairings
pair_df = pd.read_excel(
    r"D:\Maturaarbeit\evaluations\evaluation_all_MS_U13.xlsx",
    sheet_name="Pairs of 2"
)

players = sorted(set(pair_df["Player 1"]).union(pair_df["Player 2"]))

# Create empty symmetric matrix
matrix = pd.DataFrame(0, index=players, columns=players)

# Fill matrix with counts
for _, row in pair_df.iterrows():
    a, b, count = row["Player 1"], row["Player 2"], row["Count"]
    matrix.loc[a, b] = count
    matrix.loc[b, a] = count  # symmetric

fig_pair = go.Figure()

fig_pair.add_trace(go.Heatmap(
    z=matrix.values,
    x=matrix.columns,
    y=matrix.index,
    colorscale="Blues",
    colorbar=dict(title="Times Together"),
    text=matrix.values,
    texttemplate="%{text}",
    hovertemplate="Player 1 = %{y}<br>Player 2 = %{x}<br>Count = %{z}<extra></extra>"
))

# second layer for seeded players
mask = pd.DataFrame(np.nan, index=players, columns=players)

for p in deterministic_players:
    if p in mask.index: 
        mask.loc[p, :] = 1 
        mask.loc[:, p] = 1 

fig_pair.add_trace(go.Heatmap(
    z=mask.values,
    x=mask.columns,
    y=mask.index,
    colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(200,200,200,0.4)"]],  
    showscale=False,
    hoverinfo="skip"
))

fig_pair.update_layout(title="Player Pairings Heatmap (grey layer for seeded players)")
fig_pair.write_html(os.path.join(args.outdir, "heatmap_pairs.html"), include_plotlyjs="cdn")
