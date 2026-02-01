import pandas as pd
import sys

FILE_PATH = "file_import/ML BIANCHI GROUP PROTOCOLE 01.02.2023  OK FOR 2024 update fuel 1.11.24.xlsx"
SHEET_NAME = "PROTOCOLE DISTRIBUTION FRANCE"
HEADER_ROW = 6

def check_size():
    print(f"Reading {FILE_PATH}...")
    try:
        # Read without limit to see full size
        df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=HEADER_ROW)
        print(f"Shape: {df.shape}")
        print(f"Last index: {df.index[-1]}")
        
        # Check if tail is empty
        print("Tail:")
        print(df.tail())
        
        # Count non-null rows
        print(f"Non-null rows (any column): {df.dropna(how='all').shape[0]}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_size()
