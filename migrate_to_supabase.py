import sqlite3
from app import app
from extensions import db
from models import User, FoodItem

SQLITE_DB = "instance/database.db"

conn = sqlite3.connect(SQLITE_DB)
conn.row_factory = sqlite3.Row

with app.app_context():
    # Admin
    admin = conn.execute(
        "SELECT username, password_hash, is_admin FROM users WHERE is_admin=1 LIMIT 1"
    ).fetchone()

    if admin:
        existing_admin = User.query.filter_by(username=admin["username"]).first()

        if not existing_admin:
            user = User(
                username=admin["username"],
                password_hash=admin["password_hash"],
                is_admin=True
            )
            db.session.add(user)
            print("[ok] Admin migrated")
        else:
            existing_admin.password_hash = admin["password_hash"]
            existing_admin.is_admin = True
            print("[ok] Admin already exists - password hash updated")

    # Menu
    foods = conn.execute("""
        SELECT name, description, image_url, menu_type, is_available, created_at
        FROM food_items
        ORDER BY id
    """).fetchall()

    for food in foods:
        existing = FoodItem.query.filter_by(
            name=food["name"],
            menu_type=food["menu_type"]
        ).first()

        if not existing:
            item = FoodItem(
                name=food["name"],
                description=food["description"],
                image_url=food["image_url"],
                menu_type=food["menu_type"],
                is_available=bool(food["is_available"])
            )
            db.session.add(item)
            print("[ok] Menu migrated:", food["name"])
        else:
            print("[skip] Menu already exists:", food["name"])

    db.session.commit()

conn.close()

print("\nMigration complete!")
