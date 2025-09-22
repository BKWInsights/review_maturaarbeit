# Parser - Extract Tournament Draw Data

This Python script parses exported tournament draw files from the **Badminton Tournament Planner (BTP)**.
It collects all relevant player and draw information from multiple `xlsx` files and merges them into a single summary file.

---

## Features

- Processes mulitple Excel draw files from a given folder
- Only uses the sheet with the name *HE U13-Hauptfeld*
- Extracts player detail:
    - **Name**
    - **Club**
    - **Group**
    - **Seed** (if available)
- Ignores irrelevant entries (e.g., `WC`, `Standings`, `Pl`)
- Creates one combined Excel file (`all_MS_U13.xlsx`) with all results

---

## Dependencies

- Python 3.x
- `pandas` - data handling
- `openpyxl` - required Excel backend
- Standard libraries: `os`, `glob`, `re`

Install the required packages with:

```bash
pip install pandas openpyxl
```

---

## Usage

1. Prepare the input files
    - Export your tournament draws from BTP as `xlsx` files.
    - Place them in a single folder (e.g., `D:\Maturaarbeit\Draws\docs`)
    - The script expects file names like `Ausl_1.xlsx`, `Ausl_2.xlsx`, ... for correct sorting.

2. Customize the script
    - Check the following points in the script:
        - `folder_path` -> path to your folder with the Excel files
        - `sheet_name` -> must match the sheet name inside your Excel files (default: `HE U13-Hauptfeld`)
        - `output_path` -> where the merged file should be saved

3. Run the script
```bash
python draw_parser.py
```

4. Output file
    - By default the script saves to `d:/Maturaarbeit/all_MS_U13.xlsx`.
    - To change this, edit the `output_path` variable in `draw_parser`

---

## Example output (Excel)

| Name      | Club   | Group | Seed |
|-----------|--------|-------|------|
| Player 1  | Club 1 | A     | 1    |
| Player 2  | Club 2 | A     |      |
| ...       | ...    | ...   | ...  |
