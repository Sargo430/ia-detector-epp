from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDMixin, TimestampMixin


class Tenant(Base, UUIDMixin, TimestampMixin):
    """Lives in the public schema — one row per client organization."""
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    schema_name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    plan: Mapped[str] = mapped_column(String(30), default="starter")  # starter | pro | enterprise
    max_cameras: Mapped[int] = mapped_column(Integer, default=5)
    max_retention_days: Mapped[int] = mapped_column(Integer, default=30)
    contact_email: Mapped[str] = mapped_column(String(254), nullable=False)
