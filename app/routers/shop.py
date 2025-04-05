from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DBUser, DBFoodItem
from app.auth import get_current_user, oauth2_scheme
from app.schemas import FoodItemCreate, FoodItemResponse

router = APIRouter(
    prefix="/shop",
    tags=["Shop"],
    dependencies=[Depends(oauth2_scheme)],
)

# Shop Endpoints
@router.post("/bags/", response_model=FoodItemResponse)
async def add_bag(food: FoodItemCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "shop":
        raise HTTPException(status_code=403, detail="Not authorized")
    db_food = DBFoodItem(**food.dict(), shop_id=user.id)  # Set shop_id to the current user's ID
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.put("/bags/{bag_id}", response_model=FoodItemResponse)
async def update_bag(bag_id: int, food: FoodItemCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "shop":
        raise HTTPException(status_code=403, detail="Not authorized")
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == bag_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Bag not found")
    if db_food.shop_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this bag")
    for key, value in food.dict().items():
        setattr(db_food, key, value)
    db.commit()
    db.refresh(db_food)
    return db_food

@router.delete("/bags/{bag_id}", response_model=dict)
async def delete_bag(bag_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role != "shop":
        raise HTTPException(status_code=403, detail="Not authorized")
    db_food = db.query(DBFoodItem).filter(DBFoodItem.id == bag_id).first()
    if not db_food:
        raise HTTPException(status_code=404, detail="Bag not found")
    if db_food.shop_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this bag")
    db.delete(db_food)
    db.commit()
    return {"message": f"Bag {bag_id} deleted"}