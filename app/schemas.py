# app/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Schema for admin creation (used by admins/superadmins)
class UserCreate(BaseModel):
    username: str
    password: str

# Schema for customer registration (no location or phone_number)
class CustomerCreate(BaseModel):
    username: str
    password: str

# Schema for shop registration
class ShopCreate(BaseModel):
    username: str
    password: str
    location: str  # Required for shops
    phone_number: str  # Required for shops

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    can_add_admin: bool
    can_delete_shop_products: bool
    location: Optional[str]  # Still in response because shops have it
    phone_number: Optional[str]  # Still in response because shops have it

    class Config:
        from_attributes = True

class FoodItemCreate(BaseModel):
    name: str
    original_price: float
    discount_price: float
    quantity: int

class FoodItemResponse(BaseModel):
    id: int
    name: str
    original_price: float
    discount_price: float
    quantity: int
    shop_id: int | None

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    food_item_id: int
    quantity: int = 1

class OrderResponse(BaseModel):
    id: int
    user_id: int
    food_item_id: int
    status: str
    created_at: datetime
    pickup_code: str
    quantity: int

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    amount: float