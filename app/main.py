# app/main.py
from fastapi import FastAPI, Depends
from fastapi.openapi.utils import get_openapi
from sqlalchemy.orm import Session
from app.database import get_db, Base, engine
from app.models import DBUser
from app.auth import hash_password
from app.routers import public, superadmin, admin, orders, shop  # Removed surprise_bag

app = FastAPI(
    title="Surprise Bag App API",
    description="API for managing surprise bags, users, and orders",
    version="1.0.0",
)

# Include all routers (removed surprise_bag)
app.include_router(public.router)
app.include_router(superadmin.router)
app.include_router(admin.router)
app.include_router(orders.router)
app.include_router(shop.router)

# Customize OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=[
            {"name": "Public", "description": "Public endpoints"},
            {"name": "Super Admin", "description": "Super Admin endpoints"},
            {"name": "Admin", "description": "Admin endpoints"},
            {"name": "Shop", "description": "Shop endpoints"},
            {"name": "Orders", "description": "Order endpoints"},  # Removed Surprise Bag tag
        ],
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/login",
                    "scopes": {}
                }
            }
        }
    }
    openapi_schema["security"] = [{"OAuth2PasswordBearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Create all tables in the database
Base.metadata.create_all(bind=engine)

# Create a default Super Admin user if none exists
def create_default_super_admin(db: Session):
    super_admin = db.query(DBUser).filter(DBUser.role == "super_admin").first()
    if not super_admin:
        default_super_admin_username = "superadmin"
        default_super_admin_password = "superpass"
        db_user = DBUser(
            username=default_super_admin_username,
            hashed_password=hash_password(default_super_admin_password),
            role="super_admin",
            can_add_admin=True,
            can_delete_shop_products=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"Created default Super Admin: username={default_super_admin_username}, password={default_super_admin_password}")

# Initialize the database with the default Super Admin
with Session(engine) as db:
    create_default_super_admin(db)