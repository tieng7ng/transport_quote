try:
    from app.services.import_logic.column_mapper import ColumnMapper
    print("Syntax OK")
except Exception as e:
    print(f"Import Error: {e}")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
