"""
Tests unitaires — services/matching_service.py
Couvre les cas 5.1 à 5.6 du PLAN_UNITAIRES.md

Les tests créent des PartnerQuote directement en DB via la fixture `db`.
"""
import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services.matching_service import MatchingService
from app.schemas.matching import QuoteSearchRequest
from app.models.partner_quote import PartnerQuote, TransportMode
from app.models.partner import Partner
from app.core import security
from app.models.user import User, UserRole


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_partner(db) -> Partner:
    p = Partner(name="Test Partner", code="TST")
    db.add(p)
    db.flush()
    return p


def _make_quote(db, partner_id, **kwargs) -> PartnerQuote:
    defaults = dict(
        transport_mode=TransportMode.road,
        origin_country="FR",
        dest_country="FR",
        origin_city="Paris",
        dest_city="Lyon",
        weight_min=0.0,
        weight_max=9999.0,
        cost=100.0,
        pricing_type="LUMPSUM",
        currency="EUR",
        is_active=True,
        valid_from=date.today() - timedelta(days=30),
        valid_until=date.today() + timedelta(days=30),
    )
    defaults.update(kwargs)
    q = PartnerQuote(partner_id=partner_id, **defaults)
    db.add(q)
    db.flush()
    return q


def _search(db, **kwargs) -> list:
    defaults = dict(
        origin_country="FR",
        dest_country="FR",
        origin_city="Paris",
        dest_city="Lyon",
        weight=100.0,
        transport_mode=None,
        origin_postal_code=None,
        dest_postal_code=None,
        shipping_date=date.today(),
    )
    defaults.update(kwargs)
    criteria = QuoteSearchRequest(**defaults)
    return MatchingService.search_quotes(db, criteria)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestSearchQuotes:
    def test_valid_search_returns_results(self, db):
        partner = _make_partner(db)
        _make_quote(db, partner.id)
        results = _search(db)
        assert len(results) >= 1

    def test_no_match_returns_empty_list(self, db):
        results = _search(db, origin_city="ZZZ_UNKNOWN", dest_city="ZZZ_UNKNOWN")
        assert results == []

    def test_filter_by_transport_mode(self, db):
        partner = _make_partner(db)
        _make_quote(db, partner.id, transport_mode=TransportMode.road)
        _make_quote(db, partner.id, transport_mode=TransportMode.air,
                    origin_city="Paris", dest_city="Lyon")
        road_results = _search(db, transport_mode=TransportMode.road)
        assert all(r.transport_mode == TransportMode.road for r in road_results)

    def test_filter_by_weight(self, db):
        partner = _make_partner(db)
        # Quote qui accepte jusqu'à 500 kg
        _make_quote(db, partner.id, weight_min=0.0, weight_max=500.0)
        # Quote qui n'accepte que les gros volumes
        _make_quote(db, partner.id, weight_min=1000.0, weight_max=5000.0)
        results = _search(db, weight=100.0)
        # Seule la première quote doit matcher (weight 100 dans 0-500)
        assert all(r.weight_min <= 100.0 <= r.weight_max for r in results)

    def test_expired_quote_not_in_results(self, db):
        partner = _make_partner(db)
        _make_quote(
            db, partner.id,
            valid_from=date(2020, 1, 1),
            valid_until=date(2020, 12, 31),   # expirée
        )
        results = _search(db)
        assert all(r.valid_until >= date.today() for r in results if r.valid_until)

    def test_inactive_quote_not_in_results(self, db):
        partner = _make_partner(db)
        _make_quote(db, partner.id, is_active=False)
        _make_quote(db, partner.id, is_active=True)
        results = _search(db)
        assert all(r.is_active for r in results)
