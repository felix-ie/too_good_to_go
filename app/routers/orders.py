# app/routers/orders.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DBOrder, DBFoodItem
from app.auth import get_current_user, oauth2_scheme
from app.schemas import OrderCreate, OrderResponse, PaymentRequest
from datetime import datetime
import random
import string

router = APIRouter(
    prefix="",
    tags=["Orders"],
    dependencies=[Depends(oauth2_scheme)],
)

# Generate unique pickup code
def generate_pickup_code(db: Session, length=6):
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not db.query(DBOrder).filter(DBOrder.pickup_code == code).first():
            return code

# Create Order
@router.post("/user/order/", response_model=OrderResponse)
async def create_order(order: OrderCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can place orders")
    
    bag = db.query(DBFoodItem).filter(DBFoodItem.id == order.food_item_id).first()
    if not bag:
        raise HTTPException(status_code=404, detail="Food item not found")
    if bag.quantity < order.quantity:
        raise HTTPException(status_code=400, detail="Not enough items available")
    
    pickup_code = generate_pickup_code(db)
    db_order = DBOrder(
        user_id=user.id,
        food_item_id=order.food_item_id,
        status="pending",
        pickup_code=pickup_code,
        quantity=order.quantity
    )
    bag.quantity -= order.quantity  # Reduce stock by ordered quantity
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

# Cancel Order
@router.post("/user/order/{order_id}/cancel", response_model=dict)
async def cancel_order(order_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_order = db.query(DBOrder).filter(DBOrder.id == order_id, DBOrder.user_id == user.id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if db_order.status != "pending":
        raise HTTPException(status_code=400, detail="Order cannot be cancelled")
    time_diff = (datetime.utcnow() - db_order.created_at).total_seconds() / 60
    if time_diff > 5:
        raise HTTPException(status_code=400, detail="Order can only be cancelled within 5 minutes")
    
    db_order.status = "cancelled"
    bag = db.query(DBFoodItem).filter(DBFoodItem.id == db_order.food_item_id).first()
    if bag:
        bag.quantity += db_order.quantity  # Restore stock on cancellation
    db.commit()
    return {"message": "Order cancelled"}

# Pay for Order
@router.post("/user/order/pay/{pickup_code}", response_model=dict)
async def pay_order(pickup_code: str, payment: PaymentRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_order = db.query(DBOrder).filter(DBOrder.pickup_code == pickup_code, DBOrder.user_id == user.id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if db_order.status != "pending":
        raise HTTPException(status_code=400, detail="Order cannot be paid")
    
    bag = db.query(DBFoodItem).filter(DBFoodItem.id == db_order.food_item_id).first()
    if not bag:
        raise HTTPException(status_code=404, detail="Food item not found")
    
    total_amount_due = bag.discount_price * db_order.quantity
    if payment.amount < total_amount_due:
        raise HTTPException(
            status_code=400,
            detail=f"Payment failed, not enough. Amount due: {total_amount_due}, Paid: {payment.amount}"
        )
    
    db_order.status = "paid"
    db.commit()
    return {"message": "Order paid", "amount_due": total_amount_due}

# Confirm Pickup and Delete Order
@router.post("/pickup/{pickup_code}", response_model=dict)
async def confirm_pickup(pickup_code: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_order = db.query(DBOrder).filter(DBOrder.pickup_code == pickup_code).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    if db_order.status != "paid":
        raise HTTPException(status_code=400, detail="Order not paid yet")
    
    db_order.status = "picked_up"
    db.commit()
    db.delete(db_order)  # Delete the order after pickup
    db.commit()
    return {"message": f"Pickup confirmed for order with code {pickup_code}"}

# Check Order Status
@router.get("/user/order/status/{pickup_code}", response_model=OrderResponse)
async def check_order_status(pickup_code: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    db_order = db.query(DBOrder).filter(DBOrder.pickup_code == pickup_code, DBOrder.user_id == user.id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

# List User Orders (Includes Cancelled)
@router.get("/user/orders/", response_model=list[OrderResponse])
async def list_user_orders(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "customer":
        raise HTTPException(status_code=403, detail="Only customers can view their orders")
    orders = db.query(DBOrder).filter(DBOrder.user_id == user.id).all()
    return orders if orders else []