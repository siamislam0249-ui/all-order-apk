# Tiffin Desk — Food Ordering & Menu Management

A food *selection and order-tracking* website built with Flask + SQLite.
There is **no price, currency, payment, or checkout system anywhere** —
users select food and quantities, place an order, and track its status.
Admins manage the menu, users, and order statuses.

Built from the hand-drawn wireframe: Login/Registration → Main Menu screen
with two separate buttons (**Main Menu** → Daily Lunch Menu, and
**Common Menu**) → food selection → order → Admin panel (item management,
order confirmation, delivery status).

---

## 1. Project structure

```
food_ordering_app/
├── app.py                  # Flask app: all routes
├── models.py                # SQLAlchemy models (User, FoodItem, Order, OrderItem)
├── extensions.py            # db / login_manager instances
├── init_db.py                # creates tables + default admin + sample menu
├── requirements.txt
├── instance/
│   └── database.db          # SQLite file (created automatically)
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html, login.html, register.html
    ├── main_menu.html        # the two-button chooser screen
    ├── daily_menu.html        # Main Menu → Daily Lunch Menu items only
    ├── common_menu.html       # Common Menu items only
    ├── cart.html, my_orders.html, order_detail.html, errors.html
    ├── _food_card.html        # reusable food card macro
    └── admin/
        ├── dashboard.html, orders.html, users.html, menu_items.html
        ├── _admin_nav.html, _menu_item_row.html
```

## 2. Requirements

- Python 3.10+ (works on 3.9–3.12)
- pip

## 3. Setup (run in VS Code's integrated terminal, or any terminal)

```bash
# 1. Open the food_ordering_app folder in VS Code

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize the database (creates tables + default admin + sample menu)
python init_db.py

# 5. Run the app
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## 4. Default admin account

`init_db.py` automatically creates one admin account if none exists:

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `admin123` |

**Log in with this account to reach `/admin`.** Please change the password
(or create a new admin manually and remove this one) before using the
site for anything real — see section 7 below.

Regular visitors use **Register** to create their own (non-admin) account.

## 5. Using the site

**As a user:**
1. Register / log in.
2. On the Menu screen, choose **Main Menu** (Daily Lunch Menu) or
   **Common Menu** — they are always shown separately, never mixed.
3. Pick a quantity and select items — they go into your **Order Basket**.
4. Open the basket and **Place order**. You'll get an Order ID (e.g.
   `ORD-4F2A9C1B`) and can track its status any time under **My Orders**.

**As an admin (`/admin`):**
- **Dashboard** — quick counts + a banner when new (Pending) orders arrive.
- **Orders** — see every order, who placed it, what was ordered, when,
  and change its status through: Pending → Confirmed → Preparing →
  Out for Delivery → Delivered.
- **Menu items** — add/edit/delete food items, assign them to the Daily
  Lunch Menu or Common Menu, and toggle "available today" without
  deleting the item (handy for rotating the daily menu).
- **Users** — see everyone who has registered.

## 6. Database

SQLite, stored at `instance/database.db`, created by `init_db.py`
(or automatically the first time `app.py` runs). Tables:

- `users` — id, username, password_hash, is_admin, created_at
- `food_items` — id, name, description, image_url, menu_type
  (`daily`/`common`), is_available, created_at
- `orders` — id, order_code, user_id, status, created_at
- `order_items` — id, order_id, food_item_id, food_name (snapshot),
  menu_type, quantity

To start over with a clean database, stop the app and delete
`instance/database.db`, then run `python init_db.py` again.

## 7. Security notes

- Passwords are hashed with Werkzeug's `generate_password_hash`
  (never stored in plain text).
- Admin-only routes are protected by an `admin_required` decorator —
  a normal user hitting `/admin/...` gets a 403 page, not the dashboard.
- All form inputs are validated server-side (required fields, minimum
  lengths, matching passwords, valid menu types/status values).
- Before any real-world use: change `app.config["SECRET_KEY"]` in
  `app.py` to a long random value (or set it via the `SECRET_KEY`
  environment variable), and change the default admin password.

## 8. Notes on the wireframe → implementation mapping

| Wireframe note | Implementation |
|---|---|
| `website → login page (login + registration)` | `/login`, `/register` |
| `username`, `password` fields | Registration/login forms |
| `Common Menu` + `Daily Lunch Menu` as separate boxes | `/menu` (chooser) → `/menu/daily`, `/menu/common` — always rendered as two distinct pages |
| Numbered food items under each menu | `FoodItem` rows tagged `menu_type='daily'` or `'common'`, editable by admin |
| `login page → Registration → Main menu` | Register redirects to Login, successful login redirects to `/menu` |
| `Admin page — All item change + Notification + Order confirm + Delivery Report` | `/admin/menu` (item CRUD), pending-order badge in nav, `/admin/orders` (confirm/status updates), status history shown per order |

No price, `৳`, total, payment, or checkout screen exists anywhere in the
codebase — the flow stops at order placement and status tracking.
