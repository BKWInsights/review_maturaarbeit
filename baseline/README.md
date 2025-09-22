# Baseline Random Sampling

This script implements a **baseline method** for generating tournament draws using **rejection sampling**.  
It tries random assignments of players to groups and only accepts those that satisfy all constraints (seeds, group sizes, and club separation).  

**Note**: This approach is extremely slow for large simulations.  
It is included only as a **reference baseline**. The main analysis uses the MRV heuristic instead (see `statistical_analysis/`).


---


## Functionality

- Loads player list from Excel (`Spielerliste.xlsx`)
- Defines **constraints**:
  - Seed placement rules (e.g., Seed 1 must go to Group A, Seed 2 to Group B, etc.)
  - Group size limits: 3 players per group (4 players for Group G). Seeded players are placed so that each group A–H has exactly one seed.
  - No two players from the same club in the same group
- Generates random group assignments and checks validity
- Uses **rejection sampling**:
  - Invalid draws are discarded
  - Only valid draws are kept
- Saves results incrementally to `progress.csv` (resumes if file exists)


---


## Dependencies
- Input: `players.xlsx` (must contiain the columns `Name`, `Seed`, `Club`)
- Output: `progress.csv` (stores generated valid draws, auto-saves every 100 draws)

- Python 3.x
- `pandas` - data handling
- `openpyxl` - Excel bachend
- Standard library modules: `os`, `random`

Install the required packages with:
```bash
pip install pandas openpyxl
```


---


## Usage

1. Prepare the input file
    - Create an Excel file named `players.xlsx` (for testing rename file `players_example`).
    - The file **must** contain the columns: `Name`, `Seed`, `Club`.
    - Recommended setup: **34 players** (8 seeded + 26 unseeded). Other player counts may produce unexpected results.
2. Customize the script (important - change all file paths to your system)
    - Open `baseline_random_sampling.py` in an editor and change the input path:
```python
# Inside baseline_random_samping.py
df = pd.read_excel(r"D:\Maturaarbeit\players.xlsx")

```
  - Adjust `n_sim` - the number of *valid* draws you want to generate (large values greatly increase runtime).
```python
# Inside baseline_random_samping.py
monte_carlo_random(seed_map, free_slots, clubs, n_sim=1000)
```
3. Run the script:
```bash
python baseline_random_sampling.py
```
4. Stopping and resuming
    - To stop early: press *Ctrl + C* in the terminal. The script catches the interruption and saves the last state.
    - The script writes progess to `progress.csv`. If `progress.csv` exists on next run, the script will *resume* from the last saved vaild draw.
5. Output
     - `progress.csv` contains the saved valid draws with columns: `Player`, `Group`, `Simulation`
     - The script prints progress messages (e.g., every 10 valid draws (change 10 `if valid_draws % 10 == 0:` if you want more or less updates), and a summary when finished).


---


## Example Input

The scripts expects an Excel file named **`players.xlsx`** with the columns:
  - `Name` (player name)
  - `Seed` (player seed, e.g. 1, 2, "3/4", "5/8", or empty for unseeded)
  - `Club` (player's club affiliation)

For convenience, an example file **`players_example.xlsx`** is included.
  - It contains **34 example players** (8 seeded + 26 unseeded).  
  - Player names are generic placeholders (e.g., *"Example Player 1"*, *"Example Player 2"*, …).  
  - Clubs amount mirrors the structure of the real dataset. 
To test the script directly, you can rename it to `players.xlsx`.


---


## Limitations
  - Designed for **34 players** (8 seeded + 26 unseeded).
  - Other player counts may not work correctly or may produce invalid results.
  - Runtime increases rapidly with the number of simulations (`n_sim`).
  - Not suitable for large-scale evaluations.
  - Used only as a *baseline*; the main results are based on the more efficient *MRV heuristic* (see `statistical_analysis`).


