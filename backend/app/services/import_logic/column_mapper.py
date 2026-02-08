import yaml
import os
import re
import unicodedata
from typing import Dict, List, Optional, Any
import pandas as pd
import math

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "configs", "partner_mapping.yaml")

class ColumnMapper:
    def __init__(self):
        self.config = self._load_config()
        self.default_mapping = self.config.get("default", {}).get("columns", {})

    def _load_config(self) -> Dict:
        if not os.path.exists(CONFIG_PATH):
            return {}
        try:
            with open(CONFIG_PATH, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading mapping config: {e}")
            return {}

    def get_mapping_for_partner(self, partner_code: Optional[str] = None) -> Dict[str, str]:
        """
        Retourne un dictionnaire {colonne_fichier: champ_schema}
        pour un partenaire donné.
        """
        # TODO: Implémenter surcharge par partenaire si nécessaire
        # Pour l'instant on se base sur le mapping par défaut inversé pour la recherche
        return {} 

    def get_parser_config(self, partner_code: Optional[str] = None) -> Dict[str, Any]:
        """Retourne la configuration spécifique pour le parser (sheet, header...)."""
        if not partner_code:
            return {}
        p_conf = self.config.get("partners", {}).get(partner_code, {})
        return {
            "sheet_name": p_conf.get("sheet_name"),
            "header_row": p_conf.get("header_row")
        }

    def is_multi_sheet(self, partner_code: Optional[str] = None) -> bool:
        """Vérifie si le partenaire utilise le layout multi_sheet."""
        if not partner_code:
            return False
        p_conf = self.config.get("partners", {}).get(partner_code, {})
        return p_conf.get("layout") == "multi_sheet"

    def get_sheets_config(self, partner_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retourne la liste des configurations de feuilles pour un partenaire multi_sheet.
        Chaque élément contient: name, sheet_name, header_row, layout, columns, defaults, transforms, etc.
        """
        if not partner_code:
            return []
        p_conf = self.config.get("partners", {}).get(partner_code, {})
        if p_conf.get("layout") != "multi_sheet":
            return []
        return p_conf.get("sheets", [])

    def map_row_with_sheet_config(self, row: Dict[str, Any], sheet_config: Dict[str, Any], prev_weight_max: float = 0.0) -> List[Dict[str, Any]]:
        """
        Transforme une ligne brute en utilisant une configuration de feuille spécifique.
        Utilisé pour le layout multi_sheet où chaque feuille a sa propre config.
        """
        mapped_rows = []
        sheet_layout = sheet_config.get("layout", "flat")

        # Mapping inversé : {alias: [champ_schema_1, champ_schema_2]}
        alias_map = {}

        def add_mapping(alias, field):
            norm_alias = self._normalize(alias)
            if norm_alias not in alias_map:
                alias_map[norm_alias] = []
            if field not in alias_map[norm_alias]:
                alias_map[norm_alias].append(field)

        # 1. Charger aliases défaut
        for field, aliases in self.default_mapping.items():
            if isinstance(aliases, list):
                for alias in aliases:
                    add_mapping(alias, field)
            else:
                add_mapping(aliases, field)

        # 2. Surcharge depuis la config de la feuille
        sheet_cols = sheet_config.get("columns", {})
        for field, alias in sheet_cols.items():
            add_mapping(alias, field)

        # --- LOGIQUE DUAL GRID ---
        if sheet_layout == "dual_grid":
            dual_conf = sheet_config.get("dual_grid", {})

            base_row = {}
            for col_name, value in row.items():
                normalized_col = self._normalize(col_name)
                if normalized_col in alias_map:
                    for target_field in alias_map[normalized_col]:
                        base_row[target_field] = value
                elif self._normalize(col_name) in self.default_mapping:
                    if self.default_mapping[self._normalize(col_name)] not in base_row:
                        base_row[self._normalize(col_name)] = value

            defaults = sheet_config.get("defaults", {})
            for field, value in defaults.items():
                if field not in base_row or base_row[field] is None:
                    base_row[field] = value

            sections = ["small_weights", "large_weights"]
            for section_name in sections:
                section_conf = dual_conf.get(section_name)
                if not section_conf:
                    continue

                columns_map = section_conf.get("columns", {})
                pricing_col_alias = section_conf.get("pricing_col")
                delivery_col_alias = section_conf.get("delivery_time_col")

                section_pricing_type = base_row.get(pricing_col_alias)
                section_delivery_time = base_row.get(delivery_col_alias)

                for col_header, weight_range in columns_map.items():
                    found_val = None
                    norm_header = self._normalize(col_header)

                    if norm_header in row:
                        found_val = row[norm_header]
                    else:
                        for rk, rv in row.items():
                            if self._normalize(rk) == norm_header:
                                found_val = rv
                                break

                    cleaned_cost = self._clean_decimal(found_val)

                    if cleaned_cost is not None and cleaned_cost > 0:
                        new_row = base_row.copy()
                        new_row["weight_min"] = weight_range["weight_min"]
                        new_row["weight_max"] = weight_range["weight_max"]
                        new_row["cost"] = cleaned_cost

                        if section_pricing_type:
                            new_row["pricing_type"] = section_pricing_type
                        if section_delivery_time:
                            new_row["delivery_time"] = section_delivery_time

                        mapped_rows.append(new_row)

        # --- LOGIQUE SINGLE GRID ---
        elif sheet_layout == "single_grid":
            single_conf = sheet_config.get("single_grid", {})
            province_col = single_conf.get("province_column")
            brackets = single_conf.get("brackets", [])

            transforms_conf = sheet_config.get("transforms", {})
            dest_pc_extract = transforms_conf.get("dest_postal_code", {}).get("regex_extract")

            base_row = {}
            for col_name, value in row.items():
                normalized_col = self._normalize(col_name)

                if province_col and (col_name == province_col or normalized_col == self._normalize(province_col)):
                    if dest_pc_extract and isinstance(value, str):
                        match = re.search(dest_pc_extract, value)
                        if match:
                            base_row["dest_postal_code"] = match.group(1)
                            if len(match.groups()) > 1:
                                base_row["dest_city"] = match.group(2).strip()
                        else:
                            base_row["dest_postal_code"] = value
                    else:
                        base_row["dest_postal_code"] = value

                    if "dest_city" not in base_row:
                        base_row["dest_city"] = value

                elif normalized_col in alias_map:
                    for target_field in alias_map[normalized_col]:
                        base_row[target_field] = value
                elif self._normalize(col_name) in self.default_mapping:
                    base_row[self._normalize(col_name)] = value

            defaults = sheet_config.get("defaults", {})
            for field, value in defaults.items():
                if field not in base_row or base_row[field] is None:
                    base_row[field] = value

            for bracket in brackets:
                header = bracket.get("header")
                found_val = None
                norm_header = self._normalize(header)

                if header in row:
                    found_val = row[header]
                else:
                    for rk, rv in row.items():
                        if self._normalize(rk) == norm_header:
                            found_val = rv
                            break

                cleaned_cost = self._clean_decimal(found_val)

                if cleaned_cost is not None:
                    new_row = base_row.copy()
                    new_row["weight_min"] = bracket["weight_min"]
                    new_row["weight_max"] = bracket["weight_max"]
                    new_row["pricing_type"] = bracket.get("pricing_type", "PER_100KG")
                    new_row["cost"] = cleaned_cost
                    mapped_rows.append(new_row)

        # --- LOGIQUE ZONE MATRIX (Internationale Phase 2) ---
        elif sheet_layout == "zone_matrix":
            zone_conf = sheet_config.get("zone_matrix", {})
            weight_col_name = zone_conf.get("weight_column", "kg")
            # Construire un mapping insensible à la casse (les headers pandas peuvent être en minuscules)
            raw_zone_mappings = zone_conf.get("zone_to_postcodes", {})
            zone_mappings = {k.upper(): v for k, v in raw_zone_mappings.items()}

            base_row = {}
            for col_name, value in row.items():
                normalized_col = self._normalize(col_name)
                if normalized_col in alias_map:
                    for target_field in alias_map[normalized_col]:
                        base_row[target_field] = value
                elif self._normalize(col_name) in self.default_mapping:
                    base_row[self._normalize(col_name)] = value

            defaults = sheet_config.get("defaults", {})
            for field, value in defaults.items():
                if field not in base_row or base_row[field] is None:
                    base_row[field] = value

            weight_val = None
            weight_norm = self._normalize(weight_col_name)

            for col_name, value in row.items():
                if self._normalize(col_name) == weight_norm:
                    weight_val = value
                    break

            if weight_val is not None:
                w_min, w_max = self._parse_weight_key(weight_val, prev_weight_max)

                for col_name, value in row.items():
                    norm_col = self._normalize(col_name)
                    if norm_col == weight_norm:
                        continue
                    if "unnamed" in norm_col or value is None:
                        continue

                    cost = self._clean_decimal(value)
                    if cost is not None:
                        dest_key = str(col_name).strip().upper()

                        if dest_key in zone_mappings:
                            postcodes = zone_mappings[dest_key]
                            if isinstance(postcodes, list):
                                for pc in postcodes:
                                    new_row = base_row.copy()
                                    new_row["weight_min"] = w_min
                                    new_row["weight_max"] = w_max
                                    new_row["cost"] = cost
                                    new_row["dest_postal_code"] = str(pc).strip()
                                    if "pricing_type" not in new_row:
                                        new_row["pricing_type"] = "LUMPSUM"
                                    mapped_rows.append(new_row)
                            else:
                                new_row = base_row.copy()
                                new_row["weight_min"] = w_min
                                new_row["weight_max"] = w_max
                                new_row["cost"] = cost
                                new_row["dest_postal_code"] = str(postcodes).strip()
                                if "pricing_type" not in new_row:
                                    new_row["pricing_type"] = "LUMPSUM"
                                mapped_rows.append(new_row)
                        else:
                            new_row = base_row.copy()
                            new_row["weight_min"] = w_min
                            new_row["weight_max"] = w_max
                            new_row["cost"] = cost
                            new_row["dest_postal_code"] = dest_key
                            if "pricing_type" not in new_row:
                                new_row["pricing_type"] = "LUMPSUM"
                            mapped_rows.append(new_row)

        # --- LOGIQUE FLAT ---
        else:
            mapped_row = {}
            for col_name, value in row.items():
                normalized_col = self._normalize(col_name)
                if normalized_col in alias_map:
                    for target_field in alias_map[normalized_col]:
                        mapped_row[target_field] = value
                elif col_name in self.default_mapping:
                    mapped_row[col_name] = value

            defaults = sheet_config.get("defaults", {})
            for field, value in defaults.items():
                if field not in mapped_row or mapped_row[field] is None:
                    mapped_row[field] = value

            if "cost" in mapped_row:
                mapped_row["cost"] = self._clean_decimal(mapped_row.get("cost"))

            if mapped_row.get("cost") is not None:
                mapped_rows = [mapped_row]

        # --- PHASE FINALE : TRANSFORMS & CLEANUP ---
        final_rows = []
        transforms = sheet_config.get("transforms", {})

        for r in mapped_rows:
            for key in ["origin_postal_code", "dest_postal_code", "origin_city", "dest_city", "origin_country", "dest_country", "pricing_type"]:
                if key in r and r[key] is not None:
                    val_str = str(r[key]).strip()

                    if key in transforms and isinstance(transforms[key], dict) and val_str in transforms[key]:
                        val_str = transforms[key][val_str]

                    if key in ["origin_postal_code", "dest_postal_code"] and val_str.isdigit() and len(val_str) < 2:
                        val_str = val_str.zfill(2)
                    r[key] = val_str

            final_rows.append(r)

        return final_rows

    def map_row(self, row: Dict[str, Any], partner_code: Optional[str] = None, prev_weight_max: float = 0.0) -> List[Dict[str, Any]]:
        """
        Transforme une ligne brute en une ou plusieurs lignes mappées.
        Retourne toujours une LISTE de dictionnaires.
        """
        mapped_rows = []
        
        # 0. Récupérer config partenaire
        partner_config = self.config.get("partners", {}).get(partner_code, {}) if partner_code else {}
        is_grid = partner_config.get("layout") == "grid"
        is_dual_grid = partner_config.get("layout") == "dual_grid"
        is_single = partner_config.get("layout") == "single_grid"

        if not mapped_rows:
             # Debug only first row
             # print(f"DEBUG map_row code={partner_code} layout={partner_config.get('layout')} row_keys={list(row.keys())}")
             pass
        
        # Mapping inversé : {alias: [champ_schema_1, champ_schema_2]}
        alias_map = {}
        
        # Helper pour ajouter au mapping
        def add_mapping(alias, field):
            norm_alias = self._normalize(alias)
            if norm_alias not in alias_map:
                alias_map[norm_alias] = []
            if field not in alias_map[norm_alias]:
                alias_map[norm_alias].append(field)

        # 1. Charger aliases défaut
        for field, aliases in self.default_mapping.items():
            if isinstance(aliases, list):
                for alias in aliases:
                    add_mapping(alias, field)
            else:
                add_mapping(aliases, field)
                
        # 2. Surcharge Partenaire (spécifique)
        partner_cols = partner_config.get("columns", {})
        for field, alias in partner_cols.items():
             # Ici on peut avoir plusieurs fields qui pointent sur le meme alias
             add_mapping(alias, field)

        # --- LOGIQUE DUAL GRID (BIANCHI) ---
        if is_dual_grid:
            dual_conf = partner_config.get("dual_grid", {})
            mapped_rows = []
            
            # Common fields map
            base_row = {}
            for col_name, value in row.items():
                normalized_col = self._normalize(col_name)
                # Map specific fields defined in 'columns'
                if normalized_col in alias_map:
                    for target_field in alias_map[normalized_col]:
                        base_row[target_field] = value
                # Map defaults that are not mapped
                elif self._normalize(col_name) in self.default_mapping:
                     # Avoid overwriting if explicit alias exists? 
                     if self.default_mapping[self._normalize(col_name)] not in base_row:
                        base_row[self._normalize(col_name)] = value
            
            # Apply defaults
            defaults = partner_config.get("defaults", {})
            for field, value in defaults.items():
                if field not in base_row or base_row[field] is None:
                    base_row[field] = value

            # Process Sections
            sections = ["small_weights", "large_weights"]
            
            for section_name in sections:
                section_conf = dual_conf.get(section_name)
                if not section_conf:
                    continue
                
                columns_map = section_conf.get("columns", {})
                pricing_col_alias = section_conf.get("pricing_col") # e.g. "pricing_type_small"
                delivery_col_alias = section_conf.get("delivery_time_col")
                
                # Get pricing/delivery specific to this section
                # These are ALREADY in base_row because we mapped them via alias_map initially
                # But we need to assign them to the canonical 'pricing_type' and 'delivery_time' fields
                
                section_pricing_type = base_row.get(pricing_col_alias)
                section_delivery_time = base_row.get(delivery_col_alias)
                
                for col_header, weight_range in columns_map.items():
                    # Find value for this column
                    found_val = None
                    norm_header = self._normalize(col_header)
                    
                    # Try exact match first
                    if norm_header in row:
                         found_val = row[norm_header]
                    else:
                        for rk, rv in row.items():
                            if self._normalize(rk) == norm_header:
                                found_val = rv
                                break
                    
                    # Clean/Validate Cost
                    cleaned_cost = self._clean_decimal(found_val)
                    
                    if cleaned_cost is not None and cleaned_cost > 0:
                        # Create a row for this weight range
                        new_row = base_row.copy()
                        new_row["weight_min"] = weight_range["weight_min"]
                        new_row["weight_max"] = weight_range["weight_max"]
                        new_row["cost"] = cleaned_cost
                        
                        # Assign section-specific attributes
                        if section_pricing_type:
                            new_row["pricing_type"] = section_pricing_type
                        if section_delivery_time:
                            new_row["delivery_time"] = section_delivery_time
                            
                        mapped_rows.append(new_row)

        # --- LOGIQUE GRID / MATRICE ---
        elif is_grid:
            grid_conf = partner_config.get("grid", {})
            header_regex = grid_conf.get("header_regex")
            value_col_name = grid_conf.get("value_column", "cost")
            
            # Identifier les colonnes fixes (non pivot)
            base_row = {}
            pivot_data = [] # [(weight_max, cost), ...]

            for col_name, value in row.items():
                normalized_col = self._normalize(col_name)
                
                # Est-ce une colonne pivot (ex: "5 KG") ?
                match = re.search(header_regex, str(col_name), re.IGNORECASE) if header_regex else None
                
                if match:
                    # C'est une colonne de poids !
                    weight_val = float(match.group(1))
                    cleaned_val = self._clean_decimal(value)
                    if cleaned_val is not None: # Si y'a un prix
                        pivot_data.append((weight_val, cleaned_val))
                elif normalized_col in alias_map:
                    # Colonne standard mappée (peut mapper vers plusieurs champs)
                    for target_field in alias_map[normalized_col]:
                        base_row[target_field] = value
                else:
                    if self._normalize(col_name) in self.default_mapping:
                         base_row[self._normalize(col_name)] = value

            # Appliquer les valeurs par défaut
            defaults = partner_config.get("defaults", {})
            for field, value in defaults.items():
                if field not in base_row or base_row[field] is None:
                    base_row[field] = value

            # Générer les lignes pivotées
            pivot_data.sort(key=lambda x: x[0])
            weight_min_gap = grid_conf.get("weight_min_gap", 0)
            prev_weight = 0.0
            
            for weight_max, cost in pivot_data:
                new_row = base_row.copy()
                new_row["weight_min"] = prev_weight
                new_row["weight_max"] = weight_max
                new_row[value_col_name] = cost
                mapped_rows.append(new_row)
                prev_weight = weight_max + weight_min_gap


        # --- LOGIQUE SINGLE GRID (MONACO ITALIE) ---
        elif partner_config.get("layout") == "single_grid":
            single_conf = partner_config.get("single_grid", {})
            province_col = single_conf.get("province_column")
            brackets = single_conf.get("brackets", [])
            
            # Regex extraction config
            transforms_conf = partner_config.get("transforms", {})
            dest_pc_extract = transforms_conf.get("dest_postal_code", {}).get("regex_extract")

            base_row = {}
            # Copie des champs par défaut et mappings simples
            for col_name, value in row.items():
                normalized_col = self._normalize(col_name)
                
                # Si c'est la colonne province, on la traite
                if province_col and (col_name == province_col or normalized_col == self._normalize(province_col)):
                    # Extraction Regex (ex: "20 Milano" -> "20")
                    if dest_pc_extract and isinstance(value, str):
                        match = re.search(dest_pc_extract, value)
                        if match:
                             base_row["dest_postal_code"] = match.group(1)
                             if len(match.groups()) > 1:
                                 base_row["dest_city"] = match.group(2).strip()
                        else:
                             base_row["dest_postal_code"] = value
                    else:
                        base_row["dest_postal_code"] = value
                    
                    if "dest_city" not in base_row:
                         base_row["dest_city"] = value # Fallback

                elif normalized_col in alias_map:
                    for target_field in alias_map[normalized_col]:
                        base_row[target_field] = value
                elif self._normalize(col_name) in self.default_mapping:
                     base_row[self._normalize(col_name)] = value

            # Defaults
            defaults = partner_config.get("defaults", {})
            for field, value in defaults.items():
                if field not in base_row or base_row[field] is None:
                    base_row[field] = value

            # Itération sur les brackets configurés
            for bracket in brackets:
                header = bracket.get("header")
                found_val = None
                norm_header = self._normalize(header)
                
                if header in row:
                    found_val = row[header]
                else:
                    for rk, rv in row.items():
                        if self._normalize(rk) == norm_header:
                            found_val = rv
                            break
                
                cleaned_cost = self._clean_decimal(found_val)
                
                if cleaned_cost is not None:
                    new_row = base_row.copy()
                    new_row["weight_min"] = bracket["weight_min"]
                    new_row["weight_max"] = bracket["weight_max"]
                    new_row["pricing_type"] = bracket.get("pricing_type", "PER_100KG")
                    new_row["cost"] = cleaned_cost
                    mapped_rows.append(new_row)

        else:
            mapped_row = {}
            for col_name, value in row.items():
                normalized_col = self._normalize(col_name)
                if normalized_col in alias_map:
                    for target_field in alias_map[normalized_col]:
                        mapped_row[target_field] = value
                elif col_name in self.default_mapping:
                    mapped_row[col_name] = value
            
            # Defaults flat
            defaults = partner_config.get("defaults", {})
            for field, value in defaults.items():
                if field not in mapped_row or mapped_row[field] is None:
                    mapped_row[field] = value
            
            # Clean generic cost if present
            if "cost" in mapped_row:
                 mapped_row["cost"] = self._clean_decimal(mapped_row.get("cost"))

            if mapped_row.get("cost") is not None:
                mapped_rows = [mapped_row]
            else:
                mapped_rows = []
            
        
        # --- PHASE FINALE : TRANSFORMS & CLEANUP ---
        final_rows = []
        transforms = partner_config.get("transforms", {})
        
        for r in mapped_rows:
            # 1. Casting (CP, Strings)
            for key in ["origin_postal_code", "dest_postal_code", "origin_city", "dest_city", "origin_country", "dest_country", "pricing_type"]:
                if key in r and r[key] is not None:
                     val_str = str(r[key]).strip()
                     
                     # 1. Apply Transforms (Exact Match)
                     if key in transforms and val_str in transforms[key]:
                         val_str = transforms[key][val_str]
                     
                     # Formatage spécifique CP (2 caractères min si numérique, ex: '1' -> '01')
                     if key in ["origin_postal_code", "dest_postal_code"] and val_str.isdigit() and len(val_str) < 2:
                         val_str = val_str.zfill(2)
                     r[key] = val_str
            
            final_rows.append(r)


        # --- LOGIQUE SINGLE GRID (MONACO ITALIE) ---
        return final_rows

    def _clean_decimal(self, value: Any) -> Optional[float]:
        """Convertit une valeur en float, renvoie None si impossible ou vide."""
        if value is None:
            return None
        if isinstance(value, float):
            if pd.isna(value) or math.isnan(value):
                return None
            return value
        if isinstance(value, int):
            return float(value)
        
        # String cleanup
        s_val = str(value).strip().replace(",", ".").replace(" ", "")
        if not s_val:
            return None
        try:
            return float(s_val)
        except ValueError:
            return None

    def _normalize(self, text: str) -> str:
        if text is None:
            return ""
        if not isinstance(text, str):
            return str(text)
        text = text.lower().strip()
        try:
            text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
        except:
            pass
        return text.replace(" ", "_").replace("-", "_")

    def _parse_weight_key(self, val: Any, prev_weight_max: float = 0.0) -> tuple:
        """
        Parse weight keys like "0-20", "-50", "50", "100".
        Returns (min, max).
        """
        s_val = str(val).strip().replace(" ", "")
        try:
            # "0-20"
            if "-" in s_val and not s_val.startswith("-"):
                parts = s_val.split("-")
                if len(parts) == 2:
                    return float(parts[0]), float(parts[1])
            
            # "-50" -> prev_weight_max + 1 to 50
            if s_val.startswith("-"):
                 w_max = float(s_val[1:])
                 w_min = prev_weight_max + 1 if prev_weight_max > 0 else 0.0 # Ou + 0.01 ? Le client dit "21-50".
                 # Si "0-20" fini a 20. "21-50" -> min = 20 + 1 = 21.
                 # Si on met 20.01 ce serait plus précis pour float, mais souvent logistique = entier.
                 # On va assumer entier pour l'instant : +1
                 # MAIS : prev_weight_max pourrait être 0.
                 
                 # Fix: si prev est 0, alors min est 0.
                 # Non, "0-20" est explicite.
                 # "-50" est la 2eme ligne.
                 # Imaginons premiere ligne "-20". prev=0. min=0.
                 if prev_weight_max == 0.0:
                      return 0.0, w_max
                 return prev_weight_max + 1.0, w_max
            
            # "50" -> prev_weight_max + 1 to 50 (Sequential Logic)
            # This handles cases like 100, 200, 300 where each row is a bracket
            w_max = float(s_val)
            if prev_weight_max == 0.0:
                 return 0.0, w_max
            return prev_weight_max + 1.0, w_max
            
        except:
            return 0.0, 0.0
