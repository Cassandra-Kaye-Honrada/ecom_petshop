# # Routes/cart.py
# from flask import render_template, request, redirect, url_for, session, jsonify
# import MySQLdb.cursors
# from datetime import datetime
# from typing import Any

# def register_cart(app: Any, mysql: Any) -> None:
#     """Register cart-related routes"""
    
#     @app.route('/plantify/cart')
#     def cart():
#         """Display shopping cart"""
#         if 'is_loggedin' not in session or not session['is_loggedin']:
#             # Guest cart - use session ID
#             session_id = session.get('session_id')
#             if not session_id:
#                 # Create new session ID for guest
#                 import uuid
#                 session_id = str(uuid.uuid4())
#                 session['session_id'] = session_id
            
#             with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                 cursor.execute("""
#                     SELECT gc.session_id, gc.product_id, gc.quantity,
#                            p.name AS product_name, p.price, p.img_path AS image
#                     FROM guest_cart gc
#                     JOIN products p ON gc.product_id = p.product_id
#                     WHERE gc.session_id = %s
#                     ORDER BY gc.created_at DESC
#                 """, (session_id,))
#                 cart_items = cursor.fetchall()
            
#             return render_template(
#                 'customer/cart.html',
#                 title="Shopping Cart",
#                 cart_items=cart_items,
#                 is_guest=True,
#                 is_loggedin=False
#             )
#         else:
#             # User cart
#             user_id = session.get('user_id')
            
#             with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                 cursor.execute("""
#                     SELECT c.cart_id, c.product_id, c.quantity,
#                            p.name AS product_name, p.price, p.img_path AS image
#                     FROM cart c
#                     JOIN products p ON c.product_id = p.product_id
#                     WHERE c.user_id = %s
#                     ORDER BY c.created_at DESC
#                 """, (user_id,))
#                 cart_items = cursor.fetchall()
            
#             return render_template(
#                 'customer/cart.html',
#                 title="Shopping Cart",
#                 cart_items=cart_items,
#                 is_guest=False,
#                 is_loggedin=True
#             )
    
#     @app.route('/plantify/cart/add', methods=['POST'])
#     def add_to_cart():
#         """Add product to cart (AJAX)"""
#         try:
#             product_id = request.form.get('product_id', type=int)
#             quantity = request.form.get('quantity', 1, type=int)
            
#             # Validation
#             if not product_id or quantity < 1:
#                 return jsonify({'success': False, 'error': 'Invalid product or quantity'}), 400
            
#             # Check if product exists and is visible
#             with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                 cursor.execute("""
#                     SELECT p.product_id, p.name, i.quantity AS stock
#                     FROM products p
#                     JOIN inventories i ON p.product_id = i.product_id
#                     WHERE p.product_id = %s AND p.visible = 1
#                 """, (product_id,))
#                 product = cursor.fetchone()
            
#             if not product:
#                 return jsonify({'success': False, 'error': 'Product not found'}), 404
            
#             if product['stock'] < quantity:
#                 return jsonify({
#                     'success': False, 
#                     'error': f'Only {product["stock"]} items available'
#                 }), 400
            
#             # Add to appropriate cart
#             if 'is_loggedin' in session and session['is_loggedin']:
#                 # User cart
#                 user_id = session.get('user_id')
#                 with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                     cursor.execute("""
#                         INSERT INTO cart (user_id, product_id, quantity, created_at)
#                         VALUES (%s, %s, %s, %s)
#                         ON DUPLICATE KEY UPDATE quantity = quantity + %s
#                     """, (user_id, product_id, quantity, datetime.now(), quantity))
#                     mysql.connection.commit()
#             else:
#                 # Guest cart
#                 session_id = session.get('session_id')
#                 if not session_id:
#                     import uuid
#                     session_id = str(uuid.uuid4())
#                     session['session_id'] = session_id
                
#                 with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                     cursor.execute("""
#                         INSERT INTO guest_cart (session_id, product_id, quantity, created_at)
#                         VALUES (%s, %s, %s, %s)
#                         ON DUPLICATE KEY UPDATE quantity = quantity + %s
#                     """, (session_id, product_id, quantity, datetime.now(), quantity))
#                     mysql.connection.commit()
            
#             # Get updated cart count
#             cart_count = get_cart_count(mysql, session)
            
#             return jsonify({
#                 'success': True,
#                 'message': f'{product["name"]} added to cart!',
#                 'cart_count': cart_count
#             }), 200
        
