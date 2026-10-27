from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class SaleItemDTO:
    product_id: int
    quantity: int
    unit_price: int
    subtotal: int
    weight_grams: Optional[int] = None
    weight_unit: Optional[str] = None
    is_custom: bool = False
    custom_name: Optional[str] = None

@dataclass
class PaymentDTO:
    method: str
    amount_received: Optional[int] = 0
    card_last4: Optional[str] = None
    card_approval: Optional[str] = None
    transfer_bank: Optional[str] = None
    transfer_ref: Optional[str] = None
    transfer_name: Optional[str] = None
    amount_cash: Optional[int] = 0
    amount_card: Optional[int] = 0
    amount_transfer: Optional[int] = 0

@dataclass
class SaleCreateDTO:
    items: List[Dict[str, Any]]
    payment: Dict[str, Any]
    order_id: Optional[int] = None

@dataclass
class SessionOpenDTO:
    base_amount: int
    user_id: int
    store_id: int

@dataclass
class SessionCloseDTO:
    session_id: int
    actual_cash: int
