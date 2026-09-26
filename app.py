from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "inventory-demo-secret-key"
DB_NAME = "inventory.db"
DEFAULT_GST_RATE = 18.0
LOW_STOCK_LIMIT = 5

PRODUCT_IMAGE_MAP = {
    "Mouse": "mouse.svg", "Keyboard": "keyboard.svg", "Cables": "cable.svg",
    "Accessories": "hub.svg", "Audio": "audio.svg", "Adapters": "adapter.svg",
    "RAM": "ram.svg", "Storage": "ssd.svg", "Graphics Card": "gpu.svg",
    "Cooling": "cooler.svg", "Power Supply": "psu.svg", "Power Backup": "ups.svg"
}

def product_code(product_id):
    return f"CMP-{int(product_id):03d}"

def product_image(category):
    return f"product-images/{PRODUCT_IMAGE_MAP.get(category, 'default.svg')}"

app.jinja_env.filters["product_code"] = product_code

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            gst_rate REAL NOT NULL DEFAULT 18,
            stock INTEGER NOT NULL DEFAULT 0,
            image TEXT NOT NULL DEFAULT 'product-images/default.svg'
        );
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            subtotal REAL NOT NULL DEFAULT 0,
            discount REAL NOT NULL DEFAULT 0,
            gst REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0,
            payment_method TEXT NOT NULL DEFAULT 'Cash',
            sale_date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            subtotal REAL NOT NULL,
            gst_rate REAL NOT NULL DEFAULT 18,
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)

    # Add columns when opening an older version of the project database.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(sales)").fetchall()}
    migrations = {
        "subtotal": "ALTER TABLE sales ADD COLUMN subtotal REAL NOT NULL DEFAULT 0",
        "discount": "ALTER TABLE sales ADD COLUMN discount REAL NOT NULL DEFAULT 0",
        "gst": "ALTER TABLE sales ADD COLUMN gst REAL NOT NULL DEFAULT 0",
        "payment_method": "ALTER TABLE sales ADD COLUMN payment_method TEXT NOT NULL DEFAULT 'Cash'",
    }
    product_columns = {row[1] for row in conn.execute("PRAGMA table_info(products)").fetchall()}
    if "gst_rate" not in product_columns:
        conn.execute("ALTER TABLE products ADD COLUMN gst_rate REAL NOT NULL DEFAULT 18")
    if "image" not in product_columns:
        conn.execute("ALTER TABLE products ADD COLUMN image TEXT NOT NULL DEFAULT 'product-images/default.svg'")
    # Give existing products a category-based image.
    for row in conn.execute("SELECT id, category FROM products").fetchall():
        conn.execute("UPDATE products SET image=? WHERE id=?", (product_image(row["category"]), row["id"]))
    item_columns = {row[1] for row in conn.execute("PRAGMA table_info(sale_items)").fetchall()}
    if "gst_rate" not in item_columns:
        conn.execute("ALTER TABLE sale_items ADD COLUMN gst_rate REAL NOT NULL DEFAULT 18")
    for column, sql in migrations.items():
        if column not in columns:
            conn.execute(sql)

    count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    if count == 0:
        conn.executemany(
            "INSERT INTO products (name, category, price, gst_rate, stock, image) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Wireless Mouse", "Mouse", 699.00, 18, 25, product_image("Mouse")),
                ("Gaming Mouse", "Mouse", 1299.00, 18, 12, product_image("Mouse")),
                ("USB Keyboard", "Keyboard", 899.00, 18, 18, product_image("Keyboard")),
                ("Mechanical Keyboard", "Keyboard", 2499.00, 18, 10, product_image("Keyboard")),
                ("Laptop Keyboard", "Keyboard", 1599.00, 18, 8, product_image("Keyboard")),
                ("HDMI Cable", "Cables", 399.00, 18, 30, product_image("Cables")),
                ("DisplayPort Cable", "Cables", 699.00, 18, 15, product_image("Cables")),
                ("USB Type-C Cable", "Cables", 299.00, 18, 40, product_image("Cables")),
                ("Ethernet LAN Cable", "Cables", 199.00, 18, 35, product_image("Cables")),
                ("USB Hub", "Accessories", 599.00, 18, 20, product_image("Accessories")),
                ("Webcam", "Accessories", 1499.00, 18, 14, product_image("Accessories")),
                ("Computer Speakers", "Audio", 1199.00, 18, 16, product_image("Audio")),
                ("Gaming Headset", "Audio", 1999.00, 18, 9, product_image("Audio")),
                ("Bluetooth Adapter", "Adapters", 449.00, 18, 22, product_image("Adapters")),
                ("Wi-Fi Adapter", "Adapters", 799.00, 18, 17, product_image("Adapters")),
                ("RAM 8GB DDR4", "RAM", 1899.00, 18, 12, product_image("RAM")),
                ("RAM 16GB DDR4", "RAM", 3299.00, 18, 7, product_image("RAM")),
                ("SSD 500GB", "Storage", 3499.00, 18, 10, product_image("Storage")),
                ("SSD 1TB", "Storage", 5999.00, 18, 6, product_image("Storage")),
                ("HDD 1TB", "Storage", 4499.00, 18, 11, product_image("Storage")),
                ("Graphics Card 4GB", "Graphics Card", 12499.00, 18, 5, product_image("Graphics Card")),
                ("Graphics Card 8GB", "Graphics Card", 21999.00, 18, 4, product_image("Graphics Card")),
                ("CPU Cooler", "Cooling", 1299.00, 18, 13, product_image("Cooling")),
                ("PC Power Supply 550W", "Power Supply", 3499.00, 18, 8, product_image("Power Supply")),
                ("UPS 600VA", "Power Backup", 2999.00, 18, 9, product_image("Power Backup")),
            ],
        )
    conn.commit()
    conn.close()


