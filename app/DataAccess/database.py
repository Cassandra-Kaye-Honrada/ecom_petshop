import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional

class DatabaseHelper:
    def __init__(self, conn_string: str):
        """
        Initialize with connection string format:
        'mysql://user:password@host:port/database'
        """
        self.conn_string = conn_string
        self._parse_connection_string()
    
    def _parse_connection_string(self):
        """Parse connection string to get database credentials"""
        if self.conn_string.startswith('mysql://'):
            conn_str = self.conn_string.replace('mysql://', '')
            user_pass, host_db = conn_str.split('@')
            self.user, self.password = user_pass.split(':')
            host_port, self.database = host_db.split('/')
            self.host, self.port = host_port.split(':') if ':' in host_port else (host_port, 3306)
            self.port = int(self.port)
        else:
            raise ValueError("Connection string format: mysql://user:password@host:port/database")
    
    def _get_connection(self):
        """Create and return a database connection"""
        return mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port
        )
    
    def select_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query with optional parameterized query support"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Error as e:
            print(f"Database error: {e}")
            return []
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> int:
        """Execute INSERT, UPDATE, DELETE queries and return affected rows"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            affected_rows = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            return affected_rows
        except Error as e:
            print(f"Database error: {e}")
            return 0
    
    def get_last_insert_id(self) -> int:
        """Get the last inserted ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT LAST_INSERT_ID() as id")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result['id'] if result else 0
        except Error as e:
            print(f"Database error: {e}")
            return 0
    
    def execute_scalar(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute scalar query and return single value"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] if result else None
        except Error as e:
            print(f"Database error: {e}")
            return None