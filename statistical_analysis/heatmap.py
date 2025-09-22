import pandas as pd
import plotly.graph_objects as go

# Load Excel
file = r"D:\Maturaarbeit\simulation_results.xlsx"
df = pd.read_excel(file)

# Heatmap 1: Observed
obs_pivot = df.pivot(index="Player", columns="Group", values="Observed")

fig1 = go.Figure(data=go.Heatmap(
    z=obs_pivot.values,
    x=obs_pivot.columns,
    y=obs_pivot.index,
    colorscale="Blues",
    colorbar=dict(title="Observed Count"),
    text=obs_pivot.values,               # add text
    texttemplate="%{text}",              # show as plain number
    hovertemplate="Player=%{y}<br>Group=%{x}<br>Observed=%{z}<extra></extra>"
))
fig1.update_layout(title="Observed Distribution per Player")
fig1.show()

#  Heatmap 2: Observed vs Expected Exact (residuals) 
resid_exact = df.assign(
    Residual=df["Observed"] - df["Expected_exact"]
).pivot(index="Player", columns="Group", values="Residual")

fig2 = go.Figure(data=go.Heatmap(
    z=resid_exact.values,
    x=resid_exact.columns,
    y=resid_exact.index,
    colorscale="RdBu",
    zmid=0,
    colorbar=dict(title="Residual (Obs - Exp Exact)"),
    text=resid_exact.values,
    texttemplate="%{text:.0f}",          # format as integer
    hovertemplate="Player=%{y}<br>Group=%{x}<br>Residual=%{z}<extra></extra>"
))
fig2.update_layout(title="Residuals: Observed - Expected (Exact)")
fig2.show()

# Heatmap 3: Observed vs Expected Simulated (residuals)
resid_sim = df.assign(
    Residual=df["Observed"] - df["Expected_simulated"]
).pivot(index="Player", columns="Group", values="Residual")

fig3 = go.Figure(data=go.Heatmap(
    z=resid_sim.values,
    x=resid_sim.columns,
    y=resid_sim.index,
    colorscale="RdBu",
    zmid=0,
    colorbar=dict(title="Residual (Obs - Exp Simulated)"),
    text=resid_sim.values,
    texttemplate="%{text:.0f}",
    hovertemplate="Player=%{y}<br>Group=%{x}<br>Residual=%{z}<extra></extra>"
))
fig3.update_layout(title="Residuals: Observed - Expected (Simulated)")
fig3.show()

