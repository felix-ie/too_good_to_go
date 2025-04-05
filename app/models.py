# app/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="customer")
    can_add_admin = Column(Integer, default=0)
    can_delete_shop_products = Column(Integer, default=0)
    location = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)

    orders = relationship("DBOrder", back_populates="user")

class DBFoodItem(Base):
    __tablename__ = "food_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    original_price = Column(Float)
    discount_price = Column(Float)
    quantity = Column(Integer)
    shop_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    orders = relationship("DBOrder", back_populates="food_item")

class DBOrder(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_item_id = Column(Integer, ForeignKey("food_items.id"))
    status = Column(String, default="pending")  # pending, paid, picked_up, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    pickup_code = Column(String, unique=True, index=True)
    quantity = Column(Integer, default=1)  # New field for order quantity

    user = relationship("DBUser", back_populates="orders")
    food_item = relationship("DBFoodItem", back_populates="orders")