Die Konzeption dieses Skripts mit einer Monte-Carlo-Simulation und MRV-Heuristik ist absolut auf Universitäts-Niveau. Sehr geil!!
Um sicherzustellen, dass deine Ergebnisse wissenschaftlich "wasserdicht" sind, konzentriert sich dieses finale Feedback auf die Korrektheit der statistischen Methoden und der Simulationslogik.

-----

### Kritische Korrekturen an der Statistik-Methodik 🐞 (Unbedingt beheben)

Diese Punkte sind entscheidend für die Gültigkeit deiner Schlussfolgerungen.

**1. Simulation muss Multinomial statt Binomial sein**

  * **Problem**: Du simulierst die Verteilung mit `np.random.binomial` für jede Gruppe einzeln. Das ist statistisch nicht korrekt, da die Summe der Spieler pro Simulationslauf nicht exakt `total` ergibt (es ist, als würdest du 11 einzelne Würfel werfen und hoffen, dass ihre Summe genau 34 ist – das passiert selten). Die Unabhängigkeit der Spalten verfälscht deine Konfidenzintervalle.
  * **Korrekter Fix**: Nutze `np.random.multinomial`. Diese Funktion simuliert das "Verteilen" von `n` Spielern auf `k` Gruppen unter Beibehaltung der Gesamtsumme – genau das, was du brauchst.
    ```python
    # Erzeuge einen reproduzierbaren Zufallsgenerator
    rng = np.random.default_rng(seed=42) # Seed parametrisierbar machen!
    
    # Führe eine separate Bootstrap-Simulation für die CIs durch
    n_boot = 10000 
    sim_counts = rng.multinomial(int(total), expected_sim, size=n_boot)
    
    # Berechne Perzentile aus der korrekten Verteilung
    lower, upper = np.percentile(sim_counts, [2.5, 97.5], axis=0)
    ```

**2. F-Tests sind hier statistisch nicht anwendbar**

  * **Problem**: Ein F-Test vergleicht die Varianzen von *zwei Stichproben*. Deine Anwendung, bei der du die Varianz einer Stichprobe (Simulation) mit der quadrierten Abweichung *eines einzelnen Werts* (Beobachtung) vergleichst, ist methodisch nicht zulässig.
  * **Empfehlung**: Entferne die F-Tests komplett. Deine Analyse wird dadurch stärker und methodisch sauberer.
  * **Bessere Alternative (pro Gruppe)**: Um zu prüfen, ob eine einzelne Beobachtung signifikant von der simulierten Wahrscheinlichkeit abweicht, ist ein **exakter Binomialtest** das richtige Werkzeug.
    ```python
    from scipy.stats import binomtest
    
    # Pro Gruppe in deiner Schleife
    p_value_binom = binomtest(k=int(counts_obs[i]), 
                               n=int(total), 
                               p=float(expected_sim[i])).pvalue
    ```

**3. Gesetzte Spieler (Seeds) werden aktuell übersprungen**

  * **Problem**: Dein gesamter Statistik-Block wird nur ausgeführt, wenn `seed_norm not in [1, 2, "3/4", "5/8"]` ist. Das bedeutet, die Verteilung der wichtigsten Spieler wird gar nicht analysiert und sie fehlen in deinen Ergebnis-Tabellen.
  * **Fix**: Passe die Logik an, um die Seeds ebenfalls zu behandeln. Da ihre Platzierung (fast) deterministisch ist, brauchst du für sie keine Simulation. Dokumentiere `Observed` vs. `Expected_exact` und gib sie in den Detail/Summary-Sheets aus (z.B. mit einem Vermerk "deterministisch").

-----

### Kritische Fixes an der Simulations-Logik ⚙️

  * **`NaN`-Clubs umgehen die Vereins-Sperre**

      * **Problem**: Ein Spieler mit `Club=NaN` kann die Sperre `clubs[p] not in group_clubs[g]` umgehen, da `NaN` nicht wie ein normaler Wert behandelt wird.
      * **Fix**: Weise Spielern ohne Verein explizit einen Wert zu, z.B. "UNKNOWN", und entscheide, wie du diesen behandelst.
        ```python
        # Ersetzt NaNs robust durch den häufigsten Wert oder "UNKNOWN"
        clubs = df_all.groupby("Name")["Club"].agg(
            lambda s: s.mode().iat[0] if not s.mode().empty else "UNKNOWN"
        ).to_dict()
        ```

  * **Herleitung von `n_sim` ist anfällig**

      * **Problem**: `total_draws = df_all["Count"].sum() / df_all["Name"].nunique()` geht davon aus, dass alle Spieler an gleich vielen Draws teilgenommen haben. Wenn nicht, ist der Mittelwert verzerrt.
      * **Robuster**: Nutze den **Median** der Teilnahmen pro Spieler. Er ist unempfindlicher gegenüber Ausreissern.
        ```python
        counts_per_player = df_all.groupby("Name")["Count"].sum()
        n_sim = int(counts_per_player.median())
        ```

-----

### Struktur & Reproduzierbarkeit (Professioneller Standard) 🛡️

  * **Einen festen Random Seed verwenden**

      * **Problem**: Ohne festen Seed sind deine Simulationen nicht reproduzierbar – bei jedem Lauf kommen leicht andere Ergebnisse heraus.
      * **Fix**: Nutze `np.random.default_rng(seed)` und mache den `seed` zu einem Parameter, den du am Anfang des Skripts (oder via `argparse`) festlegst.

  * **Robuste Daten-Inputs**

      * **Tipp**: Anstatt eines fixen Sheet-Index (`sheet_name=5`) solltest du, wie beim Heatmap-Skript, automatisch nach dem richtigen Sheet suchen.
      * **Tipp**: Nutze `argparse`, um Input-/Output-Pfade und Simulationsparameter (wie `n_boot`, `seed`) über die Kommandozeile zu steuern.

-----

### Zusammenfassung & Definition of Done (DoD) 🏁

Dein Ansatz ist brillant, aber die methodische Umsetzung in der Statistik braucht diese Korrekturen, um wissenschaftlich unangreifbar zu sein.

Dein Skript ist "fertig", wenn:

  * ✅ Die Simulation der Konfidenzintervalle mit **Multinomial** (statt Binomial) erfolgt.
  * ✅ Die **F-Tests entfernt** und durch **Binomialtests** pro Gruppe ersetzt wurden.
  * ✅ Die **gesetzten Spieler (Seeds)** korrekt in den Ergebnissen erscheinen.
  * ✅ **`NaN`-Clubs** die Vereins-Sperre nicht mehr umgehen können.
  * ✅ Der Zufallsprozess durch einen **festen Seed** reproduzierbar ist.
  * ✅ Die **Anzahl der Simulationen (`n_sim`)** robust über den Median hergeleitet wird.