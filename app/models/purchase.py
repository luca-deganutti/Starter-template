from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Datos de la transacción
    items_summary: Mapped[str] = mapped_column(String(500), nullable=False) # Resumen de lo comprado
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="ARS", nullable=False)
    
    # Datos de Mercado Pago
    mp_payment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False) # approved, pending, rejected, etc.
    payment_type: Mapped[str | None] = mapped_column(String(50), nullable=True) # credit_card, account_money, etc.
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relación con el usuario
    user: Mapped["User"] = relationship("User", backref="purchases")
