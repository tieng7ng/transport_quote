import pandas as pd
import sys

file_path = "file_import/grille tarifaire2024 BESSON.xlsx"
if len(sys.argv) > 1:
    file_path = sys.argv[1]

try:
    xls = pd.ExcelFile(file_path)
    print(f"Sheets in {file_path}: {xls.sheet_names}")
    
    # Inspect first few rows of each sheet
    for sheet in xls.sheet_names:
        print(f"\n--- Sheet: {sheet} ---")
        df = pd.read_excel(file_path, sheet_name=sheet, header=None, nrows=10)
        print(df.to_string())
except Exception as e:
    print(f"Error reading {file_path}: {e}")
