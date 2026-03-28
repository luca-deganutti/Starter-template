from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.payment import PurchaseCreate, PreferenceResponse
from app.services import payment_service

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/create-preference", response_model=PreferenceResponse)
def create_preference(
    purchase: PurchaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db) # Incluido por si luego necesitas validar contra DB
) -> PreferenceResponse:
    """
    Crea una preferencia de pago en Mercado Pago para una lista de items.
    Solo accesible por usuarios logueados.
    """
    preference_id = payment_service.create_payment_preference(current_user, purchase)
    return PreferenceResponse(preference_id=preference_id)

@router.post("/webhook")
async def mp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para recibir notificaciones (Webhooks) de Mercado Pago.
    Este endpoint es público y Mercado Pago hará POST aquí.
    """
    body = await request.json()
    action = body.get("action")
    data_id = body.get("data", {}).get("id")
    
    if (action == "payment.created" or action == "payment.updated") and data_id:
        # Se procesa el pago y se actualiza en DB si fue aprobado
        payment_service.process_payment_update(db, data_id)
        
    # Siempre retornar 200 OK rápidamente para que MP sepa que recibimos el webhook
    return {"status": "ok"}

@router.get("/check-status/{mp_payment_id}")
def check_status(
    mp_payment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint seguro para que el Frontend verifique si el pago ya impactó en la BD.
    Usa el registro creado por el Webhook.
    """
    return payment_service.get_purchase_status(db, mp_payment_id)
