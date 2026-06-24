from flask import render_template, request, redirect, url_for, session, flash, jsonify, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from decimal import Decimal
from datetime import datetime, timedelta
import os
import time
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

def register_admin(app, mysql: MySQL):
    @app.route('/admin/dashboard')
    def admin_dashboard():
        if 'is_loggedin' in session and session['is_loggedin']:
            if 'user_role' in session and session['user_role'] == 'customer':
                print(session['user_role'])
                return redirect(url_for('customer_dashboard'))
        elif not 'is_loggedin' in session:
            return redirect(url_for('login'))

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            # Count only products from visible categories
            cursor.execute("""
                SELECT COUNT(*) as total_products 
                FROM products p
                JOIN categories c ON p.category = c.category_id
                WHERE c.visible = 1
            """)
            total_products = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) as total_users FROM users")
            total_users = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
            total_orders = cursor.fetchone()

            cursor.execute("SELECT SUM(total_amount) as total_revenue FROM orders WHERE status != 'Cancelled'")
            revenue_result = cursor.fetchone()
            total_revenue = revenue_result['total_revenue'] if revenue_result['total_revenue'] else 0

            # Top products - only from visible categories
            cursor.execute("""
                SELECT 
                    p.product_id,
                    p.name,
                    p.description,
                    p.price,
                    i.quantity,
                    p.img_path,
                    c.name,
                    COALESCE(SUM(oi.quantity), 0) as TotalSold,
                    COALESCE(SUM(oi.quantity * oi.price_at_purchase), 0) as TotalRevenue
                FROM Products p
                LEFT JOIN OrderItems oi ON p.product_id = oi.product_id
                LEFT JOIN Orders o ON oi.order_id = o.order_id AND o.status = 'Delivered'
                LEFT JOIN Categories c ON p.category = c.category_id
                JOIN Inventories i ON p.product_id = i.product_id
                WHERE p.visible = TRUE AND c.visible = 1
                GROUP BY p.product_id, p.name, p.description, p.price, i.quantity, p.img_path, c.name
                ORDER BY TotalSold DESC
                LIMIT 4
            """)
            top_products = cursor.fetchall()

        data = {
            "title": "Admin Dashboard",
            "total_products": total_products['total_products'],
            "total_orders": total_orders['total_orders'],
            "total_users": total_users['total_users'],
            "total_revenue": total_revenue,
            "top_products": top_products
        }

        return render_template('admin/dashboard.html', **data)
    
    @app.route('/admin/products')
    def manage_products():
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            # Show all products, but indicate if category is hidden
            cursor.execute("""SELECT 
                p.product_id AS product_id,
                p.name AS name,
                p.description AS description,
                p.price AS price,
                p.img_path AS img_path,
                p.visible AS visibility,
                c.name AS category,
                c.visible AS category_visible,
                i.quantity AS quantity
            FROM products p
            JOIN categories c ON p.category = c.category_id
            JOIN inventories i ON p.product_id = i.product_id
            """)
            products = cursor.fetchall()

            for product in products:
                product['price'] = "{:,.2f}".format(product['price'])
        
        return render_template('admin/product/products.html', title="Manage Products", products=products)
    
    @app.route('/admin/product/<int:product_id>')
    def admin_product_details(product_id):
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""SELECT 
                p.product_id, p.name, p.description, p.price, p.img_path, p.visible,
                c.name AS category, c.visible AS category_visible, i.quantity
            FROM products p
            JOIN categories c ON p.category = c.category_id
            JOIN inventories i ON p.product_id = i.product_id
            WHERE p.product_id = %s
            """, (product_id,))
            product = cursor.fetchone()
            print(f"Details: {product}")
        
        if not product:
            return "Product not found", 404
        
        success_message = request.args.get('success', None)
        
        return render_template(
            'admin/product/product_details.html',
            title=product['name'],
            product=product,
            success_message=success_message
        )
    
    @app.route('/admin/products/create', methods=['GET', 'POST'])
    def create_product():
        errors = {}

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            # Only show visible categories in dropdown
            cursor.execute('SELECT * FROM categories WHERE visible = 1')
            categories = cursor.fetchall()

        if request.method == "POST":
            name = request.form["name"].strip().title()
            desc = request.form["description"].strip().capitalize()
            price = request.form["price"].strip()
            quantity = request.form["stock"].strip()
            category = request.form["category"].strip()
            image = request.files["image"]
            visible = 1 if request.form.get("visible") == 'on' else 0

            if not name:
                errors['name'] = "Product name is required"
            
            if not desc:
                errors['description'] = "Product description is required"
            
            if not price:
                errors['price'] = "Product price is required"
            elif round(float(request.form["price"].strip()),2) <= 0:
                errors['price'] = "Product price must be greater than 0."

            if not quantity:
                errors['stock'] = "Product stock number is required"
            elif int(quantity) <= 0:
                errors['stock'] = "Product stock number must be greater than 0."

            if not category:
                errors['category'] = "Product category is required"

            if not image:
                errors['image'] = "Product image is required"

            if not errors:
                if image and image.filename != "":
                    filename = f"{int(time.time())}_{secure_filename(image.filename)}"
                    save_path = f"/uploads/products/{filename}"
                    image_path = os.path.join(app.config['UPLOAD_PRODUCT'], filename)
                    print(save_path)
                    print(image_path)
                    image.save(image_path)

                prc = round(float(request.form["price"].strip()),2)
                qty = int(request.form["stock"].strip())

                with mysql.connection.cursor() as cursor:
                    cursor.execute("""INSERT INTO products(name, description, price, category, img_path, visible) 
                        VALUES (%s, %s, %s, %s, %s, %s)""", (name, desc, prc, category, save_path, visible))
                    mysql.connection.commit()

                    last_id = cursor.lastrowid

                    cursor.execute("""INSERT INTO inventories(product_id, quantity) VALUES (%s, %s)""", (last_id, qty))
                    mysql.connection.commit()

                flash("Product created successfully!", "success")
                return redirect(url_for("manage_products"))
            
        return render_template("admin/product/add_product.html", title="Create Product", categories=categories, errors=errors)

    @app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
    def edit_product(product_id):
        errors = {}

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
            product = cursor.fetchone()
            if not product:
                flash("Product not found.", "danger")
                return redirect(url_for("manage_products"))

            cursor.execute("SELECT quantity FROM inventories WHERE product_id = %s", (product_id,))
            inventory = cursor.fetchone()
            current_quantity = inventory['quantity'] if inventory else 0

            # Only show visible categories in dropdown
            cursor.execute("SELECT * FROM categories WHERE visible = 1")
            categories = cursor.fetchall()

        if request.method == "POST":
            name = request.form["name"].strip().title()
            desc = request.form["description"].strip().capitalize()
            price = request.form["price"].strip()
            quantity = request.form["stock"].strip()
            category = request.form["category"].strip()
            image = request.files.get("image")
            visible = 1 if request.form.get("visible") == 'on' else 0

            if not name:
                errors['name'] = "Product name is required"
            if not desc:
                errors['description'] = "Product description is required"
            if not price:
                errors['price'] = "Product price is required"
            elif float(price) <= 0:
                errors['price'] = "Product price must be greater than 0."
            if not quantity:
                errors['stock'] = "Product stock number is required"
            elif int(quantity) < 0:
                errors['stock'] = "Product stock number must be 0 or greater."
            if not category:
                errors['category'] = "Product category is required"

            if not errors:
                if image and image.filename != "":
                    filename = f"{int(time.time())}_{secure_filename(image.filename)}"
                    save_path = f"/uploads/products/{filename}"
                    image_path = os.path.join(app.config['UPLOAD_PRODUCT'], filename)
                    image.save(image_path)
                else:
                    save_path = product['img_path']

                with mysql.connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE products 
                        SET name=%s, description=%s, price=%s, category=%s, img_path=%s, visible=%s 
                        WHERE product_id=%s
                    """, (name, desc, float(price), category, save_path, visible, product_id))
                    mysql.connection.commit()

                    if inventory:
                        cursor.execute("UPDATE inventories SET quantity=%s WHERE product_id=%s", (int(quantity), product_id))
                    else:
                        cursor.execute("INSERT INTO inventories(product_id, quantity) VALUES (%s, %s)", (product_id, int(quantity)))
                    mysql.connection.commit()

                flash("Product updated successfully!", "success")
                return redirect(url_for("manage_products"))

        return render_template(
            "admin/product/edit_product.html",
            title="Edit Product",
            product=product,
            stock=current_quantity,
            categories=categories,
            errors=errors
        )

    @app.route('/admin/product/delete/<int:id>', methods=['POST'])
    def delete_product(id):
        with mysql.connection.cursor() as cursor:
            cursor.execute('DELETE FROM `products` WHERE product_id = %s', (id,))
            mysql.connection.commit()

        flash("Product deleted successfully!", "success")
        return redirect(url_for("manage_products"))
    
   # Updated category management routes with visible field

    @app.route('/admin/categories')
    def manage_categories():
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""SELECT 
                c.category_id AS category_id,
                c.name AS name,
                c.description,
                c.visible,
                COUNT(p.product_id) AS count
            FROM categories c
            LEFT JOIN products p ON p.category = c.category_id
            GROUP BY c.category_id, c.name, c.description, c.visible;
            """)
            categories = cursor.fetchall()

        return render_template('admin/category/categories.html', title="Manage Categories", categories=categories)

    @app.route("/category/create", methods=["GET", "POST"])
    def create_category():
        errors = {}

        if request.method == "POST":
            name = request.form["name"].strip().title()
            desc = request.form["description"].strip().capitalize()
            visible = 1 if request.form.get("visible") == 'on' else 0

            if not name:
                errors['name'] = "Category name is required"
            
            if not desc:
                errors['description'] = "Category description is required"

            if not errors:
                with mysql.connection.cursor() as cursor:
                    cursor.execute('INSERT INTO categories (name, description, visible) VALUES (%s, %s, %s)', (name, desc, visible))
                    mysql.connection.commit()

                flash("Category created successfully!", "success")
                return redirect(url_for("manage_categories"))
            
        return render_template("admin/category/add_category.html", title="Create Category", errors=errors)

    @app.route("/admin/category/edit/<int:id>", methods=["GET", "POST"])
    def edit_category(id):
        errors = {}

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM categories WHERE category_id = %s', (id,))
            category = cursor.fetchone()

        if not category:
            flash("Category not found.", "danger")
            return redirect(url_for("manage_categories"))
        
        if request.method == "POST":
            name = request.form["name"].strip().title()
            desc = request.form["description"].strip().capitalize()
            visible = 1 if request.form.get("visible") == 'on' else 0

            if not name:
                errors['name'] = "Category name is required"
            
            if not desc:
                errors['description'] = "Category description is required"

            if not errors:
                with mysql.connection.cursor() as cursor:
                    cursor.execute('UPDATE categories SET name=%s, description=%s, visible=%s WHERE category_id=%s', (name, desc, visible, id))
                    mysql.connection.commit()

                flash("Category updated successfully!", "success")
                return redirect(url_for("manage_categories"))

        return render_template("admin/category/edit_category.html", category=category, errors=errors)

    @app.route("/admin/category/delete/<int:id>", methods=["POST"])
    def delete_category(id):
        with mysql.connection.cursor() as cursor:
            cursor.execute('DELETE FROM `categories` WHERE category_id = %s', (id,))
            mysql.connection.commit()

        flash("Category deleted successfully!", "success")
        return redirect(url_for("manage_categories"))

    @app.route("/admin/users")
    def manage_users():
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""SELECT 
                u.user_id,
                u.firstname,
                u.middlename,
                u.lastname,
                u.email,
                u.phone,
                u.status,
                p.province_name AS province,
                m.municipality_name AS municipality,
                b.barangay_name AS barangay
            FROM users u
            JOIN barangays b ON u.barangay = b.barangay_id
            JOIN municipalities m ON u.municipality = m.municipality_id
            JOIN provinces p ON u.province = p.province_id;
            """)
            users = cursor.fetchall()

        return render_template('admin/user/users.html', title="Manage Users", users=users)

    @app.route("/admin/user/edit/<int:user_id>", methods=["GET", "POST"])
    def edit_user(user_id):
        errors = {}

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""SELECT 
                u.user_id,
                u.firstname,
                u.middlename,
                u.lastname,
                u.email,
                u.phone,
                u.status,
                p.province_name AS province,
                m.municipality_name AS municipality,
                b.barangay_name AS barangay
            FROM users u
            JOIN barangays b ON u.barangay = b.barangay_id
            JOIN municipalities m ON u.municipality = m.municipality_id
            JOIN provinces p ON u.province = p.province_id
            WHERE u.user_id = %s;
            """, (user_id,))
            user = cursor.fetchone()

            if request.method == "POST":
                status = int(request.form['status'])

                with mysql.connection.cursor() as cursor:
                    cursor.execute('UPDATE `users` SET `status`=%s WHERE user_id = %s', (status, user_id))
                    mysql.connection.commit()

                flash("User updated successfully!", "success")
                return redirect(url_for("manage_users"))

        return render_template('admin/user/edit_user.html', title="Edit User", user=user, errors=errors)
    
    @app.route("/admin/user/reset-password/<int:user_id>", methods=["GET", "POST"])
    def reset_password(user_id):
        errors = {}

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            user = cursor.fetchone()

        if request.method == "POST":
            new = request.form['new_password'].strip()
            confirm = request.form['confirm_password'].strip()

            if not new:
                errors['new'] = "New password is required."
            elif len(new) < 8:
                errors["new"] = "Password must be at least 8 characters long."

            if not confirm:
                errors['confirm'] = "Please confirm the new password."
            elif not confirm == new:
                errors['confirm'] = "Password don't match."

            if not errors:
                with mysql.connection.cursor() as cursor:
                    cursor.execute('UPDATE `users` SET `password`=%s WHERE user_id = %s', (generate_password_hash(new), user_id))
                    mysql.connection.commit()

                flash("Password reset successfully!", "success")
                return redirect(url_for("manage_users"))

        return render_template('admin/user/reset_password.html', title="Reset Password", user=user, errors=errors)


    @app.route('/admin/orders')
    def manage_orders():
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT o.order_id, o.order_date, o.status, o.total_amount, 
                    o.tracking_number, o.delivery_address,
                    CONCAT(u.firstname, ' ', u.lastname) AS customer_name,
                    u.email AS customer_email,
                    COUNT(oi.order_item_id) as item_count,
                    p.method AS payment_method,
                    p.status AS payment_status
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.user_id
                LEFT JOIN orderitems oi ON o.order_id = oi.order_id
                LEFT JOIN payments p ON o.order_id = p.order_id
                GROUP BY o.order_id
                ORDER BY o.order_date DESC
            """)
            orders = cursor.fetchall()

        return render_template('admin/orders/orders.html', title="Manage Orders", orders=orders)

    @app.route('/admin/orders/<int:order_id>')
    def view_order(order_id):
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT o.order_id, o.order_date, o.status, o.total_amount, 
                    o.delivery_address, o.tracking_number, o.decline_reason,
                    CONCAT(u.firstname, ' ', u.lastname) AS customer_name,
                    u.email AS customer_email, u.phone AS customer_phone,
                    p.method AS payment_method, p.status AS payment_status,
                    p.payment_proof
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.user_id
                LEFT JOIN payments p ON o.order_id = p.order_id
                WHERE o.order_id = %s
            """, (order_id,))
            order = cursor.fetchone()

            if not order:
                flash("Order not found.", "danger")
                return redirect(url_for("manage_orders"))

            cursor.execute("""
                SELECT oi.order_item_id, oi.product_id, oi.quantity, 
                    oi.price_at_purchase, oi.sub_total,
                    p.name AS product_name, p.img_path
                FROM orderitems oi
                JOIN products p ON oi.product_id = p.product_id
                WHERE oi.order_id = %s
            """, (order_id,))
            order_items = cursor.fetchall()

            cursor.execute("""
                SELECT status, changed_at
                FROM order_status_history
                WHERE order_id = %s
                ORDER BY changed_at DESC
            """, (order_id,))
            status_history = cursor.fetchall()

        return render_template('admin/orders/order_details.html', 
                             title=f"Order #{order_id}", 
                             order=order, 
                             order_items=order_items,
                             status_history=status_history)

    @app.route('/admin/orders/<int:order_id>/approve', methods=['POST'])
    def approve_order(order_id):
        tracking_number = request.form.get('tracking_number', '').strip()

        if not tracking_number:
            flash("Tracking number is required to approve order.", "danger")
            return redirect(url_for('view_order', order_id=order_id))

        with mysql.connection.cursor() as cursor:
            cursor.execute("""
                UPDATE orders 
                SET status='Processing', tracking_number=%s 
                WHERE order_id=%s
            """, (tracking_number, order_id))

            cursor.execute("""
                INSERT INTO order_status_history (order_id, status, changed_at)
                VALUES (%s, %s, %s)
            """, (order_id, 'Processing', datetime.now()))

            mysql.connection.commit()

        flash("Order approved successfully!", "success")
        return redirect(url_for('view_order', order_id=order_id))

    @app.route('/admin/orders/<int:order_id>/decline', methods=['POST'])
    def decline_order(order_id):
        decline_reason = request.form.get('decline_reason', '').strip()

        if not decline_reason:
            flash("Decline reason is required.", "danger")
            return redirect(url_for('view_order', order_id=order_id))

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT oi.product_id, oi.quantity
                FROM orderitems oi
                WHERE oi.order_id = %s
            """, (order_id,))
            order_items = cursor.fetchall()

            for item in order_items:
                cursor.execute("""
                    UPDATE inventories 
                    SET quantity = quantity + %s 
                    WHERE product_id = %s
                """, (item['quantity'], item['product_id']))

            cursor.execute("""
                UPDATE orders 
                SET status='Cancelled', decline_reason=%s 
                WHERE order_id=%s
            """, (decline_reason, order_id))

            cursor.execute("""
                INSERT INTO order_status_history (order_id, status, changed_at)
                VALUES (%s, %s, %s)
            """, (order_id, 'Cancelled', datetime.now()))

            mysql.connection.commit()

        flash("Order declined successfully. Stock has been restored.", "success")
        return redirect(url_for('view_order', order_id=order_id))

    @app.route('/admin/orders/<int:order_id>/update-status', methods=['POST'])
    def update_order_status(order_id):
        new_status = request.form.get('status', '').strip()

        valid_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
        if new_status not in valid_statuses:
            flash("Invalid status.", "danger")
            return redirect(url_for('view_order', order_id=order_id))

        with mysql.connection.cursor() as cursor:
            cursor.execute("""
                UPDATE orders 
                SET status=%s 
                WHERE order_id=%s
            """, (new_status, order_id))

            if new_status == 'Delivered':
                cursor.execute("""
                    UPDATE payments 
                    SET status=%s 
                    WHERE order_id=%s
                """, ('Paid', order_id))

            cursor.execute("""
                INSERT INTO order_status_history (order_id, status, changed_at)
                VALUES (%s, %s, %s)
            """, (order_id, new_status, datetime.now()))

            mysql.connection.commit()

        flash(f"Order status updated to {new_status}!", "success")
        return redirect(url_for('view_order', order_id=order_id))
            
    @app.route('/admin/reports')
    def sales_reports():
        period = request.args.get('period', 'monthly')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        today = datetime.now()
        
        if period == 'daily':
            filter_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = "Today"
        elif period == 'weekly':
            filter_start = today - timedelta(days=today.weekday())
            filter_start = filter_start.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = "This Week"
        elif period == 'monthly':
            filter_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            filter_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = "This Month"
        elif period == 'custom' and start_date and end_date:
            filter_start = datetime.strptime(start_date, '%Y-%m-%d')
            filter_end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            period_label = f"{start_date} to {end_date}"
        else:
            filter_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            filter_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = "This Month"

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT o.order_id) as total_orders,
                    COALESCE(SUM(o.total_amount), 0) as gross_revenue,
                    COALESCE(SUM(CASE WHEN o.status != 'Cancelled' THEN o.total_amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN o.status = 'Delivered' THEN o.total_amount ELSE 0 END), 0) as delivered_revenue,
                    COALESCE(SUM(CASE WHEN o.status = 'Cancelled' THEN o.total_amount ELSE 0 END), 0) as cancelled_revenue,
                    COUNT(DISTINCT CASE WHEN o.status = 'Pending' THEN o.order_id END) as pending_orders,
                    COUNT(DISTINCT CASE WHEN o.status = 'Processing' THEN o.order_id END) as processing_orders,
                    COUNT(DISTINCT CASE WHEN o.status = 'Shipped' THEN o.order_id END) as shipped_orders,
                    COUNT(DISTINCT CASE WHEN o.status = 'Delivered' THEN o.order_id END) as delivered_orders,
                    COUNT(DISTINCT CASE WHEN o.status = 'Cancelled' THEN o.order_id END) as cancelled_orders
                FROM orders o
                WHERE o.order_date BETWEEN %s AND %s
            """, (filter_start, filter_end))
            summary = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    o.order_id,
                    o.order_date,
                    o.status,
                    o.total_amount,
                    CONCAT(u.firstname, ' ', u.lastname) as customer_name,
                    p.method as payment_method
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.user_id
                LEFT JOIN payments p ON o.order_id = p.order_id
                WHERE o.order_date BETWEEN %s AND %s
                ORDER BY o.order_date DESC
            """, (filter_start, filter_end))
            orders = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    p.product_id,
                    p.name as product_name,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.sub_total) as total_revenue,
                    COUNT(DISTINCT oi.order_id) as order_count
                FROM orderitems oi
                JOIN products p ON oi.product_id = p.product_id
                JOIN orders o ON oi.order_id = o.order_id
                WHERE o.order_date BETWEEN %s AND %s
                    AND o.status != 'Cancelled'
                GROUP BY p.product_id, p.name
                ORDER BY total_revenue DESC
                LIMIT 10
            """, (filter_start, filter_end))
            top_products = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    DATE(o.order_date) as date,
                    COUNT(DISTINCT o.order_id) as orders,
                    COALESCE(SUM(CASE WHEN o.status != 'Cancelled' THEN o.total_amount ELSE 0 END), 0) as revenue
                FROM orders o
                WHERE o.order_date BETWEEN %s AND %s
                GROUP BY DATE(o.order_date)
                ORDER BY date DESC
            """, (filter_start, filter_end))
            daily_breakdown = cursor.fetchall()

        return render_template('admin/reports/sales_reports.html',
                            title="Sales Reports",
                            summary=summary,
                            orders=orders,
                            top_products=top_products,
                            daily_breakdown=daily_breakdown,
                            period=period,
                            period_label=period_label,
                            start_date=start_date,
                            end_date=end_date)

    @app.route('/admin/reports/download')
    def download_report():
        period = request.args.get('period', 'monthly')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        format_type = request.args.get('format', 'pdf')

        today = datetime.now()
        
        if period == 'daily':
            filter_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = "Today"
        elif period == 'weekly':
            filter_start = today - timedelta(days=today.weekday())
            filter_start = filter_start.replace(hour=0, minute=0, second=0, microsecond=0)
            filter_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = "This Week"
        elif period == 'monthly':
            filter_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            filter_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = "This Month"
        elif period == 'custom' and start_date and end_date:
            filter_start = datetime.strptime(start_date, '%Y-%m-%d')
            filter_end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            period_label = f"{start_date} to {end_date}"
        else:
            filter_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            filter_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = "This Month"

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT o.order_id) as total_orders,
                    COALESCE(SUM(CASE WHEN o.status != 'Cancelled' THEN o.total_amount ELSE 0 END), 0) as total_revenue,
                    COALESCE(SUM(CASE WHEN o.status = 'Delivered' THEN o.total_amount ELSE 0 END), 0) as delivered_revenue,
                    COUNT(DISTINCT CASE WHEN o.status = 'Delivered' THEN o.order_id END) as delivered_orders
                FROM orders o
                WHERE o.order_date BETWEEN %s AND %s
            """, (filter_start, filter_end))
            summary = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    o.order_id,
                    o.order_date,
                    o.status,
                    o.total_amount,
                    CONCAT(u.firstname, ' ', u.lastname) as customer_name,
                    p.method as payment_method
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.user_id
                LEFT JOIN payments p ON o.order_id = p.order_id
                WHERE o.order_date BETWEEN %s AND %s
                ORDER BY o.order_date DESC
            """, (filter_start, filter_end))
            orders = cursor.fetchall()

            cursor.execute("""
                SELECT 
                    p.product_id,
                    p.name as product_name,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.sub_total) as total_revenue
                FROM orderitems oi
                JOIN products p ON oi.product_id = p.product_id
                JOIN orders o ON oi.order_id = o.order_id
                WHERE o.order_date BETWEEN %s AND %s
                    AND o.status != 'Cancelled'
                GROUP BY p.product_id, p.name
                ORDER BY total_revenue DESC
                LIMIT 10
            """, (filter_start, filter_end))
            top_products = cursor.fetchall()

        if format_type == 'pdf':
            return _generate_pdf_report(summary, orders, top_products, period_label, filter_start, filter_end)
        else:
            flash("Invalid format requested", "danger")
            return redirect(url_for('sales_reports'))

    def _generate_pdf_report(summary, orders, top_products, period_label, start_date, end_date):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        elements = []
        styles = getSampleStyleSheet()
        
        primary_color = colors.HexColor('#F89C20') 
        secondary_color = colors.HexColor('#4D4C45') 
        light_bg = colors.HexColor('#FFF9E6') 
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=primary_color,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=secondary_color,
            spaceAfter=12,
            spaceBefore=12
        )
        
        elements.append(Paragraph("🐾 PetSup Sales Report", title_style))
        elements.append(Paragraph(f"Period: {period_label}", styles['Normal']))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y %I:%M %p')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("Summary Statistics", heading_style))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Orders', str(summary['total_orders'] or 0)],
            ['Total Revenue (excluding cancelled)', f"PHP {summary['total_revenue'] or 0:,.2f}"],
            ['Delivered Orders', str(summary['delivered_orders'] or 0)],
            ['Delivered Revenue', f"PHP {summary['delivered_revenue'] or 0:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), light_bg),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        if top_products:
            elements.append(Paragraph("Top 10 Products", heading_style))
            
            products_data = [['Product Name', 'Quantity Sold', 'Revenue']]
            for product in top_products:
                products_data.append([
                    product['product_name'],
                    str(product['total_quantity']),
                    f"PHP {product['total_revenue']:,.2f}"
                ])
            
            products_table = Table(products_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            products_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), light_bg),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(products_table)
            elements.append(Spacer(1, 20))
        
        if orders:
            elements.append(Paragraph(f"Order Details ({len(orders)} orders)", heading_style))
            
            orders_data = [['Order ID', 'Date', 'Customer', 'Status', 'Amount']]
            for order in orders[:50]:
                orders_data.append([
                    f"#{order['order_id']}",
                    order['order_date'].strftime('%Y-%m-%d'),
                    order['customer_name'] or 'Guest',
                    order['status'],
                    f"PHP {order['total_amount']:,.2f}"
                ])
            
            orders_table = Table(orders_data, colWidths=[0.8*inch, 1.2*inch, 1.8*inch, 1.2*inch, 1*inch])
            orders_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), light_bg),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(orders_table)
            
            if len(orders) > 50:
                elements.append(Spacer(1, 10))
                elements.append(Paragraph(f"Note: Showing first 50 of {len(orders)} orders", styles['Italic']))
        
        doc.build(elements)
        
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=sales_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response