#         except Exception as e:
#             print(f"Error adding to cart: {str(e)}")
#             return jsonify({'success': False, 'error': 'An error occurred'}), 500
    
#     @app.route('/plantify/cart/update-quantity', methods=['POST'])
#     def update_quantity():
#         """Update cart item quantity"""
#         try:
#             product_id = request.form.get('product_id', type=int)
#             quantity = request.form.get('quantity', type=int)
            
#             if not product_id or quantity < 0:
#                 return redirect(url_for('cart'))
            
#             if quantity == 0:
#                 # Remove item if quantity is 0
#                 return remove_from_cart_helper(mysql, session, product_id)
            
#             # Update quantity
#             if 'is_loggedin' in session and session['is_loggedin']:
#                 user_id = session.get('user_id')
#                 with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                     cursor.execute("""
#                         UPDATE cart
#                         SET quantity = %s
#                         WHERE user_id = %s AND product_id = %s
#                     """, (quantity, user_id, product_id))
#                     mysql.connection.commit()
#             else:
#                 session_id = session.get('session_id')
#                 with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                     cursor.execute("""
#                         UPDATE guest_cart
#                         SET quantity = %s
#                         WHERE session_id = %s AND product_id = %s
#                     """, (quantity, session_id, product_id))
#                     mysql.connection.commit()
            
#             return redirect(url_for('cart'))
        
#         except Exception as e:
#             print(f"Error updating quantity: {str(e)}")
#             return redirect(url_for('cart'))
    
#     @app.route('/plantify/cart/remove', methods=['POST'])
#     def remove_from_cart():
#         """Remove item from cart"""
#         product_id = request.form.get('product_id', type=int)
#         return remove_from_cart_helper(mysql, session, product_id)
    
#     @app.route('/plantify/cart/count')
#     def get_cart_count_route():
#         """Get cart item count (AJAX)"""
#         count = get_cart_count(mysql, session)
#         return jsonify({'count': count}), 200
    
#     @app.route('/plantify/cart/clear', methods=['POST'])
#     def clear_cart():
#         """Clear entire cart"""
#         try:
#             if 'is_loggedin' in session and session['is_loggedin']:
#                 user_id = session.get('user_id')
#                 with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                     cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
#                     mysql.connection.commit()
#             else:
#                 session_id = session.get('session_id')
#                 if session_id:
#                     with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                         cursor.execute("DELETE FROM guest_cart WHERE session_id = %s", (session_id,))
#                         mysql.connection.commit()
            
#             return redirect(url_for('cart'))
        
#         except Exception as e:
#             print(f"Error clearing cart: {str(e)}")
#             return redirect(url_for('cart'))


# # Helper Functions

# def get_cart_count(mysql, session):
#     """Get total items in cart"""
#     try:
#         if 'is_loggedin' in session and session['is_loggedin']:
#             user_id = session.get('user_id')
#             with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                 cursor.execute("""
#                     SELECT SUM(quantity) as total
#                     FROM cart
#                     WHERE user_id = %s
#                 """, (user_id,))
#                 result = cursor.fetchone()
#                 return result['total'] if result['total'] else 0
#         else:
#             session_id = session.get('session_id')
#             if not session_id:
#                 return 0
            
#             with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                 cursor.execute("""
#                     SELECT SUM(quantity) as total
#                     FROM guest_cart
#                     WHERE session_id = %s
#                 """, (session_id,))
#                 result = cursor.fetchone()
#                 return result['total'] if result['total'] else 0
#     except:
#         return 0


# def remove_from_cart_helper(mysql, session, product_id):
#     """Helper to remove item from cart"""
#     try:
#         if 'is_loggedin' in session and session['is_loggedin']:
#             user_id = session.get('user_id')
#             with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                 cursor.execute("""
#                     DELETE FROM cart
#                     WHERE user_id = %s AND product_id = %s
#                 """, (user_id, product_id))
#                 mysql.connection.commit()
#         else:
#             session_id = session.get('session_id')
#             with mysql.connection.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                 cursor.execute("""
#                     DELETE FROM guest_cart
#                     WHERE session_id = %s AND product_id = %s
#                 """, (session_id, product_id))
#                 mysql.connection.commit()
        
#         return redirect(url_for('cart'))
    
#     except Exception as e:
#         print(f"Error removing from cart: {str(e)}")
#         return redirect(url_for('cart'))