@app.route("/")
def home():
    conn = get_db()
    product_count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    stock_count = conn.execute("SELECT COALESCE(SUM(stock), 0) AS c FROM products").fetchone()["c"]
    sales_count = conn.execute("SELECT COUNT(*) AS c FROM sales").fetchone()["c"]
    revenue = conn.execute("SELECT COALESCE(SUM(total), 0) AS total FROM sales").fetchone()["total"]
    low_stock = conn.execute("SELECT * FROM products WHERE stock <= ? ORDER BY stock ASC", (LOW_STOCK_LIMIT,)).fetchall()
    recent_sales = conn.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 5").fetchall()
    today = datetime.now().strftime("%d-%m-%Y")
    today_sales = conn.execute("SELECT COALESCE(SUM(total), 0) AS total FROM sales WHERE sale_date LIKE ?", (today + "%",)).fetchone()["total"]
    conn.close()
    return render_template("index.html", product_count=product_count, stock_count=stock_count,
                           sales_count=sales_count, revenue=revenue, today_sales=today_sales,
                           low_stock=low_stock, recent_sales=recent_sales, low_stock_limit=LOW_STOCK_LIMIT)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/support")
def support():
    return render_template("support.html")


@app.route("/hello/<name>")
def hello(name):
    return render_template("hello.html", name=name)


