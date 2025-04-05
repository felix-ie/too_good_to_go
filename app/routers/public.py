# app/routers/public.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DBUser, DBFoodItem
from app.auth import hash_password, create_access_token, verify_password
from app.schemas import CustomerCreate, ShopCreate, FoodItemResponse, UserResponse

router = APIRouter(
    prefix="",
    tags=["Public"],
)

# Customer Registration (no location or phone_number)
@router.post("/register/customer", response_model=dict)
async def register_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    if db.query(DBUser).filter(DBUser.username == customer.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    db_user = DBUser(
        username=customer.username,
        hashed_password=hash_password(customer.password),
        role="customer"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token(data={"sub": customer.username})
    return {
        "username": db_user.username,
        "role": db_user.role,
        "location": db_user.location,  # Will be null
        "phone_number": db_user.phone_number,  # Will be null
        "access_token": access_token
    }

# Shop Registration
@router.post("/register/shop", response_model=dict)
async def register_shop(shop: ShopCreate, db: Session = Depends(get_db)):
    if db.query(DBUser).filter(DBUser.username == shop.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    db_user = DBUser(
        username=shop.username,
        hashed_password=hash_password(shop.password),
        role="shop",
        location=shop.location,
        phone_number=shop.phone_number
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token = create_access_token(data={"sub": shop.username})
    return {
        "username": db_user.username,
        "role": db_user.role,
        "location": db_user.location,
        "phone_number": db_user.phone_number,
        "access_token": access_token
    }

# Existing Endpoints
@router.post("/login", response_model=dict)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/bags/", response_model=list[FoodItemResponse])
async def list_bags(db: Session = Depends(get_db)):
    return db.query(DBFoodItem).all()

@router.get("/shops/", response_model=list[UserResponse])
async def list_shops(db: Session = Depends(get_db)):
    shops = db.query(DBUser).filter(DBUser.role == "shop").all()
    if not shops:
        raise HTTPException(status_code=404, detail="No shops found")
    return shops

@router.get("/shops/{shop_id}/products/", response_model=list[FoodItemResponse])
async def list_shop_products(shop_id: int, db: Session = Depends(get_db)):
    shop = db.query(DBUser).filter(DBUser.id == shop_id, DBUser.role == "shop").first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    products = db.query(DBFoodItem).filter(DBFoodItem.shop_id == shop_id).all()
    if not products:
        raise HTTPException(status_code=404, detail="No products found for this shop")
    return products