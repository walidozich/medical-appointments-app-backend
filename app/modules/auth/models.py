from datetime import datetime
from sqlalchemy import Column, String, DateTime
from app.db.base import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    token = Column(String, primary_key=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
