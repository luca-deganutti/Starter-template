from sqlalchemy.orm import Session
from app.models.purchase import Purchase

def create_purchase(
    db: Session,
    *,
    user_id: int,
    items_summary: str,
    total_amount: float,
    mp_payment_id: str,
    status: str,
    payment_type: str | None = None,
    currency: str = "ARS"
) -> Purchase:
    db_purchase = Purchase(
        user_id=user_id,
        items_summary=items_summary,
        total_amount=total_amount,
        mp_payment_id=mp_payment_id,
        status=status,
        payment_type=payment_type,
        currency=currency
    )
    db.add(db_purchase)
    db.flush()
    return db_purchase

def get_purchase_by_mp_id(db: Session, mp_payment_id: str) -> Purchase | None:
    return db.query(Purchase).filter(Purchase.mp_payment_id == mp_payment_id).first()

def get_user_purchases(db: Session, user_id: int) -> list[Purchase]:
    return db.query(Purchase).filter(Purchase.user_id == user_id).all()
