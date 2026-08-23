"""
Database models for the Food Ordering & Menu Management site.

Tables:
    User       - registered users (normal users + admins)
    FoodItem   - menu items, tagged as 'daily' (Daily Lunch Menu)
                 or 'common' (Common Menu)
    Order      - one order placed by a user (no price / payment data)
    OrderItem  - line items belonging to an Order (food + quantity)
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db

# Allowed order statuses, in their normal lifecycle order.
ORDER_STATUSES = [
    "Pending",
    "Confirmed",
    "Preparing",
    "Out for Delivery",
    "Delivered",
]

MENU_TYPES = ["daily", "common"]


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship("Order", backref="user", lazy=True)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username}>"


class FoodItem(db.Model):
    __tablename__ = "food_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(300), nullable=True)  # optional
    menu_type = db.Column(db.String(10), nullable=False)  # 'daily' or 'common'
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FoodItem {self.name} ({self.menu_type})>"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(30), default="Pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship(
        "OrderItem", backref="order", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order {self.order_code} - {self.status}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    food_item_id = db.Column(
        db.Integer, db.ForeignKey("food_items.id"), nullable=True
    )  # nullable: food may be deleted later, we keep a name snapshot
    food_name = db.Column(db.String(120), nullable=False)  # snapshot at order time
    menu_type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    food_item = db.relationship("FoodItem", backref="order_items", lazy=True)
