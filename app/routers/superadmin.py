from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DBUser, DBFoodItem
from app.auth import get_current_user, oauth2_scheme
from app.schemas import UserResponse, FoodItemCreate, FoodItemResponse

router = APIRouter(
    prefix="/superadmin",
    tags=["Super Admin"],
    dependencies=[Depends(oauth2_scheme)],
)

# Super Admin Endpoints
@router.get("/users/", response_model=list[UserResponse])
async def list_users(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(DBUser).all()

@router.post("/make-admin/{username}", response_model=dict)
async def make_admin(username: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user = db.query(DBUser).filter(DBUser.username == username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    target_user.role = "admin"
    db.commit()
    return {"message": f"{username} is now an admin"}

@router.post("/grant-admin-permission/{username}/grant", response_model=dict)
async def grant_admin_permission(username: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user = db.query(DBUser).filter(DBUser.username == username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.role != "admin":
        raise HTTPException(status_code=400, detail="User must be an admin to grant this permission")
    if target_user.can_add_admin:
        raise HTTPException(status_code=400, detail="User already has this permission")
    target_user.can_add_admin = True
    db.commit()
    return {"message": f"Admin permission granted to {username}"}

@router.post("/grant-admin-permission/{username}/revoke", response_model=dict)
async def revoke_admin_permission(username: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user = db.query(DBUser).filter(DBUser.username == username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot revoke admin permission for super_admin")
    if target_user.role != "admin":
        raise HTTPException(status_code=400, detail="User must be an admin to revoke this permission")
    if not target_user.can_add_admin:
        raise HTTPException(status_code=400, detail="User does not have this permission")
    target_user.can_add_admin = False
    db.commit()
    return {"message": f"Admin permission revoked for {username}"}

@router.post("/grant-delete-shop-products-permission/{username}/grant", response_model=dict)
async def grant_delete_shop_products_permission(username: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user = db.query(DBUser).filter(DBUser.username == username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.role != "admin":
        raise HTTPException(status_code=400, detail="User must be an admin to grant this permission")
    if target_user.can_delete_shop_products:
        raise HTTPException(status_code=400, detail="User already has this permission")
    target_user.can_delete_shop_products = True
    db.commit()
    return {"message": f"Delete shop products permission granted to {username}"}

@router.post("/grant-delete-shop-products-permission/{username}/revoke", response_model=dict)
async def revoke_delete_shop_products_permission(username: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    target_user = db.query(DBUser).filter(DBUser.username == username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.role == "super_admin":
        raise HTTPException(status_code=403, detail="Cannot revoke delete shop products permission for super_admin")
    if target_user.role != "admin":
        raise HTTPException(status_code=400, detail="User must be an admin to revoke this permission")
    if not target_user.can_delete_shop_products:
        raise HTTPException(status_code=400, detail="User does not have this permission")
    target_user.can_delete_shop_products = False
    db.commit()
    return {"message": f"Delete shop products permission revoked for {username}"}

@router.post("/bags/", response_model=FoodItemResponse)
async def add_bag(food: FoodItemCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db_food = DBFoodItem(**food.dict(), shop_id=user.id)  # Set shop_id to the current user's ID
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.put("/bags/{bag_id}", response_model=FoodItemResponse)
async def update_bag(bag_id: int, food: FoodItemCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
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
async def delete_bag(bag_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == bag_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Bag not found")
    db.delete(db_food)
    db.commit()
    return {"message": f"Bag {bag_id} deleted"}

@router.delete("/delete-shop-products/{bag_id}", response_model=dict)
async def delete_shop_product(bag_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Fetch the food item
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == bag_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Bag not found")
    
    # Check if the food item belongs to a shop
    bag_owner = db.query(DBUser).filter(DBUser.id == db_food.shop_id).first()
    if not bag_owner:
        raise HTTPException(status_code=404, detail="Bag owner not found")
    if bag_owner.role != "shop":
        raise HTTPException(status_code=400, detail="This item does not belong to a shop")
    
    # Super admin can delete the shop product
    db.delete(db_food)
    db.commit()
    return {"message": f"Shop product {bag_id} deleted"}