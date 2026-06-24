from datetime import datetime
from dataclasses import dataclass

@dataclass
class Cart:
    cart_id: int
    user_id: int
    created_at: datetime

@dataclass
class CartItem:
    cart_item_id: int
    cart_id: int
    product_id: int
    quantity: int
    product_name: str
    price: float
    image: str
    
    @property
    def total(self) -> float:
        return self.price * self.quantity

@dataclass
class GuestCartItem:
    session_id: str
    product_id: int
    quantity: int
    product_name: str
    price: float
    image: str
    
    @property
    def total(self) -> float:
        return self.price * self.quantity

