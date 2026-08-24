"""
Food Ordering & Menu Management - main Flask application.

Run locally:
    python app.py

See README.md for full setup instructions.
"""
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, redirect, url_for, request,
    flash, session, abort, jsonify
)
from flask_login import (
    login_user, logout_user, login_required, current_user
)

from extensions import db, login_manager
from models import User, FoodItem, Order, OrderItem, ORDER_STATUSES, MENU_TYPES

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    INSTANCE_DIR, "database.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
login_manager.init_app(app)
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def admin_required(view_func):
    """Only allow admin users through; everyone else gets a 403."""
    @wraps(view_func)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapped


def get_cart():
    """Cart is stored in the session as {food_item_id(str): quantity(int)}."""
    return session.setdefault("cart", {})


def cart_item_count():
    return sum(get_cart().values())


@app.context_processor
def inject_globals():
    pending_count = 0
    if current_user.is_authenticated and current_user.is_admin:
        pending_count = Order.query.filter_by(status="Pending").count()
    return dict(
        cart_count=cart_item_count() if current_user.is_authenticated else 0,
        pending_order_count=pending_count,
        current_year=datetime.utcnow().year,
    )


def generate_order_code():
    return "ORD-" + uuid.uuid4().hex[:8].upper()


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("menu_home"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("menu_home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", username=username)

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", username="")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("menu_home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("menu_home"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("cart", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Main menu chooser (the two-button screen from the wireframe)
# ---------------------------------------------------------------------------

@app.route("/menu")
@login_required
def menu_home():
    return render_template("main_menu.html")


@app.route("/menu/daily")
@login_required
def menu_daily():
    items = FoodItem.query.filter_by(menu_type="daily", is_available=True).all()
    return render_template("daily_menu.html", items=items, cart=get_cart())


@app.route("/menu/common")
@login_required
def menu_common():
    items = FoodItem.query.filter_by(menu_type="common", is_available=True).all()
    return render_template("common_menu.html", items=items, cart=get_cart())


# ---------------------------------------------------------------------------
# Cart & ordering
# ---------------------------------------------------------------------------

@app.route("/cart/add", methods=["POST"])
@login_required
def cart_add():
    food_id = request.form.get("food_id")
    quantity = request.form.get("quantity", "1")
    return_to = request.form.get("return_to") or url_for("menu_home")

    item = db.session.get(FoodItem, int(food_id)) if food_id else None
    if not item or not item.is_available:
        flash("That item is not available.", "error")
        return redirect(return_to)

    try:
        quantity = max(1, min(20, int(quantity)))
    except ValueError:
        quantity = 1

    cart = get_cart()
    cart[str(item.id)] = cart.get(str(item.id), 0) + quantity
    session["cart"] = cart
    session.modified = True

    flash(f"Added {item.name} to your order.", "success")
    return redirect(return_to)


@app.route("/cart/remove/<int:food_id>", methods=["POST"])
@login_required
def cart_remove(food_id):
    cart = get_cart()
    cart.pop(str(food_id), None)
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart_view"))


@app.route("/cart")
@login_required
def cart_view():
    cart = get_cart()
    line_items = []
    for food_id_str, qty in cart.items():
        item = db.session.get(FoodItem, int(food_id_str))
        if item:
            line_items.append({"item": item, "quantity": qty})
    return render_template("cart.html", line_items=line_items)


@app.route("/cart/confirm", methods=["POST"])
@login_required
def cart_confirm():
    cart = get_cart()
    if not cart:
        flash("Your order is empty. Please select some food first.", "error")
        return redirect(url_for("menu_home"))

    order = Order(order_code=generate_order_code(), user_id=current_user.id, status="Pending")
    db.session.add(order)
    db.session.flush()  # get order.id before commit

    for food_id_str, qty in cart.items():
        item = db.session.get(FoodItem, int(food_id_str))
        if not item:
            continue
        db.session.add(OrderItem(
            order_id=order.id,
            food_item_id=item.id,
            food_name=item.name,
            menu_type=item.menu_type,
            quantity=qty,
        ))

    db.session.commit()
    session["cart"] = {}
    session.modified = True

    flash("Order placed successfully!", "success")
    return redirect(url_for("order_detail", order_id=order.id))


@app.route("/orders")
@login_required
def my_orders():
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("my_orders.html", orders=orders)


@app.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order or (order.user_id != current_user.id and not current_user.is_admin):
        abort(404)
    return render_template("order_detail.html", order=order, statuses=ORDER_STATUSES)


# ---------------------------------------------------------------------------
# Admin: dashboard
# ---------------------------------------------------------------------------

@app.route("/admin")
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status="Pending").count()
    total_items = FoodItem.query.count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_items=total_items,
        recent_orders=recent_orders,
    )


@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@app.route("/admin/orders")
@admin_required
def admin_orders():
    status_filter = request.args.get("status", "")
    query = Order.query
    if status_filter and status_filter in ORDER_STATUSES:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template(
        "admin/orders.html",
        orders=orders,
        statuses=ORDER_STATUSES,
        status_filter=status_filter,
    )


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)
    new_status = request.form.get("status")
    if new_status not in ORDER_STATUSES:
        flash("Invalid status.", "error")
        return redirect(url_for("admin_orders"))
    order.status = new_status
    db.session.commit()
    flash(f"Order {order.order_code} marked as {new_status}.", "success")
    return redirect(request.referrer or url_for("admin_orders"))


