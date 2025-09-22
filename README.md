# Matura Thesis – Badminton Tournament Group Draws

This repository contains the code for my **Matura thesis**. The goal is to investigate the **randomness and fairness of badminton tournament group draws** and to develop a custom method to improve these draws.

The scripts serve different purposes: generating and extracting draws, performing statistical analyses, and implementing a custom algorithm using *Simulated Annealing* and *Boltzmann rules*.

> Note: These scripts are not intended as standalone software. Many parts rely on the program Badminton Tournament Planner (BTP) and are specifically tailored to my working environment (e.g., screen resolution for macros).

---

## Project Structure and Code Modules

### 1. draw_macro
- Automatically generates a specified number of tournament draws in Badminton Tournament Planner.
- Uses mouse clicks calibrated to my screen resolution.
- Serves to create a large dataset of tournament draws.

---

### 2. draw_parser
- Reads the exported draw files from the macro.
- Extracts relevant information into an Excel table:
    - File, Group, Club, Name, Seed
- Output: a structured table containing all player data and group assignments.

---

### 3. draw_statistics
- Performs initial evaluations of the draws.
    - Examples:  
        - How often a player landed in a specific group.  
        - How often a player was paired with a specific other player.
---

### 4. statistical_analysis
- Mathematical analysis of the draws.
    - Includes, among others: 
        - **Chi² distribution**  
        - **Monte Carlo simulations**  
        - **Cramer’s V**  
        - **F-Test, t-Test**  
- Goal: Check whether group assignments appear statistically random or if systematic patterns exist.

---

### 5. heatmap
- Visualizes the results of the draws.
- Two heatmaps:
1. Player–Group observations  
2. Deviations between observed and expected values
- Helps to quickly identify/visualize irregularities in the distribution.
    
---

### 6. own_algorithm
- Custom algorithm for “fairer” draws.
- Uses **Simulated Annealing** and **Boltzmann rules**:
  - Starts with a random draw.
  - Iteratively refines it to avoid unfavorable situations (e.g., same-club players, repeated pairings).
- Goal: Better balance between fairness and randomness compared to BTP.
---

### 7. penalty_learning_curve
- Visualizes the learning curve of the custom algorithm.
- Shows how the **penalty function** (penalty points for unfair situations) decreases over the course of Simulated Annealing. 
- Illustrates the optimization process.

---


### 8. baseline_random_sampling
- Originally intended for **Rejection Sampling**.
- Problem: highly inefficient → with 1'000'000 simulations, often only 2–6 valid draws were produced.  
- Later replaced by Monte Carlo with MRV heuristic in `statistical_analysis`


---


## Requirements

- **Badminton Tournament Planner (BTP)** (for macro and draw generation)  
- **Python 3.x**  
- Typical Python Libraries:  
   - `pandas`, `numpy`, `scipy`, `matplotlib`, `openpyxl`, `tqdm`, `plotly`

---

## Usage
This project is not designed for general use. For personal testing: `players_example` as an example Excel file.  
- Works most reliably with **34 players including 8 seeded**.
- Focus is on analysis and visualization, not on a production-ready tool.
---

## License
This project was created as part of a **Matura thesis**.
The code is provided for **demonstration and research purposes only**.
