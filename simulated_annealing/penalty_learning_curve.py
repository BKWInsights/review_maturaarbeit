import pandas as pd
import numpy as np
import plotly.graph_objects as go
import argparse, os
import plotly.express as px
import webbrowser
import random

history_versions = [0,1,2,3,4,5,"full"]
dfs = {}

base_dir = os.getcwd()

for v in history_versions:
    if v == "full":
        file = os.path.join(base_dir, "penalty_history_all_full_history.csv")
    else:
        file = os.path.join(base_dir, f"penalty_history_all_hist{v}.csv")
    
    if not os.path.exists(file):
        print(f"[Warning] File not found: {file}")
        continue


    df = pd.read_csv(file)
    df["Delta"] = df["Penalty"] - df.groupby("Simulation")["Penalty"].transform("first")
    dfs[v] = df

parser = argparse.ArgumentParser(description="Visualize penalty progression.")
parser.add_argument("--input", default=r"D:\Maturaarbeit\penalty_history.csv", help="Path to penalty_history.csv")
parser.add_argument("--sample_size", type=int, default=10, help="Number of samples (sample mode only)")
parser.add_argument("--legend_every", type=int, default=50, help="Every Nth simulation gets a legend entry")
parser.add_argument("--out", default="penalty_progression.html", help="Output HTML file name")
args = parser.parse_args()

if not os.path.exists(args.input):
    raise FileNotFoundError(f"Input file not found: {args.input}")

df_penalty = pd.read_csv(args.input)

required = {"Simulation", "Iteration", "Penalty"}
if not required.issubset(df_penalty.columns):
    raise ValueError(f"Missing columns: {required - set(df_penalty.columns)}")

df_penalty = (
    df_penalty
    .dropna(subset=required)
    .astype({"Simulation": "int64", "Iteration": "int64"})
    .sort_values(["Simulation", "Iteration"])
    .drop_duplicates(["Simulation", "Iteration"], keep="last")
)

# Ensure data types
df_penalty["Simulation"] = pd.to_numeric(df_penalty["Simulation"], errors="coerce").astype("Int64")
df_penalty["Iteration"] = pd.to_numeric(df_penalty["Iteration"], errors="coerce").astype("Int64")
df_penalty["Penalty"] = pd.to_numeric(df_penalty["Penalty"], errors="coerce")
df_penalty["Delta"] = (
    df_penalty["Penalty"] 
    - df_penalty.groupby("Simulation")["Penalty"].transform("first")
)

colors = px.colors.qualitative.Bold
outputs = []

for v_idx, v in enumerate(history_versions):
    df_penalty = dfs[v]
    fig = go.Figure()

    # --- Median + Perzentilband ---
    agg = df_penalty.groupby("Iteration")["Penalty"].agg(
        median="median",
        p10=lambda x: np.percentile(x, 10),
        p90=lambda x: np.percentile(x, 90)
    ).reset_index()

    fig.add_trace(go.Scatter(
        x=pd.concat([agg["Iteration"], agg["Iteration"][::-1]]),
        y=pd.concat([agg["p90"], agg["p10"][::-1]]),
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name="10–90 %"
    ))

    fig.add_trace(go.Scatter(
        x=agg["Iteration"],
        y=agg["median"],
        mode="lines",
        name="Median",
        line=dict(color="green", width=2),
        hovertemplate="Iteration: %{x}<br>Median Penalty: %{y:.2f}<extra></extra>"
    ))

    # --- Best Improvement ---
    df_start = df_penalty.groupby("Simulation")["Penalty"].first()
    df_end   = df_penalty.groupby("Simulation")["Penalty"].last()
    improvement = df_end - df_start
    best_improvement = improvement.idxmin()

    df_best = df_penalty[df_penalty["Simulation"] == best_improvement].sort_values("Iteration")
    fig.add_trace(go.Scattergl(
        x=df_best["Iteration"],
        y=df_best["Penalty"],
        mode="lines",
        name=f"Best Improvement (Sim {best_improvement})",
        line=dict(width=3.5, color="red"),
        opacity=1.0,
        text=[best_improvement]*len(df_best),
        customdata=df_best["Delta"],
        hovertemplate="Best Simulation: %{text}<br>Iteration: %{x}<br>Penalty: %{y:.2f}<br>ΔPenalty: %{customdata:.2f}<extra></extra>"
    ))

    # --- Alle Simulationen als unsichtbare Traces ---
    sim_traces = []
    for sim, df_sim in df_penalty.groupby("Simulation"):
        df_sim = df_sim.sort_values("Iteration")
        fig.add_trace(go.Scattergl(
            x=df_sim["Iteration"],
            y=df_sim["Penalty"],
            mode="lines",
            name=f"Sim {sim}",
            opacity=0.3,
            showlegend=False,
            text=[sim]*len(df_sim),
            customdata=df_sim["Delta"],
            hovertemplate="Simulation: %{text}<br>Iteration: %{x}<br>Penalty: %{y:.2f}<br>ΔPenalty: %{customdata:.2f}<extra></extra>",
            visible=False
        ))
        sim_traces.append(sim)

    # --- Gruppen bilden ---
    n_sims = df_penalty["Simulation"].nunique()
    if v == "full":
        group_size = 100
    elif isinstance(v, int) and v > 0:
        group_size = v + 1
    else:  # hist=0
        group_size = 50

    sims = sorted(df_penalty["Simulation"].unique())
    groups = [sims[i:i+group_size] for i in range(0, len(sims), group_size)]

    # Stichprobe: max. 20 Gruppen
    if len(groups) > 20:
        sampled_groups = random.sample(groups, 20)
    else:
        sampled_groups = groups

    # --- Dropdown Buttons ---
    base_visible = [True, True, True] + [False]*(len(fig.data)-3)
    group_buttons = []

    for grp in sampled_groups:
        vis = base_visible.copy()
        for i, trace in enumerate(fig.data[3:], start=3):
            sim_id = int(trace.name.split()[-1])
            if sim_id in grp:
                vis[i] = True
        label = f"Sim {grp[0]}–{grp[-1]}"
        group_buttons.append(dict(
            label=label,
            method="update",
            args=[{"visible": vis}]
        ))

    fig.update_layout(
        updatemenus=[dict(
            type="dropdown",
            buttons=group_buttons,
            x=1.05, y=1.05
        )],
        showlegend=True
    )

    # --- Ausgabe pro Version ---
    outname = f"penalty_progression_hist{v}.html"
    fig.write_html(outname, auto_open=False)
    outputs.append(outname)
    print(f"Saved {outname}")

# Am Ende alle Dateien im Browser öffnen
for out in outputs:
    webbrowser.open('file://' + os.path.realpath(out))
