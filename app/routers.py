from fastapi import APIRouter, HTTPException, Depends, Form
from app.models import UserCreate, User, FoodItem, Favourite, Order, DBUser, DBFoodItem, DBFavourite, DBOrder
from app.auth import hash_password, verify_password, create_access_token
from app.dependencies import get_current_active_user, get_admin_user, get_super_admin_user
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

# ------------------- PUBLIC ENDPOINTS -------------------
@router.post("/register", response_model=User, tags=["Public"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(DBUser).filter(DBUser.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    db_user = DBUser(username=user.username, hashed_password=hash_password(user.password), role="user")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", tags=["Public"])
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/food/", response_model=List[FoodItem], tags=["Public"])
def list_food_items(db: Session = Depends(get_db)):
    return db.query(DBFoodItem).filter(DBFoodItem.quantity > 0).all()

# ------------------- AUTHENTICATED ENDPOINTS -------------------
@router.post("/favourite/", response_model=Favourite, tags=["Authenticated"])
def add_to_favourite(favourite: Favourite, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_favourite = DBFavourite(user_id=current_user.id, food_item_id=favourite.food_item_id, quantity=favourite.quantity)
    db.add(db_favourite)
    db.commit()
    db.refresh(db_favourite)
    return favourite  # Return Pydantic model without user_id

# ------------------- SUPER ADMIN ENDPOINTS -------------------
@router.get("/superadmin/users/", response_model=List[User], tags=["Super Admin"])
def superadmin_list_users(current_user: User = Depends(get_super_admin_user), db: Session = Depends(get_db)):
    return db.query(DBUser).all()

@router.post("/superadmin/make-admin/{username}", tags=["Super Admin"])
def superadmin_make_admin(username: str, current_user: User = Depends(get_super_admin_user), db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot change super admin role")
    user.role = "admin"
    db.commit()
    return {"message": f"{username} is now an admin"}

@router.post("/superadmin/grant-admin-permission/{username}", tags=["Super Admin"])
def superadmin_grant_admin_permission(username: str, current_user: User = Depends(get_super_admin_user), db: Session = Depends(get_db)):
    admin = db.query(DBUser).filter(DBUser.username == username, DBUser.role == "admin").first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    admin.can_add_admin = True
    db.commit()
    return {"message": f"{username} can now add admins"}

@router.post("/superadmin/food/", response_model=FoodItem, tags=["Super Admin"])
def superadmin_add_food_item(food: FoodItem, current_user: User = Depends(get_super_admin_user), db: Session = Depends(get_db)):
    if db.query(DBFoodItem).filter(DBFoodItem.id == food.id).first():
        raise HTTPException(status_code=400, detail="Food item ID already exists")
    db_food = DBFoodItem(**food.dict())
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.put("/superadmin/food/{food_id}", response_model=FoodItem, tags=["Super Admin"])
def superadmin_update_food_item(food_id: int, updated_food: FoodItem, current_user: User = Depends(get_super_admin_user), db: Session = Depends(get_db)):
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == food_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Food item not found")
    if updated_food.id != food_id:
        raise HTTPException(status_code=400, detail="Cannot change food item ID")
    for key, value in updated_food.dict().items():
        setattr(db_food, key, value)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.delete("/superadmin/food/{food_id}", tags=["Super Admin"])
def superadmin_delete_food_item(food_id: int, current_user: User = Depends(get_super_admin_user), db: Session = Depends(get_db)):
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == food_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Food item not found")
    db.delete(db_food)
    db.commit()
    return {"message": f"Food item {food_id} deleted"}

# ------------------- ADMIN ENDPOINTS -------------------
@router.get("/admin/users/", response_model=List[User], tags=["Admin"])
def admin_list_users(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return db.query(DBUser).all()

@router.post("/admin/food/", response_model=FoodItem, tags=["Admin"])
def admin_add_food_item(food: FoodItem, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    if db.query(DBFoodItem).filter(DBFoodItem.id == food.id).first():
        raise HTTPException(status_code=400, detail="Food item ID already exists")
    db_food = DBFoodItem(**food.dict())
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.put("/admin/food/{food_id}", response_model=FoodItem, tags=["Admin"])
def admin_update_food_item(food_id: int, updated_food: FoodItem, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == food_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Food item not found")
    if updated_food.id != food_id:
        raise HTTPException(status_code=400, detail="Cannot change food item ID")
    for key, value in updated_food.dict().items():
        setattr(db_food, key, value)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.delete("/admin/food/{food_id}", tags=["Admin"])
def admin_delete_food_item(food_id: int, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == food_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Food item not found")
    db.delete(db_food)
    db.commit()
    return {"message": f"Food item {food_id} deleted"}

@router.post("/admin/add-admin", response_model=User, tags=["Admin"])
def admin_add_admin(username: str, password: str, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    if current_user.role != "super_admin" and not current_user.can_add_admin:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if db.query(DBUser).filter(DBUser.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    db_admin = DBUser(username=username, hashed_password=hash_password(password), role="admin")
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

# ------------------- USER ENDPOINTS -------------------
@router.post("/user/order/", response_model=Order, tags=["User"])
def user_create_order(food_item_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == food_item_id).first()
    if not db_food or db_food.quantity <= 0:
        raise HTTPException(status_code=404, detail="Food item not found or out of stock")
    db_order = DBOrder(user_id=current_user.id, food_item_id=food_item_id, order_time=datetime.now().isoformat())
    db_food.quantity -= 1
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@router.post("/user/order/{order_id}/cancel", tags=["User"])
def user_cancel_order(order_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_order = db.query(DBOrder).filter(DBOrder.id == order_id, DBOrder.user_id == current_user.id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    order_time = datetime.fromisoformat(db_order.order_time)
    if datetime.now() - order_time > timedelta(minutes=5):
        raise HTTPException(status_code=400, detail="Cannot cancel after 5 minutes")
    if db_order.is_cancelled:
        raise HTTPException(status_code=400, detail="Order already cancelled")
    db_order.is_cancelled = True
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == db_order.food_item_id).first()
    if db_food:
        db_food.quantity += 1
    db.commit()
    return {"message": "Order cancelled"}