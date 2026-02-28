"""
Tests unitaires — services/import_logic/row_validator.py
Couvre les cas 6.1 à 6.6 du PLAN_UNITAIRES.md

RowValidator.validate() retourne un ValidationResult (is_valid, data, errors).
"""
import pytest
from app.services.import_logic.row_validator import RowValidator


@pytest.fixture
def validator():
    return RowValidator()


VALID_ROW = {
    "transport_mode": "road",
    "origin_city": "Paris",
    "origin_country": "FR",
    "dest_city": "Lyon",
    "dest_country": "FR",
    "cost": 150.0,
}


class TestRowValidator:
    def test_valid_row_passes(self, validator):
        result = validator.validate(VALID_ROW)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_required_field(self, validator):
        row = {**VALID_ROW}
        del row["origin_city"]
        result = validator.validate(row)
        assert result.is_valid is False
        fields = [e.field for e in result.errors]
        assert "origin_city" in fields

    def test_negative_cost_fails(self, validator):
        result = validator.validate({**VALID_ROW, "cost": -10.0})
        assert result.is_valid is False

    def test_zero_cost_fails(self, validator):
        """cost doit être > 0 (Field(gt=0))."""
        result = validator.validate({**VALID_ROW, "cost": 0.0})
        assert result.is_valid is False

    def test_invalid_country_code_fails(self, validator):
        """Code pays doit faire exactement 2 caractères."""
        result = validator.validate({**VALID_ROW, "origin_country": "FRANCE"})
        assert result.is_valid is False
        fields = [e.field for e in result.errors]
        assert "origin_country" in fields

    def test_unknown_transport_mode_fails(self, validator):
        result = validator.validate({**VALID_ROW, "transport_mode": "flying_carpet"})
        assert result.is_valid is False
        fields = [e.field for e in result.errors]
        assert "transport_mode" in fields