@app.route("/inventory")
def inventory():
    q = request.args.get("q", "").strip()
    conn = get_db()
    if q:
        products = conn.execute(
            """SELECT * FROM products
               WHERE name LIKE ? OR category LIKE ? OR CAST(id AS TEXT) LIKE ?
               ORDER BY id DESC""", (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    else:
        products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("inventory.html", products=products, q=q, low_stock_limit=LOW_STOCK_LIMIT)


@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            category = request.form["category"].strip()
            price = float(request.form["price"])
            gst_rate = float(request.form.get("gst_rate", DEFAULT_GST_RATE))
            stock = int(request.form["stock"])
            if not name or not category or price < 0 or gst_rate < 0 or gst_rate > 100 or stock < 0:
                raise ValueError
        except (KeyError, ValueError):
            flash("Please enter valid product details.", "error")
            return redirect(url_for("add_product"))
        conn = get_db()
        conn.execute("INSERT INTO products (name, category, price, gst_rate, stock, image) VALUES (?, ?, ?, ?, ?, ?)",
                     (name, category, price, gst_rate, stock, product_image(category)))
        conn.commit(); conn.close()
        flash("Product added successfully.", "success")
        return redirect(url_for("inventory"))
    return render_template("add_product.html")


@app.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close(); return "Product not found", 404
    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            category = request.form["category"].strip()
            price = float(request.form["price"])
            gst_rate = float(request.form.get("gst_rate", DEFAULT_GST_RATE))
            stock = int(request.form["stock"])
            if not name or not category or price < 0 or gst_rate < 0 or gst_rate > 100 or stock < 0:
                raise ValueError
        except (KeyError, ValueError):
            conn.close(); flash("Please enter valid product details.", "error")
            return redirect(url_for("edit_product", product_id=product_id))
        conn.execute("UPDATE products SET name=?, category=?, price=?, gst_rate=?, stock=?, image=? WHERE id=?",
                     (name, category, price, gst_rate, stock, product_image(category), product_id))
        conn.commit(); conn.close()
        flash("Product updated successfully.", "success")
        return redirect(url_for("inventory"))
    conn.close()
    return render_template("edit_product.html", product=product)


@app.route("/remove-product/<int:product_id>", methods=["POST"])
def remove_product(product_id):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit(); conn.close()
    flash("Product removed.", "success")
    return redirect(url_for("inventory"))


@app.route("/billing", methods=["GET", "POST"])
def billing():
    conn = get_db()
    products = conn.execute("SELECT * FROM products WHERE stock > 0 ORDER BY name").fetchall()
    if request.method == "POST":
        customer = request.form.get("customer_name", "Walk-in Customer").strip() or "Walk-in Customer"
        payment_method = request.form.get("payment_method", "Cash")
        allowed_methods = {"Cash", "UPI", "Card", "Other"}
        if payment_method not in allowed_methods:
            payment_method = "Cash"
        product_ids = request.form.getlist("product_id")
        quantities = request.form.getlist("quantity")
        try:
            discount_percent = float(request.form.get("discount_percent", 0) or 0)
            if discount_percent < 0 or discount_percent > 100:
                raise ValueError
        except ValueError:
            conn.close(); flash("Discount must be between 0 and 100%.", "error")
            return redirect(url_for("billing"))

        items, subtotal, gst_total = [], 0.0, 0.0
        try:
            for pid, qty_text, gst_text in zip(product_ids, quantities, request.form.getlist("item_gst")):
                qty = int(qty_text)
                if qty <= 0: continue
                product = conn.execute("SELECT * FROM products WHERE id = ?", (int(pid),)).fetchone()
                if not product: continue
                if qty > product["stock"]:
                    flash(f"Not enough stock for {product['name']}.", "error")
                    conn.close(); return redirect(url_for("billing"))
                try:
                    item_gst_rate = float(gst_text or product["gst_rate"])
                    if item_gst_rate < 0 or item_gst_rate > 100: raise ValueError
                except ValueError:
                    conn.close(); flash("GST rate must be between 0 and 100%.", "error")
                    return redirect(url_for("billing"))
                line = product["price"] * qty
                subtotal += line
                items.append((product, qty, line, item_gst_rate))
            if not items:
                flash("Please select at least one product.", "error")
                conn.close(); return redirect(url_for("billing"))
            discount = subtotal * discount_percent / 100
            discount_factor = (subtotal - discount) / subtotal if subtotal else 0
            gst_total = sum(line * discount_factor * item_gst_rate / 100 for _, _, line, item_gst_rate in items)
            total = subtotal - discount + gst_total
            now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
            cur = conn.execute("""INSERT INTO sales
                (customer_name, subtotal, discount, gst, total, payment_method, sale_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (customer, subtotal, discount, gst, total, payment_method, now))
            sale_id = cur.lastrowid
            for product, qty, line, item_gst_rate in items:
                conn.execute("""INSERT INTO sale_items
                    (sale_id, product_id, product_name, quantity, price, subtotal, gst_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (sale_id, product["id"], product["name"], qty, product["price"], line, item_gst_rate))
                conn.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (qty, product["id"]))
            conn.commit(); conn.close()
            return redirect(url_for("bill", sale_id=sale_id))
        except (ValueError, TypeError):
            conn.close(); flash("Please enter valid quantities.", "error")
            return redirect(url_for("billing"))
    conn.close()
    return render_template("billing.html", products=products, default_gst=DEFAULT_GST_RATE)


@app.route("/bill/<int:sale_id>")
def bill(sale_id):
    conn = get_db()
    sale = conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
    items = conn.execute("SELECT * FROM sale_items WHERE sale_id = ?", (sale_id,)).fetchall()
    conn.close()
    if not sale: return "Bill not found", 404
    return render_template("bill.html", sale=sale, items=items)


@app.route("/sales")
def sales_history():
    conn = get_db()
    sales = conn.execute("SELECT * FROM sales ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("sales.html", sales=sales)


@app.route("/reports")
def reports():
    conn = get_db()
    total_sales = conn.execute("SELECT COALESCE(SUM(total),0) AS v FROM sales").fetchone()["v"]
    total_discount = conn.execute("SELECT COALESCE(SUM(discount),0) AS v FROM sales").fetchone()["v"]
    total_gst = conn.execute("SELECT COALESCE(SUM(gst),0) AS v FROM sales").fetchone()["v"]
    total_bills = conn.execute("SELECT COUNT(*) AS v FROM sales").fetchone()["v"]
    today = datetime.now().strftime("%d-%m-%Y")
    today_sales = conn.execute("SELECT COALESCE(SUM(total),0) AS v FROM sales WHERE sale_date LIKE ?", (today+"%",)).fetchone()["v"]
    monthly = conn.execute("""SELECT substr(sale_date, 4, 7) AS month, COUNT(*) AS bills,
        COALESCE(SUM(total),0) AS total FROM sales GROUP BY substr(sale_date, 4, 7) ORDER BY MAX(id) DESC""").fetchall()
    top_products = conn.execute("""SELECT product_name, SUM(quantity) AS quantity,
        COALESCE(SUM(subtotal),0) AS amount FROM sale_items GROUP BY product_name
        ORDER BY quantity DESC LIMIT 5""").fetchall()
    payment_summary = conn.execute("""SELECT payment_method, COUNT(*) AS bills,
        COALESCE(SUM(total),0) AS total FROM sales GROUP BY payment_method ORDER BY total DESC""").fetchall()
    conn.close()
    return render_template("reports.html", total_sales=total_sales, total_discount=total_discount,
                           total_gst=total_gst, total_bills=total_bills, today_sales=today_sales,
                           monthly=monthly, top_products=top_products, payment_summary=payment_summary)


@app.route("/search")
def search_product():
    q = request.args.get("q", "").strip()
    return redirect(url_for("inventory", q=q))


@app.route("/api/products")
def api_products():
    conn = get_db(); products = conn.execute("SELECT * FROM products ORDER BY id").fetchall(); conn.close()
    return jsonify([dict(p) for p in products])


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__("os").environ.get("PORT", 5000)), debug=True)
