Super Script!

### Kritische Bugs & Robustheit 🐞 (Unbedingt beheben)

Diese Punkte sind entscheidend, da sie zu Abstürzen, Endlosschleifen oder falschen Ergebnissen führen können.

**1. Endlos-Loop-Risiko bei der Start-Zuweisung**

  * **Problem**: Wenn die Spieler-Konstellation sehr einschränkend ist (z.B. viele Spieler aus einem Club), findet `random_assignment()` möglicherweise **nie** eine gültige Zuweisung und läuft in einer Endlosschleife.
  * **Robuster Fix**: Baue einen Zähler mit einer maximalen Anzahl an Versuchen ein.
    ```python
    def random_assignment(max_tries=5000):
        for _ in range(max_tries):
            # ... deine bisherige Logik ...
            if valid_assignment(assignment):
                return assignment
        # Wenn nach max_tries keine Lösung gefunden wurde:
        raise RuntimeError("Kein gültiges Start-Assignment gefunden. Constraints (z.B. Club-Verteilung) könnten zu streng sein.")
    ```

**2. `NaN`-Clubs heben die Vereins-Sperre aus**

  * **Problem**: Ein Spieler mit `Club=NaN` kann die Sperre in `valid_assignment` umgehen, da `NaN == NaN` immer `False` ist. So können fälschlicherweise mehrere Spieler ohne Club in einer Gruppe landen.
  * **Fix**: Normalisiere fehlende Club-Namen vorab.
    ```python
    # Am Anfang, nach dem Einlesen der Spielerdaten:
    df["Club"] = df["Club"].fillna("UNKNOWN").astype(str).str.strip()
    clubs = dict(zip(df["Name"], df["Club"]))
    # Entscheide dann, ob "UNKNOWN" als ein einziger Club zählt oder ignoriert wird.
    ```

**3. Fehlende Daten-Validierung**

  * **Problem**: Das Skript geht davon aus, dass die `players.xlsx` perfekt ist. Falsche Setzlisten-Anzahlen oder eine abweichende Spielerzahl führen zu unbemerkten Fehlern oder Abstürzen (`IndexError` bei `.pop()`).
  * **Fix**: Füge am Anfang "Assertions" (Prüfungen) hinzu, die sofort abbrechen, wenn die Daten nicht stimmen.
    ```python
    # Beispiel-Prüfungen nach dem Laden von df:
    assert sum(group_sizes) == len(df), "Die Summe der Gruppengrößen passt nicht zur Spieleranzahl!"
    seed_counts = df['Seed'].astype(str).value_counts()
    assert seed_counts.get('1', 0) == 1, "Es muss genau ein Seed 1 geben!"
    # ... weitere Prüfungen für Seed 2, 3/4, 5/8 ...
    ```

**4. Doppelter CSV-Export**

  * **Problem**: Der Code-Block zum Schreiben der CSV-Datei ist doppelt vorhanden, was zu duplizierten Einträgen führt.
  * **Fix**: Entferne den zweiten, identischen Block (Zeilen \~451-461).

-----

### Reproduzierbarkeit für die Wissenschaftlichkeit 🔬

  * **Zufall deterministisch machen (extrem wichtig\!)**
      * **Problem**: Ohne festen "Seed" liefert dein Skript bei jedem Durchlauf andere Ergebnisse. Für eine wissenschaftliche Arbeit ist Reproduzierbarkeit aber unerlässlich.
      * **Fix**: Setze den Seed für alle Zufallsgeneratoren am Anfang deines Skripts.
        ```python
        SEED = 42 # Eine beliebige, aber feste Zahl
        random.seed(SEED)
        np.random.seed(SEED)
        ```

-----

### Architektur & Performance 🚀

  * **Struktur mit einer Klasse (OOP)**: Wie besprochen, ist das Auslagern der Logik und der Zustände (wie `history`) in eine `DrawOptimizer`-Klasse der beste Weg, um die globalen Variablen zu eliminieren und den Code professionell zu strukturieren.
  * **Delta-Scoring statt Full Rescore**: Ebenfalls wie besprochen, ist die Implementierung einer `score_delta()`-Funktion, die nur die Veränderung der Penalty berechnet, der größte Hebel zur Steigerung der Performance.
  * **Konfiguration zentralisieren**: Fasse alle Parameter (`T_START`, `MAX_ITER`, `W_HALF` etc.) in einem zentralen `CONFIG`-Dictionary am Anfang des Skripts zusammen. Mache das Skript über `argparse` steuerbar.

-----

### Methodik & Algorithmus-Design 💡 (Für die Diskussion in deiner Arbeit)

  * **Das "Bewegliche Ziel" der Penalty-Funktion**

      * **Beobachtung**: Da du die `history`-Tabellen nach jeder Simulation aktualisierst, ändert sich die Zielfunktion (`score`) im Laufe der Zeit. Spätere Simulationen optimieren also gegen ein anderes Ziel als frühere.
      * **Gedanke**: Das ist eine wichtige methodische Entscheidung\! Ist das gewollt, um die Diversität der Ergebnisse zu erhöhen? Oder wäre es besser, die Historie vor den Haupt-Simulationen "einzufrieren"? Dies ist ein exzellenter Punkt für die Diskussion oder den Methodik-Teil deiner Arbeit.

  * **Nachbarschafts-Strategie erweitern**

      * **Idee**: Wenn einfache Swaps oft zu ungültigen Zuweisungen führen, könntest du deinem Algorithmus weitere "Züge" beibringen, z.B. einen 3er-Ringtausch zwischen drei Gruppen. Das kann helfen, in schwierigen Konstellationen bessere Lösungen zu finden.

-----

### Zusammenfassung & Definition of Done (DoD) 🏁

Dein Algorithmus ist konzeptionell brillant. Diese Fixes stellen sicher, dass er auch in der Praxis robust, korrekt und wissenschaftlich fundiert ist.

Dein Skript ist "fertig", wenn:

  * ✅ `random_assignment` bei unmöglichen Konstellationen sauber abbricht statt in einer Endlosschleife zu hängen.
  * ✅ Spieler mit `Club=NaN` korrekt behandelt werden.
  * ✅ Das Skript mit einer Prüfung der Input-Daten (Spielerzahl, Seeds) startet.
  * ✅ Die Ergebnisse durch einen festen `SEED` zu 100% reproduzierbar sind.
  * ✅ Der doppelte CSV-Schreibvorgang entfernt wurde.