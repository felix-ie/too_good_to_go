# Food App - A Too Good To Go Inspired API
## Description
Developed by Hyunjin, this FastAPI-based web application is inspired by Too Good To Go, designed to bridge the gap between shops with surplus food and customers seeking affordable deals. Shops can register to list their food items with original and discounted prices, while customers can browse shops, place orders with quantities, pay with validation, and pick up using unique codes. The app features robust role-based access control (super admin, admin, shop, customer) and includes order management, payment processing, and real-time stock updates.
### Features
- **User Roles**: Super Admin (manage users), Admin (manage admins/products), Shop (list items), Customer (order food).
- **Shop Management**: List and manage food items with stock tracking.
- **Order System**: Order multiple items, receive unique pickup codes, pay with amount checks, and confirm pickup.
- **Payment**: Validates payment amounts based on order quantities and discount prices.
- **Stock Control**: Automatically adjusts item quantities on orders and cancellations.
## Project Structure
food_app/
├── app/
│   ├── init.py         # Package initializer
│   ├── main.py            # Main application entry point
│   ├── database.py        # SQLite database configuration
│   ├── auth.py            # Authentication utilities (JWT, OAuth2)
│   ├── models.py          # SQLAlchemy database models
│   ├── schemas.py         # Pydantic schemas for validation
│   └── routers/           # API endpoint routers
│       ├── init.py    # Router package initializer
│       ├── public.py      # Public routes (registration, login, shop listing)
│       ├── superadmin.py  # Super admin routes (user management)
│       ├── admin.py       # Admin routes (add admins, manage products)
│       ├── orders.py      # Customer order routes (order, pay, track)
│       └── shop.py        # Shop-specific routes (list items)
├── requirements.txt       # Python dependencies
├── .gitignore             # Files/folders to exclude from Git
└── README.md              # Project documentation (this file)

## Prerequisites
- **Python 3.13+**: Ensure Python is installed on your system.
- **Git**: For cloning the repository.
- **pip**: Python package manager (included with Python).
## Installation
Follow these steps to set up the project on your operating system.
### On Windows
1. **Clone the Repository**: `git clone https://github.com/hyunjin-9/to_good_to_go.git && cd food_app`
2. **Create a Virtual Environment**: `python -m venv venv && venv\Scripts\activate`
3. **Install Dependencies**: `pip install -r requirements.txt`
4. **Run the Application**: `uvicorn app.main:app --reload` (visit `http://127.0.0.1:8000/docs`)
### On macOS
1. **Clone the Repository**: `git clone https://github.com/hyunjin-9/to_good_to_go.git && cd food_app`
2. **Create a Virtual Environment**: `python3 -m venv venv && source venv/bin/activate`
3. **Install Dependencies**: `pip install -r requirements.txt`
4. **Run the Application**: `uvicorn app.main:app --reload` (visit `http://127.0.0.1:8000/docs`)
### On Linux
1. **Clone the Repository**: `git clone https://github.com/hyunjin-9/to_good_to_go.git && cd food_app`
2. **Create a Virtual Environment**: `python3 -m venv venv && source venv/bin/activate`
3. **Install Dependencies**: `pip install -r requirements.txt`
4. **Run the Application**: `uvicorn app.main:app --reload` (visit `http://127.0.0.1:8000/docs`)
## Usage
### Registering Users
- **Customer**: `POST /register/customer` `{"username": "customer1", "password": "pass123"}`
- **Shop**: `POST /register/shop` `{"username": "pizzashop", "password": "shoppass", "location": "789 Pizza St", "phone_number": "+9876543210"}`
### Logging In
- `POST /login`: `{"username": "customer1", "password": "pass123"}` (returns `access_token`)
### Browsing Shops
- List all shops: `GET /shops/`
- View a shop’s products: `GET /shops/{shop_id}/products/`
### Placing an Order
- `POST /user/order/` (with `Authorization: Bearer <token>`): `{"food_item_id": 1, "quantity": 2}` (returns `pickup_code`)
### Paying for an Order
- `POST /user/order/pay/{pickup_code}` (with token): `{"amount": 14.0}`
### Tracking Orders
- All orders: `GET /user/orders/` (with token)
- Specific order: `GET /user/order/status/{pickup_code}` (with token)
## Technologies
- **FastAPI**: High-performance web framework for the API.
- **SQLAlchemy**: ORM for SQLite database interactions.
- **Pydantic**: Data validation and schema enforcement.
- **Uvicorn**: ASGI server to run the application.
- **JWT**: Secure authentication with OAuth2 password flow.
## Additional Setup
### Generate `requirements.txt`
`pip freeze > requirements.txt`
### Configure `.gitignore`
venv/
food_app.db
pycache/
*.pyc
*.log

## Notes
- **Database**: `food_app.db` auto-generates on first run.
- **Default Super Admin**: `username: superadmin`, `password: superpass`.
- **Security**: For production, use environment variables for secrets (e.g., `SECRET_KEY` in `auth.py`).
## Contributing
1. Fork the repository.
2. Create a branch: `git checkout -b feature-name`.
3. Commit: `git commit -m "Add feature"`.
4. Push: `git push origin feature-name`.
5. Open a pull request.
