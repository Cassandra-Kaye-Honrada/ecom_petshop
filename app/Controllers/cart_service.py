from Models.Cart import CartItem, GuestCartItem
from DataAccess.database import DatabaseHelper
from typing import List

class CartService:
    def __init__(self, db: DatabaseHelper):
        self.db = db
    
    def get_or_create_session_id(self, session_data: dict) -> str:
        """Ensure session is always created consistently"""
        session_id = session_data.get('session_id')
        
        if not session_id or not session_data.get('cart_initialized'):
            session_id = session_data.get('session_id', 'temp')
            session_data['cart_initialized'] = True
        
        return session_id
    
    def add_to_user_cart(self, user_id: int, product_id: int, quantity: int = 1):
        """Add item to user's cart"""
        cart_query = "SELECT CartID FROM Cart WHERE UserID = %s"
        cart_result = self.db.select_query(cart_query, {'user_id': user_id})
        
        if not cart_result:
            create_query = "INSERT INTO Cart (UserID) VALUES (%s)"
            self.db.execute_query(create_query, {'user_id': user_id})
            cart_id = self.db.get_last_insert_id()
        else:
            cart_id = cart_result[0]['CartID']
        
        insert_query = """INSERT INTO CartItems (CartID, ProductID, Quantity) 
                          VALUES (%s, %s, %s)
                          ON DUPLICATE KEY UPDATE Quantity = Quantity + %s"""
        params = {'cart_id': cart_id, 'product_id': product_id, 'quantity': quantity}
        self.db.execute_query(insert_query, params)
    
    def add_to_guest_cart(self, session_id: str, product_id: int, quantity: int = 1):
        """Add item to guest cart"""
        insert_query = """INSERT INTO GuestCart (SessionID, ProductID, Quantity) 
                          VALUES (%s, %s, %s)
                          ON DUPLICATE KEY UPDATE Quantity = Quantity + %s"""
        params = {'session_id': session_id, 'product_id': product_id, 'quantity': quantity}
        self.db.execute_query(insert_query, params)
    
    def get_user_cart_items(self, user_id: int) -> List[CartItem]:
        """Get all cart items for a user"""
        query = """SELECT ci.CartItemID, ci.CartID, ci.ProductID, ci.Quantity,
                   p.ProductName, p.Price, p.Image
                   FROM CartItems ci
                   JOIN Cart c ON ci.CartID = c.CartID
                   JOIN Products p ON ci.ProductID = p.ProductID
                   WHERE c.UserID = %s"""
        
        results = self.db.select_query(query, {'user_id': user_id})
        items = []
        
        for row in results:
            items.append(CartItem(
                cart_item_id=row['CartItemID'],
                cart_id=row['CartID'],
                product_id=row['ProductID'],
                quantity=row['Quantity'],
                product_name=row['ProductName'],
                price=float(row['Price']),
                image=row['Image']
            ))
        
        return items
    
    def get_guest_cart_items(self, session_id: str) -> List[GuestCartItem]:
        """Get all cart items for a guest session"""
        if not session_id:
            return []
        
        query = """SELECT gc.SessionID, gc.ProductID, gc.Quantity,
                   p.ProductName, p.Price, p.Image
                   FROM GuestCart gc
                   JOIN Products p ON gc.ProductID = p.ProductID
                   WHERE gc.SessionID = %s"""
        
        try:
            results = self.db.select_query(query, {'session_id': session_id})
            items = []
            
            for row in results:
                items.append(GuestCartItem(
                    session_id=row['SessionID'],
                    product_id=row['ProductID'],
                    quantity=row['Quantity'],
                    product_name=row['ProductName'],
                    price=float(row['Price']),
                    image=row['Image']
                ))
            
            return items
        except Exception as e:
            print(f"Error fetching guest cart items: {e}")
            return []
    
    def update_user_cart_quantity(self, user_id: int, product_id: int, quantity: int):
        """Update quantity for user cart item"""
        if quantity <= 0:
            self.remove_from_user_cart(user_id, product_id)
            return
        
        query = """UPDATE CartItems ci
                   JOIN Cart c ON ci.CartID = c.CartID
                   SET ci.Quantity = %s
                   WHERE c.UserID = %s AND ci.ProductID = %s"""
        self.db.execute_query(query, {'quantity': quantity, 'user_id': user_id, 'product_id': product_id})
    
    def update_guest_cart_quantity(self, session_id: str, product_id: int, quantity: int):
        """Update quantity for guest cart item"""
        if quantity <= 0:
            self.remove_from_guest_cart(session_id, product_id)
            return
        
        query = """UPDATE GuestCart
                   SET Quantity = %s
                   WHERE SessionID = %s AND ProductID = %s"""
        self.db.execute_query(query, {'quantity': quantity, 'session_id': session_id, 'product_id': product_id})
    
    def remove_from_user_cart(self, user_id: int, product_id: int):
        """Remove item from user cart"""
        query = """DELETE ci FROM CartItems ci
                   JOIN Cart c ON ci.CartID = c.CartID
                   WHERE c.UserID = %s AND ci.ProductID = %s"""
        self.db.execute_query(query, {'user_id': user_id, 'product_id': product_id})
    
    def remove_from_guest_cart(self, session_id: str, product_id: int):
        """Remove item from guest cart"""
        query = """DELETE FROM GuestCart
                   WHERE SessionID = %s AND ProductID = %s"""
        self.db.execute_query(query, {'session_id': session_id, 'product_id': product_id})
    
    def get_user_cart_count(self, user_id: int) -> int:
        """Get total quantity of items in user's cart"""
        query = """SELECT SUM(ci.Quantity) as total_count
                   FROM CartItems ci
                   JOIN Cart c ON ci.CartID = c.CartID
                   WHERE c.UserID = %s"""
        
        result = self.db.select_query(query, {'user_id': user_id})
        return result[0]['total_count'] if result and result[0]['total_count'] else 0
    
    def get_guest_cart_count(self, session_id: str) -> int:
        """Get total quantity of items in guest cart"""
        if not session_id:
            return 0
        
        query = """SELECT SUM(Quantity) as total_count
                   FROM GuestCart
                   WHERE SessionID = %s"""
        
        result = self.db.select_query(query, {'session_id': session_id})
        return result[0]['total_count'] if result and result[0]['total_count'] else 0

