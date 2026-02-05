#!/usr/bin/env python3
"""
Script de test pour l'import MONACO_LOG (multi_sheet).
Teste le parsing des deux feuilles du fichier Excel.
"""

import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.import_logic.column_mapper import ColumnMapper
from app.services.parsers.excel_parser import ExcelParser

# Chemin du fichier Excel
FILE_PATH = "../file_import/PROTOCOLLO NT-MonacoLogistique Ott 2020 - agg.to 01.01.2023.xlsx"


def test_multi_sheet_config():
    """Test de la configuration multi_sheet."""
    print("=" * 60)
    print("TEST 1: Configuration multi_sheet")
    print("=" * 60)

    mapper = ColumnMapper()

    # Vérifier que MONACO_LOG est bien multi_sheet
    assert mapper.is_multi_sheet("MONACO_LOG"), "MONACO_LOG devrait être multi_sheet"
    print("✓ MONACO_LOG est bien reconnu comme multi_sheet")

    # Vérifier les configs des feuilles
    sheets = mapper.get_sheets_config("MONACO_LOG")
    assert len(sheets) == 2, f"Attendu 2 feuilles, trouvé {len(sheets)}"
    print(f"✓ 2 feuilles configurées")

    # Vérifier feuille France
    france = sheets[0]
    assert france["name"] == "france"
    assert france["layout"] == "dual_grid"
    assert france["sheet_name"] == "1-Tarifs MonacoLog"
    print(f"✓ Feuille France: {france['sheet_name']} (layout: {france['layout']})")

    # Vérifier feuille Italie
    italy = sheets[1]
    assert italy["name"] == "italy"
    assert italy["layout"] == "single_grid"
    assert italy["sheet_name"] == "2.TARIFS NT"
    print(f"✓ Feuille Italie: {italy['sheet_name']} (layout: {italy['layout']})")

    print()


def test_france_parsing():
    """Test du parsing de la feuille France."""
    print("=" * 60)
    print("TEST 2: Parsing feuille France")
    print("=" * 60)

    mapper = ColumnMapper()
    parser = ExcelParser()
    sheets = mapper.get_sheets_config("MONACO_LOG")
    france_conf = sheets[0]

    # Parser la feuille France
    parser_config = {
        "sheet_name": france_conf["sheet_name"],
        "header_row": france_conf["header_row"]
    }
    raw_data = parser.parse(FILE_PATH, **parser_config)

    print(f"Lignes parsées: {len(raw_data)}")
    assert len(raw_data) > 0, "Aucune donnée parsée pour la France"

    # Afficher un exemple
    print(f"Exemple première ligne (clés): {list(raw_data[0].keys())[:8]}...")

    # Mapper quelques lignes
    mapped_count = 0
    for row in raw_data[:3]:
        mapped_rows = mapper.map_row_with_sheet_config(row, france_conf)
        mapped_count += len(mapped_rows)
        if mapped_rows:
            first = mapped_rows[0]
            print(f"  → dest={first.get('dest_postal_code')}, weight={first.get('weight_min')}-{first.get('weight_max')}, cost={first.get('cost')}, origin={first.get('origin_city')}")

    print(f"✓ Mapping OK: {mapped_count} quotes générées pour 3 lignes sources")
    print()


def test_italy_parsing():
    """Test du parsing de la feuille Italie."""
    print("=" * 60)
    print("TEST 3: Parsing feuille Italie")
    print("=" * 60)

    mapper = ColumnMapper()
    parser = ExcelParser()
    sheets = mapper.get_sheets_config("MONACO_LOG")
    italy_conf = sheets[1]

    # Parser la feuille Italie
    parser_config = {
        "sheet_name": italy_conf["sheet_name"],
        "header_row": italy_conf["header_row"]
    }
    raw_data = parser.parse(FILE_PATH, **parser_config)

    print(f"Lignes parsées: {len(raw_data)}")
    assert len(raw_data) > 0, "Aucune donnée parsée pour l'Italie"

    # Afficher un exemple
    print(f"Exemple première ligne (clés): {list(raw_data[0].keys())}")

    # Mapper quelques lignes
    mapped_count = 0
    for row in raw_data[:3]:
        mapped_rows = mapper.map_row_with_sheet_config(row, italy_conf)
        mapped_count += len(mapped_rows)
        if mapped_rows:
            first = mapped_rows[0]
            print(f"  → dest={first.get('dest_postal_code')}, city={first.get('dest_city')}, weight={first.get('weight_min')}-{first.get('weight_max')}, cost={first.get('cost')}, origin={first.get('origin_city')}")

    print(f"✓ Mapping OK: {mapped_count} quotes générées pour 3 lignes sources")
    print()


def test_full_import_simulation():
    """Simulation d'un import complet (sans écriture en DB)."""
    print("=" * 60)
    print("TEST 4: Simulation import complet")
    print("=" * 60)

    mapper = ColumnMapper()
    parser = ExcelParser()
    sheets = mapper.get_sheets_config("MONACO_LOG")

    total_quotes = 0
    stats = {}

    for sheet_conf in sheets:
        sheet_name = sheet_conf["sheet_name"]
        conf_name = sheet_conf["name"]

        parser_config = {
            "sheet_name": sheet_name,
            "header_row": sheet_conf["header_row"]
        }
        raw_data = parser.parse(FILE_PATH, **parser_config)

        quotes_count = 0
        for row in raw_data:
            mapped_rows = mapper.map_row_with_sheet_config(row, sheet_conf)
            quotes_count += len(mapped_rows)

        stats[conf_name] = {
            "raw_rows": len(raw_data),
            "quotes": quotes_count
        }
        total_quotes += quotes_count
        print(f"Feuille '{conf_name}': {len(raw_data)} lignes → {quotes_count} quotes")

    print()
    print(f"TOTAL: {total_quotes} quotes générées")
    print()

    # Vérifications
    assert stats["france"]["quotes"] >= 60, f"France devrait avoir au moins 60 quotes (trouvé: {stats['france']['quotes']})"
    assert stats["italy"]["quotes"] >= 500, f"Italie devrait avoir au moins 500 quotes (trouvé: {stats['italy']['quotes']})"

    print("✓ Tous les tests passés!")


if __name__ == "__main__":
    test_multi_sheet_config()
    test_france_parsing()
    test_italy_parsing()
    test_full_import_simulation()