# ---------------------------------------------------------------------------
# Admin: menu management
# ---------------------------------------------------------------------------

@app.route("/admin/menu")
@admin_required
def admin_menu():
    daily_items = FoodItem.query.filter_by(menu_type="daily").all()
    common_items = FoodItem.query.filter_by(menu_type="common").all()
    return render_template(
        "admin/menu_items.html", daily_items=daily_items, common_items=common_items
    )


@app.route("/admin/menu/add", methods=["POST"])
@admin_required
def admin_menu_add():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    image_url = request.form.get("image_url", "").strip()
    menu_type = request.form.get("menu_type")

    if not name or menu_type not in MENU_TYPES:
        flash("Food name and a valid menu type are required.", "error")
        return redirect(url_for("admin_menu"))

    item = FoodItem(
        name=name,
        description=description or None,
        image_url=image_url or None,
        menu_type=menu_type,
        is_available=True,
    )
    db.session.add(item)
    db.session.commit()
    flash(f"Added \"{name}\" to the {menu_type} menu.", "success")
    return redirect(url_for("admin_menu"))


@app.route("/admin/menu/<int:item_id>/edit", methods=["POST"])
@admin_required
def admin_menu_edit(item_id):
    item = db.session.get(FoodItem, item_id)
    if not item:
        abort(404)

    name = request.form.get("name", "").strip()
    if not name:
        flash("Food name cannot be empty.", "error")
        return redirect(url_for("admin_menu"))

    item.name = name
    item.description = request.form.get("description", "").strip() or None
    item.image_url = request.form.get("image_url", "").strip() or None
    menu_type = request.form.get("menu_type")
    if menu_type in MENU_TYPES:
        item.menu_type = menu_type

    db.session.commit()
    flash(f"Updated \"{item.name}\".", "success")
    return redirect(url_for("admin_menu"))


@app.route("/admin/menu/<int:item_id>/delete", methods=["POST"])
@admin_required
def admin_menu_delete(item_id):
    item = db.session.get(FoodItem, item_id)
    if not item:
        abort(404)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"Deleted \"{name}\".", "info")
    return redirect(url_for("admin_menu"))


@app.route("/admin/menu/<int:item_id>/toggle", methods=["POST"])
@admin_required
def admin_menu_toggle(item_id):
    item = db.session.get(FoodItem, item_id)
    if not item:
        abort(404)
    item.is_available = not item.is_available
    db.session.commit()
    state = "available today" if item.is_available else "hidden from menu"
    flash(f"\"{item.name}\" is now {state}.", "info")
    return redirect(url_for("admin_menu"))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(403)
def forbidden(e):
    return render_template("errors.html", code=403, message="You don't have permission to view this page."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("errors.html", code=404, message="That page could not be found."), 404


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


