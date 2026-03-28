from pydantic import BaseModel

class PaymentItem(BaseModel):
    title: str
    quantity: int = 1
    unit_price: float
    currency_id: str = "ARS"

class PurchaseCreate(BaseModel):
    items: list[PaymentItem]

class PreferenceResponse(BaseModel):
    preference_id: str
    