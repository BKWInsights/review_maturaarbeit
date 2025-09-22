import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Parameters
penalty_file = r"D:\Maturaarbeit\penalty_history.csv"

# Choose mode: "all" or "sample"
# "all"    = each simulation individually
# "sample" = aggregate lines + percentile bands + sample
mode = "all"

# Number of random simulations in sample mode
sample_size = 10

# Load data
df_penalty = pd.read_csv(penalty_file)

# Ensure data types
df_penalty["Simulation"] = pd.to_numeric(df_penalty["Simulation"], errors="coerce").astype("Int64")
df_penalty["Iteration"] = pd.to_numeric(df_penalty["Iteration"], errors="coerce").astype("Int64")
df_penalty["Penalty"] = pd.to_numeric(df_penalty["Penalty"], errors="coerce")

# Create plot
fig = go.Figure()

if mode == "all":
    # Each simulation as its own line
    for sim, df_sim in df_penalty.groupby("Simulation"):
        df_sim = df_sim.sort_values("Iteration")
        fig.add_trace(go.Scatter(
            x=df_sim["Iteration"],
            y=df_sim["Penalty"],
            mode="lines",
            name=f"Sim {sim}",
            hovertemplate="Simulation: %{text}<br>Iteration: %{x}<br>Penalty: %{y}<extra></extra>",
            text=[sim]*len(df_sim),
            opacity=0.4
        ))

elif mode == "sample":
    # Aggregation per iteration
    agg = df_penalty.groupby("Iteration")["Penalty"].agg(
        median="median",
        p10=lambda x: np.percentile(x, 10),
        p90=lambda x: np.percentile(x, 90)
    ).reset_index()

    # Percentile band
    fig.add_trace(go.Scatter(
        x=pd.concat([agg["Iteration"], agg["Iteration"][::-1]]),
        y=pd.concat([agg["p90"], agg["p10"][::-1]]),
        fill='toself',
        fillcolor='rgba(0,100,80,0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        name="10–90 %"
    ))

    # Median line
    fig.add_trace(go.Scatter(
        x=agg["Iteration"],
        y=agg["median"],
        mode="lines",
        name="Median",
        line=dict(color="red", width=2)
    ))

    # Sample of random simulations
    sample_sims = df_penalty["Simulation"].drop_duplicates().sample(sample_size, random_state=42)
    for sim, df_sim in df_penalty[df_penalty["Simulation"].isin(sample_sims)].groupby("Simulation"):
        df_sim = df_sim.sort_values("Iteration")
        fig.add_trace(go.Scatter(
            x=df_sim["Iteration"],
            y=df_sim["Penalty"],
            mode="lines",
            name=f"Sim {sim}",
            opacity=0.3
        ))

# Layout
fig.update_layout(
    title="Penalty progression per simulation (interactive)",
    xaxis_title="Iteration",
    yaxis_title="Penalty",
    hovermode="closest",
    legend=dict(
        title="Simulations",
        itemsizing="constant"
    )
)

fig.show()
