"""
Tests unitaires — services/customer_quote_service.py
Couvre les cas 8.1 à 8.8 du PLAN_UNITAIRES.md
"""
import pytest
import uuid
from app.services.customer_quote_service import CustomerQuoteService
from app.schemas.customer_quote import CustomerQuoteCreate, CustomerQuoteUpdate
from app.models.customer_quote import CustomerQuoteStatus
from app.models.user import User, UserRole
from app.core import security


def _make_user(db, login="sq_user"):
    u = User(
        login=login,
        email=f"{login}@test.com",
        hashed_password=security.hash_password("Password123!"),
        first_name="T", last_name="U",
        role=UserRole.COMMERCIAL, is_active=True, must_change_password=False,
    )
    db.add(u)
    db.flush()
    return u


def _quote_payload(**kwargs):
    defaults = dict(
        customer_name="ACME Corp",
        customer_email="acme@test.com",
    )
    defaults.update(kwargs)
    return CustomerQuoteCreate(**defaults)


class TestCreateQuote:
    def test_creates_quote_with_draft_status(self, db):
        user = _make_user(db)
        quote = CustomerQuoteService.create_quote(db, _quote_payload(), user_id=str(user.id))
        assert quote.status == CustomerQuoteStatus.DRAFT
        assert quote.customer_name == "ACME Corp"
        assert quote.reference is not None

    def test_reference_is_unique(self, db):
        user = _make_user(db, "sq_ref_user")
        q1 = CustomerQuoteService.create_quote(db, _quote_payload(), user_id=str(user.id))
        q2 = CustomerQuoteService.create_quote(db, _quote_payload(), user_id=str(user.id))
        assert q1.reference != q2.reference


class TestGetQuote:
    def test_get_existing_quote(self, db):
        user = _make_user(db, "sq_get_user")
        created = CustomerQuoteService.create_quote(db, _quote_payload(), user_id=str(user.id))
        found = CustomerQuoteService.get_quote(db, created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_nonexistent_quote_returns_none(self, db):
        result = CustomerQuoteService.get_quote(db, str(uuid.uuid4()))
        assert result is None


class TestUpdateQuote:
    def test_update_fields_in_draft(self, db):
        user = _make_user(db, "sq_upd_user")
        quote = CustomerQuoteService.create_quote(db, _quote_payload(), user_id=str(user.id))
        updated = CustomerQuoteService.update_quote(
            db, quote.id,
            CustomerQuoteUpdate(customer_name="Updated Corp"),
            user_id=str(user.id),
        )
        assert updated.customer_name == "Updated Corp"


class TestDeleteQuote:
    def test_delete_existing_quote(self, db):
        user = _make_user(db, "sq_del_user")
        quote = CustomerQuoteService.create_quote(db, _quote_payload(), user_id=str(user.id))
        result = CustomerQuoteService.delete_quote(db, quote.id)
        assert result is True
        assert CustomerQuoteService.get_quote(db, quote.id) is None

    def test_delete_nonexistent_quote_returns_false(self, db):
        result = CustomerQuoteService.delete_quote(db, str(uuid.uuid4()))
        assert result is False


class TestAddTransportItem:
    def test_invalid_partner_quote_raises(self, db):
        user = _make_user(db, "sq_item_user")
        quote = CustomerQuoteService.create_quote(db, _quote_payload(), user_id=str(user.id))
        with pytest.raises(ValueError, match="Partner rate not found"):
            CustomerQuoteService.add_transport_item(
                db, quote.id, str(uuid.uuid4()), weight=100.0
            )

    def test_invalid_quote_id_raises(self, db):
        with pytest.raises(ValueError, match="Quote not found"):
            CustomerQuoteService.add_transport_item(
                db, str(uuid.uuid4()), str(uuid.uuid4()), weight=100.0
            )
