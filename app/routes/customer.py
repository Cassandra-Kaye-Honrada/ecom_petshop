from flask import render_template, request, redirect, url_for, session, jsonify
import MySQLdb.cursors
from datetime import datetime
import uuid
from decimal import Decimal
from flask import flash
import os
import time
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

def register_customer(app, mysql):
    @app.context_processor
    def inject_cart_count():
        return dict(cart_count=_get_cart_count(mysql, session))
    
    @app.route('/')
    @app.route('/plantify/dashboard')
    def customer_dashboard():
        if 'is_loggedin' in session and session['is_loggedin']:
            if 'user_role' in session and session['user_role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
        
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""SELECT 
                p.product_id AS product_id,
                p.name AS name,
                p.description AS description,
                p.price AS price,
                p.img_path AS img_path,
                p.visible AS visibility,
                c.name AS category,
                i.quantity AS quantity
            FROM products p
            JOIN categories c ON p.category = c.category_id
            JOIN inventories i ON p.product_id = i.product_id
            WHERE p.visible = 1 AND c.visible = 1
            LIMIT 6""")
            products = cursor.fetchall()

            cursor.execute("""
                SELECT p.product_id, p.name AS ProductName, p.img_path AS Image, 'New' AS tag
                FROM products p
                JOIN categories c ON p.category = c.category_id
                WHERE p.visible = 1 AND c.visible = 1
                ORDER BY p.created_at DESC
                LIMIT 1
            """)
            new_product = cursor.fetchone()

            cursor.execute("""
                SELECT 
                    p.product_id, 
                    p.name AS ProductName, 
                    p.img_path AS Image, 
                    'Popular' AS tag,
                    COALESCE(SUM(o.quantity), 0) AS sales_count
                FROM products p
                JOIN categories c ON p.category = c.category_id
                JOIN orderitems o ON o.product_id = p.product_id
                WHERE p.visible = 1 AND c.visible = 1
                GROUP BY p.product_id
                ORDER BY sales_count DESC
                LIMIT 1
            """)
            popular_product = cursor.fetchone()

            featured_products = []
            if new_product:
                featured_products.append(new_product)
            if popular_product:
                featured_products.append(popular_product)

            if not featured_products:
                cursor.execute("""
                    SELECT p.product_id, p.name AS ProductName, p.img_path AS Image, 'Default' AS tag
                    FROM products p
                    JOIN categories c ON p.category = c.category_id
                    WHERE p.visible = 1 AND c.visible = 1
                    LIMIT 2
                """)
                featured_products = cursor.fetchall()

        return render_template(
            'customer/dashboard.html', 
            title="Petsup", 
            products=products,
            featured_products=featured_products
        )
    
    @app.route('/plantify/products')
    def products():
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM categories WHERE visible = 1")
            categories = cursor.fetchall()

            cursor.execute("""SELECT 
                p.product_id, p.name, p.description, p.price, p.img_path,
                c.name AS category, i.quantity
            FROM products p
            JOIN categories c ON p.category = c.category_id
            JOIN inventories i ON p.product_id = i.product_id
            WHERE p.visible = 1 AND c.visible = 1
            """)
            products = cursor.fetchall()

        return render_template(
            'customer/products.html',
            title="Our Products",
            products=products,
            categories=categories
        )

    @app.route('/plantify/products/search', endpoint='live_search_products')
    def live_search_products():
        keyword = request.args.get('keyword', '').strip()
        category = request.args.get('category', '').strip()

        query = """SELECT 
            p.product_id AS product_id,
            p.name AS name,
            p.description AS description,
            p.price AS price,
            p.img_path AS img_path,
            p.visible AS visibility,
            c.name AS category,
            i.quantity AS quantity
        FROM products p
        JOIN categories c ON p.category = c.category_id
        JOIN inventories i ON p.product_id = i.product_id
        WHERE p.visible = 1 AND c.visible = 1
        """

        params = []
        if keyword:
            query += " AND p.name LIKE %s"
            params.append(f"%{keyword}%")
        if category:
            query += " AND c.category_id = %s"
            params.append(category)

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute(query, params)
            products = cursor.fetchall()

        return jsonify({'products': products or []})
    
    @app.route('/plantify/product/<int:product_id>')
    def product_details(product_id):
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""SELECT 
                p.product_id, p.name, p.description, p.price, p.img_path,
                c.name AS category, i.quantity
            FROM products p
            JOIN categories c ON p.category = c.category_id
            JOIN inventories i ON p.product_id = i.product_id
            WHERE p.product_id = %s AND p.visible = 1 AND c.visible = 1
            """, (product_id,))
            product = cursor.fetchone()
        
        if not product:
            return "Product not found", 404
        
        success_message = request.args.get('success', None)
        
        return render_template(
            'customer/product_details.html',
            title=product['name'],
            product=product,
            success_message=success_message
        )
    
    @app.route('/plantify/checkout')
    def checkout():
        """Display checkout page"""
        if not session.get('is_loggedin'):
            return redirect(url_for('login', next=request.url))
        
        user_data = session.get('user')
        user_id = user_data.get('user_id') if user_data else None
        
        if not user_id:
            return redirect(url_for('login'))
        
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT ci.cart_item_id, ci.product_id, ci.quantity,
                    p.name AS product_name, p.price, p.img_path AS image,
                    (p.price * ci.quantity) AS subtotal,
                    i.quantity AS stock
                FROM cart c
                JOIN cartitems ci ON c.cart_id = ci.cart_id
                JOIN products p ON ci.product_id = p.product_id
                JOIN categories cat ON p.category = cat.category_id
                JOIN inventories i ON p.product_id = i.product_id
                WHERE c.user_id = %s AND p.visible = 1 AND cat.visible = 1
                ORDER BY c.created_at DESC
            """, (user_id,))
            cart_items = cursor.fetchall()
        
        if not cart_items:
            return redirect(url_for('cart'))
        
        subtotal = sum(item['subtotal'] for item in cart_items)
        shipping = Decimal('50.00') 
        total = subtotal + shipping
        
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT u.*, 
                    p.province_name,
                    m.municipality_name,
                    b.barangay_name
                FROM users u
                JOIN provinces p ON u.province = p.province_id
                JOIN municipalities m ON u.municipality = m.municipality_id
                JOIN barangays b ON u.barangay = b.barangay_id
                WHERE u.user_id = %s
            """, (user_id,))
            user_info = cursor.fetchone()
        
        return render_template(
            'customer/checkout.html',
            title="Checkout",
            cart_items=cart_items,
            user_info=user_info,
            subtotal=subtotal,
            shipping=shipping,
            total=total
        )
    
    @app.route('/plantify/checkout/process', methods=['POST'])
    def process_checkout():
        """Process checkout and create order"""
        if not session.get('is_loggedin'):
            return jsonify({'success': False, 'error': 'Please login to continue'}), 401
        
        user_data = session.get('user')
        user_id = user_data.get('user_id') if user_data else None
        
        if not user_id:
            return jsonify({'success': False, 'error': 'Invalid session'}), 401
        
        try:
            payment_method = request.form.get('payment_method')
            addr = request.form.get('delivery_address', '').strip()
            receipt = request.files.get('payment_proof')
            
            if payment_method == 'OL' and not receipt:
                return jsonify({'success': False, 'error': 'Online payment selected but no proof of payment uploaded'}), 400
            
            if not addr:
                return jsonify({'success': False, 'error': 'Delivery address is required'}), 400
            
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT ci.product_id, ci.quantity, p.price, i.quantity AS stock
                    FROM cart c
                    JOIN cartitems ci ON c.cart_id = ci.cart_id
                    JOIN products p ON ci.product_id = p.product_id
                    JOIN categories cat ON p.category = cat.category_id
                    JOIN inventories i ON p.product_id = i.product_id
                    WHERE c.user_id = %s AND p.visible = 1 AND cat.visible = 1
                """, (user_id,))
                cart_items = cursor.fetchall()
                
                if not cart_items:
                    return jsonify({'success': False, 'error': 'Cart is empty'}), 400
                
                for item in cart_items:
                    if item['stock'] < item['quantity']:
                        return jsonify({
                            'success': False, 
                            'error': f'Insufficient stock for product ID {item["product_id"]}'
                        }), 400
                
                subtotal = Decimal('0.00')
                for item in cart_items:
                    subtotal += Decimal(str(item['price'])) * item['quantity']
                
                shipping = Decimal('50.00')
                total_amount = subtotal + shipping

                cursor.execute("""
                    SELECT barangay_name as barangay FROM `barangays` WHERE barangay_id = %s
                """, (session['user']['barangay'], ))
                brgy = cursor.fetchone()

                cursor.execute("""
                    SELECT municipality_name as municipality FROM `municipalities` WHERE municipality_id = %s
                """, (session['user']['municipality'], ))
                muni = cursor.fetchone()

                cursor.execute("""
                    SELECT province_name as province FROM `provinces` WHERE province_id = %s
                """, (session['user']['province'], ))
                prov = cursor.fetchone()

                delivery_addr = f"{addr}, {brgy['barangay']}, {muni['municipality']}, {prov['province']}"
                
                cursor.execute("""
                    INSERT INTO orders (user_id, order_date, status, total_amount, delivery_address)
                    VALUES (%s, %s, %s, %s, %s)
                """, (user_id, datetime.now(), 'Pending', total_amount, delivery_addr))
                order_id = cursor.lastrowid
                
                for item in cart_items:
                    item_subtotal = Decimal(str(item['price'])) * item['quantity']
                    
                    cursor.execute("""
                        INSERT INTO orderitems (order_id, product_id, quantity, price_at_purchase, sub_total)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (order_id, item['product_id'], item['quantity'], 
                        item['price'], item_subtotal))
                    
                    cursor.execute("""
                        UPDATE inventories 
                        SET quantity = quantity - %s 
                        WHERE product_id = %s
                    """, (item['quantity'], item['product_id']))
                
                payment_path = None
                if payment_method == 'OL' and receipt:
                    filename = f"{int(time.time())}_{secure_filename(receipt.filename)}"
                    save_path = f"/uploads/payments/{filename}"
                    image_path = os.path.join(app.config['UPLOAD_PAYMENT'], filename)
                    receipt.save(image_path)
                    payment_path = save_path
                
                payment_status = 'Unpaid' if payment_method == 'COD' else 'Paid'

                cursor.execute("""
                    INSERT INTO payments (order_id, method, status, payment_proof)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, payment_method, payment_status, payment_path))
                
                cursor.execute("""
                    INSERT INTO order_status_history (order_id, status, changed_at)
                    VALUES (%s, %s, %s)
                """, (order_id, 'Pending', datetime.now()))
                
                cursor.execute("""
                    DELETE ci FROM cartitems ci
                    JOIN cart c ON ci.cart_id = c.cart_id
                    WHERE c.user_id = %s
                """, (user_id,))
                cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
                
                mysql.connection.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Order placed successfully!',
                'order_id': order_id
            }), 200
        
        except Exception as e:
            mysql.connection.rollback()
            print(f"Error processing checkout: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': 'An error occurred while processing your order'}), 500

    @app.route('/plantify/cart/add', methods=['POST'])
    def add_to_cart():
        """Add product to cart"""
        try:
            product_id = request.form.get('product_id', type=int)
            quantity = request.form.get('quantity', 1, type=int)
            
            if not product_id or quantity < 1:
                return jsonify({'success': False, 'error': 'Invalid product or quantity'}), 400
            
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT p.product_id, p.name, i.quantity AS stock
                    FROM products p
                    JOIN categories c ON p.category = c.category_id
                    JOIN inventories i ON p.product_id = i.product_id
                    WHERE p.product_id = %s AND p.visible = 1 AND c.visible = 1
                """, (product_id,))
                product = cursor.fetchone()
            
            if not product:
                return jsonify({'success': False, 'error': 'Product not found or unavailable'}), 404
            
            if product['stock'] < quantity:
                return jsonify({
                    'success': False, 
                    'error': f'Only {product["stock"]} items available'
                }), 400
            
            if session.get('is_loggedin') == True:
                user_data = session.get('user')
                user_id = user_data.get('user_id') if user_data else None
                
                if not user_id:
                    print("ERROR: User marked as logged in but no user_id in session!")
                    session.clear()
                    return jsonify({'success': False, 'error': 'Session error. Please log in again.'}), 401
                
                with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                    cursor.execute("SELECT cart_id FROM cart WHERE user_id = %s", (user_id,))
                    cart = cursor.fetchone()
                    
                    if not cart:
                        cursor.execute("INSERT INTO cart (user_id, created_at) VALUES (%s, %s)", 
                                     (user_id, datetime.now()))
                        mysql.connection.commit()
                        cart_id = cursor.lastrowid
                    else:
                        cart_id = cart['cart_id']
                    
                    cursor.execute("""
                        SELECT cart_item_id, quantity 
                        FROM cartitems 
                        WHERE cart_id = %s AND product_id = %s
                    """, (cart_id, product_id))
                    existing_item = cursor.fetchone()
                    
                    if existing_item:
                        new_quantity = existing_item['quantity'] + quantity
                        cursor.execute("""
                            UPDATE cartitems 
                            SET quantity = %s 
                            WHERE cart_item_id = %s
                        """, (new_quantity, existing_item['cart_item_id']))
                    else:
                        cursor.execute("""
                            INSERT INTO cartitems (cart_id, product_id, quantity)
                            VALUES (%s, %s, %s)
                        """, (cart_id, product_id, quantity))
                    
                    mysql.connection.commit()
            else:
                if 'session_id' not in session:
                    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                        cursor.execute("DELETE FROM guestcart")
                        mysql.connection.commit()

                    session['session_id'] = str(uuid.uuid4())
                    session.modified = True
                
                session_id = session.get('session_id')
                
                with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                    cursor.execute("""
                        SELECT quantity 
                        FROM guestcart 
                        WHERE session_id = %s AND product_id = %s
                    """, (session_id, product_id))
                    existing_item = cursor.fetchone()
                    
                    if existing_item:
                        new_quantity = existing_item['quantity'] + quantity
                        cursor.execute("""
                            UPDATE guestcart 
                            SET quantity = %s 
                            WHERE session_id = %s AND product_id = %s
                        """, (new_quantity, session_id, product_id))
                    else:
                        cursor.execute("""
                            INSERT INTO guestcart (session_id, product_id, quantity, created_at)
                            VALUES (%s, %s, %s, %s)
                        """, (session_id, product_id, quantity, datetime.now()))
                    
                    mysql.connection.commit()
            
            cart_count = _get_cart_count(mysql, session)
            
            return jsonify({
                'success': True,
                'message': f'{product["name"]} added to cart!',
                'cart_count': cart_count
            }), 200
        
        except Exception as e:
            print(f"Error adding to cart: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': 'An error occurred while adding to cart'}), 500
    
    @app.route('/plantify/cart')
    def cart():
        session.pop('checkout_auth', None)

        """Display shopping cart"""
        if session.get('is_loggedin') == True:
            user_data = session.get('user')
            user_id = user_data.get('user_id') if user_data else None
            
            if user_id:
                with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                    cursor.execute("""
                        SELECT ci.cart_item_id, ci.product_id, ci.quantity,
                               p.name AS product_name, p.price, p.img_path AS image,
                               (p.price * ci.quantity) AS total
                        FROM cart c
                        JOIN cartitems ci ON c.cart_id = ci.cart_id
                        JOIN products p ON ci.product_id = p.product_id
                        JOIN categories cat ON p.category = cat.category_id
                        WHERE c.user_id = %s AND p.visible = 1 AND cat.visible = 1
                        ORDER BY c.created_at DESC
                    """, (user_id,))
                    cart_items = cursor.fetchall()
                
                return render_template(
                    'customer/cart.html',
                    title="Shopping Cart",
                    cart_items=cart_items,
                    is_guest=False,
                    is_loggedin=True
                )
        
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
        
        session_id = session.get('session_id')
        
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT gc.product_id, gc.quantity,
                       p.name AS product_name, p.price, p.img_path AS image,
                       (p.price * gc.quantity) AS total
                FROM guestcart gc
                JOIN products p ON gc.product_id = p.product_id
                JOIN categories cat ON p.category = cat.category_id
                WHERE gc.session_id = %s AND p.visible = 1 AND cat.visible = 1
                ORDER BY gc.created_at DESC
            """, (session_id,))
            cart_items = cursor.fetchall()
        
        return render_template(
            'customer/cart.html',
            title="Shopping Cart",
            cart_items=cart_items,
            is_guest=True,
            is_loggedin=False
        )
    
    @app.route('/plantify/cart/checkout/auth')
    def checkout_auth():
        session['checkout_auth'] = True
        return redirect(url_for('login'))

    @app.route('/plantify/cart/update-quantity', methods=['POST'])
    def update_quantity():
        """Update cart item quantity"""
        try:
            product_id = request.form.get('product_id', type=int)
            quantity = request.form.get('quantity', type=int)
            
            if not product_id or quantity < 0:
                flash('Invalid product or quantity', 'danger')
                return redirect(url_for('cart'))
            
            if quantity == 0:
                return _remove_from_cart_helper(mysql, session, product_id)
            
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT i.quantity AS stock, p.name 
                    FROM inventories i 
                    JOIN products p ON i.product_id = p.product_id
                    WHERE p.product_id = %s
                """, (product_id,))
                product = cursor.fetchone()
                
                if not product:
                    flash('Product not found', 'danger')
                    return redirect(url_for('cart'))
                
                if quantity > product['stock']:
                    flash(f'Only {product["stock"]} item(s) of {product["name"]} available in stock', 'danger')
                    return redirect(url_for('cart'))
            
            if session.get('is_loggedin') == True:
                user_data = session.get('user')
                user_id = user_data.get('user_id') if user_data else None
                
                if user_id:
                    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                        cursor.execute("""
                            UPDATE cartitems ci
                            JOIN cart c ON ci.cart_id = c.cart_id
                            SET ci.quantity = %s
                            WHERE c.user_id = %s AND ci.product_id = %s
                        """, (quantity, user_id, product_id))
                        mysql.connection.commit()
            else:
                session_id = session.get('session_id')
                if session_id:
                    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                        cursor.execute("""
                            UPDATE guestcart
                            SET quantity = %s
                            WHERE session_id = %s AND product_id = %s
                        """, (quantity, session_id, product_id))
                        mysql.connection.commit()
            
            flash('Cart updated successfully', 'success')
            return redirect(url_for('cart'))
            
        except Exception as e:
            print(f"Error updating quantity: {str(e)}")
            flash('An error occurred while updating the cart', 'danger')
            return redirect(url_for('cart'))

    @app.route('/plantify/cart/remove', methods=['POST'])
    def remove_from_cart():
        """Remove item from cart"""
        product_id = request.form.get('product_id', type=int)
        return _remove_from_cart_helper(mysql, session, product_id)

    @app.route('/plantify/cart/count')
    def get_cart_count_route():
        """Get cart item count (AJAX)"""
        count = _get_cart_count(mysql, session)
        return jsonify({'count': count}), 200

    @app.route('/plantify/cart/clear', methods=['POST'])
    def clear_cart():
        """Clear entire cart"""
        try:
            if session.get('is_loggedin') == True:
                user_data = session.get('user')
                user_id = user_data.get('user_id') if user_data else None
                
                if user_id:
                    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                        cursor.execute("""
                            DELETE ci FROM cartitems ci
                            JOIN cart c ON ci.cart_id = c.cart_id
                            WHERE c.user_id = %s
                        """, (user_id,))
                        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
                        mysql.connection.commit()
            else:
                session_id = session.get('session_id')
                if session_id:
                    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                        cursor.execute("DELETE FROM guestcart WHERE session_id = %s", (session_id,))
                        mysql.connection.commit()
            
            return redirect(url_for('cart'))
        
        except Exception as e:
            print(f"Error clearing cart: {str(e)}")
            return redirect(url_for('cart'))

    @app.route('/plantify/about')
    def about():
        return render_template('customer/about.html', title="About Us")
    
    @app.route('/plantify/contact', methods=['GET', 'POST'])
    def contact():
        if request.method == 'GET':
            return render_template('customer/contact.html', title="Contact Us")
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()
            
            if not all([name, email, subject, message]):
                return jsonify({'error': 'All fields are required'}), 400
            
            if "@" not in email:
                return jsonify({'error': 'Invalid email format'}), 400
            
            if len(message) < 10:
                return jsonify({'error': 'Message must be at least 10 characters'}), 400
            
            try:
                with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                    cursor.execute("""
                        INSERT INTO contact_messages 
                        (name, email, subject, message, created_at, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (name, email, subject, message, datetime.now(), 'new'))
                    
                    mysql.connection.commit()
                
                return jsonify({
                    'success': True, 
                    'message': 'Thank you for contacting us! We will get back to you soon.'
                }), 200
            
            except Exception as e:
                print(f"Error: {str(e)}")
                return jsonify({'error': 'An error occurred. Please try again later.'}), 500
    
    @app.route('/plantify/profile')
    def profile():
        """Display user profile"""
        if not session.get('is_loggedin'):
            return redirect(url_for('login'))
        
        user_data = session.get('user')
        user_id = user_data.get('user_id') if user_data else None
        
        if not user_id:
            return redirect(url_for('login'))
        
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT u.*, 
                    p.province_name,
                    m.municipality_name,
                    b.barangay_name
                FROM users u
                LEFT JOIN provinces p ON u.province = p.province_id
                LEFT JOIN municipalities m ON u.municipality = m.municipality_id
                LEFT JOIN barangays b ON u.barangay = b.barangay_id
                WHERE u.user_id = %s
            """, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return redirect(url_for('login'))
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) as completed_orders,
                    COALESCE(SUM(total_amount), 0) as total_spent
                FROM orders
                WHERE user_id = %s
            """, (user_id,))
            stats = cursor.fetchone()
        
        return render_template(
            'customer/profile.html',
            title="My Profile",
            user=user,
            stats=stats
        )

    @app.route('/plantify/profile/edit', methods=['GET', 'POST'])
    def edit_profile():
        """Edit user profile"""
        if not session.get('is_loggedin'):
            return redirect(url_for('login'))
        
        user_data = session.get('user')
        user_id = user_data.get('user_id') if user_data else None
        
        if not user_id:
            return redirect(url_for('login'))
        
        if request.method == 'GET':
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
                
                cursor.execute("SELECT * FROM provinces ORDER BY province_name")
                provinces = cursor.fetchall()
                
                municipalities = []
                if user.get('province'):
                    cursor.execute(
                        "SELECT * FROM municipalities WHERE province_id = %s ORDER BY municipality_name",
                        (user['province'],)
                    )
                    municipalities = cursor.fetchall()
                
                barangays = []
                if user.get('municipality'):
                    cursor.execute(
                        "SELECT * FROM barangays WHERE municipality_id = %s ORDER BY barangay_name",
                        (user['municipality'],)
                    )
                    barangays = cursor.fetchall()
            
            return render_template(
                'customer/edit_profile.html',
                title="Edit Profile",
                user=user,
                provinces=provinces,
                municipalities=municipalities,
                barangays=barangays
            )
        
        try:
            firstname = request.form.get('firstname', '').strip()
            middlename = request.form.get('middlename', '').strip()
            lastname = request.form.get('lastname', '').strip()
            phone = request.form.get('phone', '').strip()
            province_raw = request.form.get('province', '').strip()
            municipality_raw = request.form.get('municipality', '').strip()
            barangay_raw = request.form.get('barangay', '').strip()
            
            if not all([firstname, lastname, phone]):
                flash('First name, last name, and phone are required', 'danger')
                return redirect(url_for('edit_profile'))
            
            if not province_raw.isdigit() or not municipality_raw.isdigit() or not barangay_raw.isdigit():
                flash('Invalid location selection', 'danger')
                return redirect(url_for('edit_profile'))
            
            province = int(province_raw)
            municipality = int(municipality_raw)
            barangay = int(barangay_raw)
            
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute("""
                    UPDATE users 
                    SET firstname = %s, middlename = %s, lastname = %s,
                        phone = %s, province = %s, municipality = %s, barangay = %s
                    WHERE user_id = %s
                """, (firstname, middlename, lastname, phone,
                    province, municipality, barangay, user_id))
                mysql.connection.commit()
                
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                updated_user = cursor.fetchone()
                session['user'] = updated_user
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            flash('An error occurred while updating your profile', 'danger')
            return redirect(url_for('edit_profile'))

    @app.route('/plantify/profile/change-password', methods=['GET', 'POST'])
    def change_password():
        """Change user password"""
        if not session.get('is_loggedin'):
            return redirect(url_for('login'))
        
        user_data = session.get('user')
        user_id = user_data.get('user_id') if user_data else None
        
        if not user_id:
            return redirect(url_for('login'))
        
        if request.method == 'GET':
            return render_template('customer/change_password.html', title="Change Password")
        
        try:
            current_password = request.form.get('current_password', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if not all([current_password, new_password, confirm_password]):
                flash('All fields are required', 'danger')
                return redirect(url_for('change_password'))
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'danger')
                return redirect(url_for('change_password'))
            
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long', 'danger')
                return redirect(url_for('change_password'))
            
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
                user = cursor.fetchone()
                
                if not user or not check_password_hash(user['password'], current_password):
                    flash('Current password is incorrect', 'danger')
                    return redirect(url_for('change_password'))
                
                cursor.execute(
                    "UPDATE users SET password = %s WHERE user_id = %s",
                    (generate_password_hash(new_password), user_id)
                )
                mysql.connection.commit()
            
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))
        
        except Exception as e:
            print(f"Error changing password: {str(e)}")
            flash('An error occurred while changing your password', 'danger')
            return redirect(url_for('change_password'))

    @app.route('/api/municipalities/<int:province_id>', endpoint='customer_get_municipalities')
    def get_municipalities_customer(province_id):
        """Get municipalities for a given province"""
        try:
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT municipality_id, municipality_name 
                    FROM municipalities 
                    WHERE province_id = %s 
                    ORDER BY municipality_name
                """, (province_id,))
                municipalities = cursor.fetchall()
            
            return jsonify(municipalities), 200
        except Exception as e:
            print(f"Error fetching municipalities: {str(e)}")
            return jsonify([]), 500

    @app.route('/api/barangays/<int:municipality_id>', endpoint='customer_get_barangays')
    def get_barangays_customer(municipality_id):
        """Get barangays for a given municipality"""
        try:
            with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                cursor.execute("""
                    SELECT barangay_id, barangay_name 
                    FROM barangays 
                    WHERE municipality_id = %s 
                    ORDER BY barangay_name
                """, (municipality_id,))
                barangays = cursor.fetchall()
            
            return jsonify(barangays), 200
        except Exception as e:
            print(f"Error fetching barangays: {str(e)}")
            return jsonify([]), 500

   
    @app.route('/plantify/settings')
    def settings():
        return "setting"
    @app.route('/plantify/orders')
    def orders():
        """Display user orders"""
        if not session.get('is_loggedin'):
            return redirect(url_for('login'))
        
        user_data = session.get('user')
        user_id = user_data.get('user_id') if user_data else None
        
        if not user_id:
            return redirect(url_for('login'))
        
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT o.order_id, o.order_date, o.status, o.total_amount, 
                    o.delivery_address, o.tracking_number,
                    COUNT(oi.order_item_id) as item_count
                FROM orders o
                LEFT JOIN orderitems oi ON o.order_id = oi.order_id
                WHERE o.user_id = %s
                GROUP BY o.order_id
                ORDER BY o.order_date DESC
            """, (user_id,))
            orders = cursor.fetchall()
        
        return render_template(
            'customer/orders.html',
            title="My Orders",
            orders=orders
        )



    @app.route('/plantify/orders/<int:order_id>')
    def order_details(order_id):
        if not session.get('is_loggedin'):
            return redirect(url_for('login'))
        
        user_data = session.get('user')
        user_id = user_data.get('user_id') if user_data else None
        
        if not user_id:
            return redirect(url_for('login'))
        
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT o.order_id, o.order_date, o.status, o.total_amount, 
                    o.delivery_address, o.tracking_number, o.decline_reason
                FROM orders o
                WHERE o.order_id = %s AND o.user_id = %s
            """, (order_id, user_id))
            order = cursor.fetchone()
            
            if not order:
                return "Order not found", 404
            
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
                SELECT payment_id, method, status, payment_proof
                FROM payments
                WHERE order_id = %s
            """, (order_id,))
            payment = cursor.fetchone()
        
        return render_template(
            'customer/order_details.html',
            title=f"Order #{order_id}",
            order=order,
            order_items=order_items,
            payment=payment
        )


def _get_cart_count(mysql, session):
    """Get total items in cart"""
    try:
        if session.get('is_loggedin') == True:
            user_data = session.get('user')
            user_id = user_data.get('user_id') if user_data else None
            
            if user_id:
                with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                    cursor.execute("""
                        SELECT SUM(ci.quantity) as total
                        FROM cart c
                        JOIN cartitems ci ON c.cart_id = ci.cart_id
                        WHERE c.user_id = %s
                    """, (user_id,))
                    result = cursor.fetchone()
                    return result['total'] if result['total'] else 0
        
        session_id = session.get('session_id')
        if not session_id:
            return 0
        
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT SUM(quantity) as total
                FROM guestcart
                WHERE session_id = %s
            """, (session_id,))
            result = cursor.fetchone()
            return result['total'] if result['total'] else 0
    except Exception as e:
        print(f"Error getting cart count: {str(e)}")
        return 0


def _remove_from_cart_helper(mysql, session, product_id):
    """Helper to remove item from cart"""
    try:
        if session.get('is_loggedin') == True:
            user_data = session.get('user')
            user_id = user_data.get('user_id') if user_data else None
            
            if user_id:
                with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                    cursor.execute("""
                        DELETE ci FROM cartitems ci
                        JOIN cart c ON ci.cart_id = c.cart_id
                        WHERE c.user_id = %s AND ci.product_id = %s
                    """, (user_id, product_id))
                    mysql.connection.commit()
        else:
            session_id = session.get('session_id')
            if session_id:
                with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                    cursor.execute("""
                        DELETE FROM guestcart
                        WHERE session_id = %s AND product_id = %s
                    """, (session_id, product_id))
                    mysql.connection.commit()
        
        return redirect(url_for('cart'))
    
    except Exception as e:
        print(f"Error removing from cart: {str(e)}")
        return redirect(url_for('cart'))
    
