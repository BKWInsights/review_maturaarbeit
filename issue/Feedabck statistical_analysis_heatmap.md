Zuerst einmal: Die README für diesen Teil deines Projekts ist exzellent. Sie erklärt die Methodik der statistischen Analyse und die Rolle der Heatmaps klar und präzise. Das allein ist schon auf sehr hohem Niveau.

Dein Skript ist schön kompakt und die Visualisierungen treffen genau den Kern deiner Analyse. Die `README` ist professionell, und die interaktiven Plotly-Heatmaps sind eine hervorragende Wahl. Die Nutzung von `hovertemplate` und `zmid` ist bereits sehr gut.

Hier ist der finale Feinschliff, der dein Skript von "sehr gut" zu "absolut robust und professionell" macht.

-----

### Kritische Fixes & Robuste Datenverarbeitung 🐞

Diese Punkte stellen sicher, dass dein Skript nicht nur unter Idealbedingungen, sondern auch mit leichten Abweichungen in den Daten zuverlässig funktioniert.

**1. Automatisches Finden des richtigen Sheets & Spalten-Check**

  * **Problem**: Das Skript bricht ab, wenn das Sheet nicht exakt "Detail" heisst oder Spalten fehlen.
  * **Robuster Fix**: Lass das Skript automatisch nach dem richtigen Sheet suchen und prüfe die Spalten.
    ```python
    import pandas as pd
    import numpy as np # Wird später benötigt
    
    file_path = r"D:\Maturaarbeit\simulation_results.xlsx"
    xls = pd.ExcelFile(file_path)
    
    required = {"Player", "Group", "Observed", "Expected_exact", "Expected_simulated"}
    df = None
    # Durchsuche Sheets (bevorzugt von hinten, falls es am Ende liegt)
    for sheet_name in reversed(xls.sheet_names):
        temp_df = pd.read_excel(xls, sheet_name=sheet_name)
        if required.issubset(temp_df.columns):
            df = temp_df
            print(f"Daten aus Sheet '{sheet_name}' geladen.")
            break
            
    if df is None:
        raise ValueError(f"Kein Sheet mit den erforderlichen Spalten gefunden: {required}")
    ```

**2. `pivot_table` & Feste Achsenordnung für Stabilität**

  * **Problem**: `pivot()` ist nicht robust gegen Duplikate. Zudem kann eine fehlende Gruppe die Achsen verschieben, was Vergleiche unmöglich macht.
  * **Sicherer Fix**: Nutze `pivot_table` und erzwinge eine feste, sortierte Achsenordnung.
    ```python
    groups = list("ABCDEFGHIJK") # Feste Reihenfolge für die X-Achse
    obs_pivot = (df.pivot_table(index="Player", columns="Group",
                                values="Observed", aggfunc="sum", fill_value=0)
                   .reindex(columns=groups, fill_value=0)
                   .sort_index()) # Spieler alphabetisch sortieren
    ```

**3. Wichtiger Check: Sind deine "Expected" Werte Counts oder Wahrscheinlichkeiten?**

  * **Gedanke**: Deine `Observed`-Werte sind Zählungen. Stelle sicher, dass `Expected_exact` und `Expected_simulated` ebenfalls Zählungen sind. Falls es sich um Wahrscheinlichkeiten (Werte zwischen 0 und 1) handelt, musst du sie **vor der Subtraktion** mit der Gesamtzahl der Draws multiplizieren, sonst sind deine Residuen-Heatmaps nicht korrekt.

-----

### Visuelle Exzellenz & Analytische Tiefe 📊

  * **Eine gemeinsame, symmetrische Skala für faire Vergleiche**

      * **Problem**: Damit die Farben in den beiden Residual-Plots exakt dasselbe bedeuten, müssen sie dieselbe Skala haben (z.B. von -10 bis +10).
      * **Fix**: Finde den maximalen Absolutwert über *beide* Residual-Matrizen und nutze ihn als gemeinsame Grenze.
        ```python
        # Annahme: resid_exact und resid_sim sind als robuste pivot_tables erstellt
        zlim = float(np.nanmax(np.abs([resid_exact.values, resid_sim.values])))
  
        # In go.Heatmap für beide Plots verwenden:
        # zmid=0, zmin=-zlim, zmax=zlim
        ```

  * **Pro-Tipp: Heatmap für statistische Signifikanz**

      * **Idee**: Eine dritte Residual-Heatmap mit **standardisierten Residuen** zeigt dir, welche Abweichungen statistisch am auffälligsten sind.
      * **Umsetzung**:
        ```python
        # Berechne standardisierte Residuen (vermeidet Division durch Null)
        exp = df["Expected_exact"].clip(lower=1e-9)
        df["Std_Residual"] = (df["Observed"] - exp) / np.sqrt(exp)
        # Werte > 2 oder < -2 sind hier besonders interessant!
        ```

  * **Sinnvolle Y-Achsen-Sortierung**

      * **Tipp**: Wenn deine Daten eine "Seed"-Spalte enthalten, sortiere die Spieler danach. Das kann Muster aufdecken, die bei alphabetischer Sortierung verborgen bleiben.

-----

### Professionelle Skript-Struktur & Anwendung 🔧

  * **Kommandozeilen-Argumente (`argparse`) statt fester Pfade**

      * **Tipp**: Mache dein Skript portabel und wiederverwendbar.
        ```python
        import argparse
        parser = argparse.ArgumentParser(description="Generate heatmaps from simulation results.")
        parser.add_argument("input_file", help="Path to simulation_results.xlsx")
        parser.add_argument("--outdir", default=".", help="Directory to save output files")
        args = parser.parse_args()
  
        # file = args.input_file
        ```

  * **Code-Wiederholung mit einer Schleife eliminieren (DRY)**

      * Erstelle die beiden Residual-Heatmaps in einer eleganten Schleife, um Code-Duplikation zu vermeiden.

  * **Plots speichern & Layout-Details**

      * **Wichtig**: Speichere die Plots für deine Maturaarbeit\!
        ```python
        fig.write_html(f"{args.outdir}/heatmap_final.html", include_plotlyjs="cdn")
        fig.write_image(f"{args.outdir}/heatmap_final.png") # braucht 'pip install kaleido'
        ```
      * **Feinschliff**: Füge `xgap=1, ygap=1` zu `go.Heatmap` für ein sauberes Gitter hinzu und nutze `fig.update_layout(height=max(500, 18 * len(obs_pivot)))` für eine dynamische Höhe.