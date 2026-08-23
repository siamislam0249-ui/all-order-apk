"""
Database initialization / seed script.

Run this once before starting the app for the first time:
    python init_db.py

What it does:
    1. Creates all tables (if they don't already exist).
    2. Creates a default ADMIN account (username: admin / password: admin123)
       -- only if no admin account exists yet.
    3. Seeds a few example Daily Lunch Menu and Common Menu items
       -- only if the food_items table is empty.

Safe to re-run: it will not duplicate the admin account or the sample
menu items on subsequent runs.
"""
from app import app
from extensions import db
from models import User, FoodItem

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"

SAMPLE_DAILY_ITEMS = [
    {"name": "Rice", "description": "Steamed white rice"},
    {"name": "Chicken Curry", "description": "Home-style chicken curry"},
    {"name": "Fish Curry", "description": "Traditional fish curry"},
    {"name": "Mixed Vegetables", "description": "Seasonal vegetable mix"},
    {"name": "Dal", "description": "Lentil soup"},
]

SAMPLE_COMMON_ITEMS = [
    {"name": "Paratha", "description": "Flaky flatbread"},
    {"name": "Tea", "description": "Hot tea"},
    {"name": "Coffee", "description": "Hot coffee"},
    {"name": "Noodles", "description": "Stir-fried noodles"},
]


def run():
    with app.app_context():
        db.create_all()
        print("[ok] Tables created (or already existed).")

        if not User.query.filter_by(is_admin=True).first():
            admin = User(username=DEFAULT_ADMIN_USERNAME, is_admin=True)
            admin.set_password(DEFAULT_ADMIN_PASSWORD)
            db.session.add(admin)
            print(
                f"[ok] Default admin created -> "
                f"username: '{DEFAULT_ADMIN_USERNAME}', password: '{DEFAULT_ADMIN_PASSWORD}'"
            )
            print("     IMPORTANT: change this password after first login!")
        else:
            print("[skip] An admin account already exists.")

        if FoodItem.query.count() == 0:
            for data in SAMPLE_DAILY_ITEMS:
                db.session.add(FoodItem(menu_type="daily", is_available=True, **data))
            for data in SAMPLE_COMMON_ITEMS:
                db.session.add(FoodItem(menu_type="common", is_available=True, **data))
            print("[ok] Sample Daily Lunch Menu and Common Menu items added.")
        else:
            print("[skip] Food items already exist, sample data not re-added.")

        db.session.commit()
        print("\nDatabase is ready. You can now run: python app.py")


if __name__ == "__main__":
    run()
