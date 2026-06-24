from flask import render_template, request, redirect, url_for, jsonify, flash, session
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

def register_auth(app, mysql):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        errors = {}

        if 'is_loggedin' in session and session['is_loggedin']:
            print(session['is_loggedin'])
            if 'user_role' in session and session['user_role'] == 'admin':
                print(session['user_role'])
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        print('not logged in')

        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']

            if not email:
                errors['email'] = 'Email is required.'
            if not password:
                errors['password'] = 'Password is required.'

            if not errors:
                if email == 'admin@gmail.com':
                    if password == 'password123':
                        session['is_loggedin'] = True
                        session['user_role'] = 'admin'
                        flash('Welcome back, Admin', 'success')
                        return redirect(url_for('admin_dashboard'))
                    else:
                        errors['password'] = 'Incorrect password.'
                else:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('SELECT * from users wHERE email = %s', (email,))
                    user = cursor.fetchone()

                    if not user:
                        errors['email'] = 'Email not found.'
                    else:
                        if user['status'] == 0:
                            flash('Your account is disabled. Please contact the administrator.', 'warning')
                            errors['account'] = 'Your account is disabled. Please contact the administrator.'
                        elif check_password_hash(user['password'], password):
                            session['is_loggedin'] = True
                            session['user_role'] = 'customer'
                            user.pop('password', None)
                            session['user'] = user
                            print(f'User: {user}')

                            # --- TRANSFER GUEST CART TO USER CART ---
                            if 'session_id' in session:
                                guest_session_id = session['session_id']
                                user_id = user['user_id']

                                print(f"Transferring guest cart (session_id={guest_session_id}) to user cart for user_id={user_id}")

                                with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                                    # Check if there are guest cart items for this session_id
                                    cursor.execute("""
                                        SELECT product_id, quantity
                                        FROM guestcart
                                        WHERE session_id = %s
                                    """, (guest_session_id,))
                                    guest_items = cursor.fetchall()

                                    if guest_items:
                                        # Get or create user cart
                                        cursor.execute("SELECT cart_id FROM cart WHERE user_id = %s", (user_id,))
                                        user_cart = cursor.fetchone()

                                        if not user_cart:
                                            cursor.execute(
                                                "INSERT INTO cart (user_id, created_at) VALUES (%s, %s)",
                                                (user_id, datetime.now())
                                            )
                                            mysql.connection.commit()
                                            cart_id = cursor.lastrowid
                                        else:
                                            cart_id = user_cart['cart_id']

                                        # Transfer each guest cart item to the user's cart
                                        for item in guest_items:
                                            product_id = item['product_id']
                                            quantity = item['quantity']

                                            # If the item already exists in the user cart, update it
                                            cursor.execute("""
                                                SELECT cart_item_id, quantity FROM cartitems
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

                                        # Clear transferred guest cart
                                        cursor.execute("DELETE FROM guestcart WHERE session_id = %s", (guest_session_id,))
                                        mysql.connection.commit()

                                        print(f"Guest cart items transferred and cleared for session_id={guest_session_id}")

                            flash(f'Welcome back, {user['firstname']} {user['lastname']}', 'success')

                            if session.get('checkout_auth', False):
                                return redirect(url_for('cart'))
                            return redirect(url_for('customer_dashboard'))
                        else:
                            errors['password'] = 'Incorrect password.'

        return render_template('auth/login.html', errors=errors)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        errors = {}
        province = ''
        municipality = ''
        municipalities = []
        barangays = []

        if 'is_loggedin' in session and session['is_loggedin']:
            if 'user_role' in session and session['user_role'] == 'admin':
                print(session['user_role'])
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))

        if request.method == 'POST':
            first_name = request.form['first_name'].strip() 
            middle_name = request.form['middle_name'].strip()
            last_name = request.form['last_name'].strip()
            email = request.form['email'].strip()
            phone = request.form['phone'].strip()
            province = request.form['province'].strip()
            municipality = request.form['municipality'].strip()
            barangay = request.form['barangay'].strip()
            password = request.form['password'].strip()
            confirm_password = request.form['confirm_password'].strip()

            print(type(province))

            if not first_name:
                errors['first_name'] = "First name is required."

            if not middle_name:
                errors['middle_name'] = "Middle name is required."

            if not last_name:
                errors['last_name'] = "Last name is required."

            if not email:
                errors['email'] = "Email is required."
            elif "@" not in email:
                errors['email'] = "Invalid email format."
            else:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT email FROM users WHERE email = %s', (email,))
                account = cursor.fetchone()
                cursor.close()

                if account:
                    errors['email'] = "Email already in use."

            if not phone:
                errors['phone'] = "Phone number is required"
            elif not phone.isdigit():
                errors['phone'] = "Phone number must contain only digits"
            elif not len(phone) == 11: 
                errors['phone'] = "Phone number must be 11 digits"
            elif not phone.startswith("09"):
                errors['phone'] = "Phone number must start with 09"

            if not province:
                errors['province'] = "Province is required."

            if not municipality:
                errors['municipality'] = "Municipality is required."



            if not barangay:
                errors['barangay'] = "Barangay is required."

            if not password:
                errors['password'] = "Password is required."
            elif len(password) < 8:
                errors['password'] = "Password must be at least 8 characters."

            if not confirm_password:
                errors['confirm_password'] = "Please confirm your password."
            elif password != confirm_password:
                errors['confirm_password'] = "Passwords do not match."

            if not errors:
                with mysql.connection.cursor() as cursor:
                    cursor.execute("INSERT INTO users (firstname, middlename, lastname, email, phone, province, municipality, barangay, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", (first_name.title(), middle_name.title(), last_name.title(), email, phone, int(province), int(municipality), int(barangay), generate_password_hash(password)))

                    mysql.connection.commit()
                    inserted_id = cursor.lastrowid
                
                with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                    cursor.execute("SELECT * FROM users WHERE user_id = %s", (inserted_id,))

                    user = cursor.fetchone()

                session['is_loggedin'] = True
                session['user_role'] = 'customer'
                session['user'] = user
                print(f"User: {user}")

                # --- TRANSFER GUEST CART TO USER CART ---
                if 'session_id' in session:
                    guest_session_id = session['session_id']
                    user_id = session['user']['user_id']

                    print(f"Transferring guest cart (session_id={guest_session_id}) to user cart for user_id={user_id}")

                    with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
                        # Check if there are guest cart items for this session_id
                        cursor.execute("""
                            SELECT product_id, quantity
                            FROM guestcart
                            WHERE session_id = %s
                        """, (guest_session_id,))
                        guest_items = cursor.fetchall()

                        if guest_items:
                            # Get or create user cart
                            cursor.execute("SELECT cart_id FROM cart WHERE user_id = %s", (user_id,))
                            user_cart = cursor.fetchone()

                            if not user_cart:
                                cursor.execute(
                                    "INSERT INTO cart (user_id, created_at) VALUES (%s, %s)",
                                    (user_id, datetime.now())
                                )
                                mysql.connection.commit()
                                cart_id = cursor.lastrowid
                            else:
                                cart_id = user_cart['cart_id']

                            # Transfer each guest cart item to the user's cart
                            for item in guest_items:
                                product_id = item['product_id']
                                quantity = item['quantity']

                                # If the item already exists in the user cart, update it
                                cursor.execute("""
                                    SELECT cart_item_id, quantity FROM cartitems
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

                            # Clear transferred guest cart
                            cursor.execute("DELETE FROM guestcart WHERE session_id = %s", (guest_session_id,))
                            mysql.connection.commit()

                            print(f"Guest cart items transferred and cleared for session_id={guest_session_id}")

                flash(f"Welcome, {first_name.title()} {last_name.title()}! Your account has been created successfully.", 'success')
                if session.get('checkout_auth', False):
                    return redirect(url_for('cart'))

                return redirect(url_for('customer_dashboard'))
                
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM provinces')
        provinces = cursor.fetchall()
        cursor.close()
        

        if province:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT municipality_id, municipality_name FROM municipalities WHERE province_id = %s', (province,))
            municipalities = cursor.fetchall()
            print(municipalities)
            cursor.close()

        if municipality:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT barangay_id, barangay_name FROM barangays WHERE municipality_id = %s', (municipality,))
            barangays = cursor.fetchall()
            print(barangays)
            cursor.close()
        
        return render_template('auth/register.html', provinces=provinces, municipalities=municipalities, barangays=barangays, errors=errors)
    
    @app.route('/get_municipalities/', methods=['GET'])
    def get_municipalities():
        id = request.args["province_id"]

        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute('SELECT municipality_id, municipality_name FROM municipalities WHERE province_id = %s', (id,))
            municipalities = cursor.fetchall()

        return jsonify(municipalities)
    
    @app.route('/get_barangays/', methods=['GET'])
    def get_barangays():
        id = request.args["municipality_id"]
        with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute('SELECT barangay_id, barangay_name FROM barangays WHERE municipality_id = %s', (id,))
            barangays = cursor.fetchall()

        return jsonify(barangays)


    @app.route('/logout')
    def logout():
        session.clear()
        flash("You have been logged out successfully.", "info")
        return redirect(url_for('customer_dashboard'))