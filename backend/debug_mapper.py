from app.services.import_logic.column_mapper import ColumnMapper
import json

# Mock config loading by subclassing or patching?
# Actually ColumnMapper loads from file. I updated the file. So it should load BIANCHI.

def debug_bianchi_mapping():
    mapper = ColumnMapper()
    
    # Check config loaded
    conf = mapper.get_parser_config("BIANCHI")
    print(f"Config loaded: {conf}")
    
    # Simulate a row (keys are normalized by ExcelParser)
    # Based on inspect_excel output:
    # 06 | 8.79... | 5.23...
    
    # Construct a sample row dict
    sample_row = {
        "nan": None,
        "zip_code": "06",
        "minimum": 9.23,
        "100/300_kg": 5.5,
        "301/500kg": 5.47, # key might be slightly different depending on normalization?
                         # inspect output: '100/300 kg'. ExcelParser normalize: '100/300_kg'
                         # Yaml config: "100/300 kg". Mapper normalize: "100/300_kg"
                         # So they should match.
        "501/1000_kg": 5.13,
        "pricing": "PRICE PER 100KGS",
        "t/t_from_nice_**": "24h",
        
        "nan.1": None,
        "zip_code.1": "06",
        "1001/1500_kg": 4.92,
        "1501/2000_kg": 4.61,
        "2001/3000_kg": 4.1,
        "3001/4000_kg": 98,
        "4001/5000_kg": 115,
        "pricing.1": "LUMPSUM FROM NICE",
        "t/t_from_nice_**.1": "24h"
    }

    print("Mapping row...")
    try:
        results = mapper.map_row(sample_row, "BIANCHI")
        print(f"Mapped {len(results)} rows.")
        for r in results:
            print(r)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_bianchi_mapping()
