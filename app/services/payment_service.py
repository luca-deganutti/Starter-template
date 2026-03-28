import mercadopago
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User
from app.repositories import purchase_repository as purchase_repo
from app.schemas.payment import PurchaseCreate

def get_mp_sdk() -> mercadopago.SDK:
    settings = get_settings()
    if not settings.MP_ACCESS_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Mercado Pago SDK is not configured properly (missing MP_ACCESS_TOKEN)"
        )
    return mercadopago.SDK(settings.MP_ACCESS_TOKEN)

def create_payment_preference(user: User, purchase: PurchaseCreate, back_urls: dict | None = None) -> str:
    sdk = get_mp_sdk()
    
    items_data = []
    for item in purchase.items:
        items_data.append({
            "title": item.title,
            "quantity": item.quantity,
            "currency_id": item.currency_id,
            "unit_price": item.unit_price
        })
    
    preference_data = {
        "items": items_data,
        "payer": {
            "email": user.email
        },
        "external_reference": str(user.id)
    }
    
    if back_urls:
        preference_data["back_urls"] = back_urls
        preference_data["auto_return"] = "approved"
        
    response = sdk.preference().create(preference_data)
    
    if response["status"] >= 400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating MP preference: {response.get('response', {}).get('message', 'Unknown error')}"
        )
        
    return response["response"]["id"]

def process_payment_update(db: Session, data_id: str) -> dict:
    sdk = get_mp_sdk()
    
    payment_info = sdk.payment().get(data_id)
    
    if payment_info["status"] >= 400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error retrieving payment info from Mercado Pago"
        )
        
    payment = payment_info["response"]
    
    # Verifica si el pago fue aprobado
    if payment.get("status") == "approved":
        user_id_str = payment.get("external_reference")
        mp_payment_id = str(payment.get("id"))
        
        # Evitar duplicados (Mercado Pago puede mandar el mismo webhook varias veces)
        existing = purchase_repo.get_purchase_by_mp_id(db, mp_payment_id)
        if existing:
            return payment

        if user_id_str:
            try:
                user_id = int(user_id_str)
                
                # Resumen de los items
                items = payment.get("additional_info", {}).get("items", [])
                summary = ", ".join([i.get("title", "Item") for i in items]) if items else "Compra de productos"

                # Guardamos el registro oficial de la compra
                purchase_repo.create_purchase(
                    db,
                    user_id=user_id,
                    items_summary=summary,
                    total_amount=float(payment.get("transaction_amount", 0)),
                    mp_payment_id=mp_payment_id,
                    status="approved",
                    payment_type=payment.get("payment_type_id"),
                    currency=payment.get("currency_id", "ARS")
                )
                db.commit()
                print(f"[Webhook] Compra registrada exitosamente para el usuario ID: {user_id}")
            except Exception as e:
                db.rollback()
                print(f"[Webhook] Error al registrar compra: {str(e)}")
                
    return payment

def get_purchase_status(db: Session, mp_payment_id: str) -> dict:
    """Verifica en nuestra base de datos si el pago ya fue aprobado."""
    purchase = purchase_repo.get_purchase_by_mp_id(db, mp_payment_id)
    if purchase:
        return {"status": purchase.status, "mp_id": purchase.mp_payment_id}
    return {"status": "not_found"}

