# app/routers/admin.py (full updated version)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DBUser, DBFoodItem
from app.auth import get_current_user, oauth2_scheme, hash_password
from app.schemas import UserCreate, FoodItemCreate, FoodItemResponse, UserResponse

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(oauth2_scheme)],
)

@router.get("/users/", response_model=list[UserResponse])
async def admin_list_users(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(DBUser).all()

@router.post("/bags/", response_model=FoodItemResponse)
async def admin_add_bag(food: FoodItemCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_food = DBFoodItem(**food.dict(), shop_id=user.id)
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.put("/bags/{bag_id}", response_model=FoodItemResponse)
async def admin_update_bag(bag_id: int, food: FoodItemCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == bag_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Bag not found")
    for key, value in food.dict().items():
        setattr(db_food, key, value)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.delete("/bags/{bag_id}", response_model=dict)
async def admin_delete_bag(bag_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == bag_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Bag not found")
    
    bag_owner = db.query(DBUser).filter(DBUser.id == db_food.shop_id).first()
    if not bag_owner:
        raise HTTPException(status_code=404, detail="Bag owner not found")
    
    if db_food.shop_id == user.id:
        db.delete(db_food)
        db.commit()
        return {"message": f"Bag {bag_id} deleted"}
    
    if bag_owner.role == "shop":
        if user.role == "super_admin" or (user.role == "admin" and user.can_delete_shop_products):
            db.delete(db_food)
            db.commit()
            return {"message": f"Bag {bag_id} deleted"}
        raise HTTPException(status_code=403, detail="Not authorized to delete shop products")
    
    if bag_owner.role in ["admin", "super_admin"] and user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this bag")
    
    db.delete(db_food)
    db.commit()
    return {"message": f"Bag {bag_id} deleted"}

@router.post("/add-admin", response_model=dict)
async def add_admin(user_data: UserCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin" and (user.role == "admin" and not user.can_add_admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    if db.query(DBUser).filter(DBUser.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    db_user = DBUser(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),  # Fixed typo here
        role="admin"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": f"Admin {db_user.username} added successfully", "role": db_user.role}

@router.delete("/delete-shop-products/{bag_id}", response_model=dict)
async def delete_shop_product(bag_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == bag_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Bag not found")
    
    bag_owner = db.query(DBUser).filter(DBUser.id == db_food.shop_id).first()
    if not bag_owner or bag_owner.role != "shop":
        raise HTTPException(status_code=400, detail="This item does not belong to a shop")
    
    if user.role == "super_admin" or (user.role == "admin" and user.can_delete_shop_products):
        db.delete(db_food)
        db.commit()
        return {"message": f"Shop product {bag_id} deleted"}
    raise HTTPException(status_code=403, detail="Not authorized to delete shop products")