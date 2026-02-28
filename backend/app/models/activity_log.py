import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_login  = Column(String(100))           # snapshot au moment de l'action
    user_role   = Column(String(50))            # snapshot du rôle
    action      = Column(String(100), nullable=False)   # ex: "search.performed"
    resource    = Column(String(50))            # ex: "customer_quote", "partner"
    resource_id = Column(String(100))
    details     = Column(JSONB, default=dict)   # données contextuelles libres
    ip_address  = Column(String(45))
    created_at  = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
