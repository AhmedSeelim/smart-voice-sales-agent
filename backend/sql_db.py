import json
import sqlite3
from typing import List, Dict, Tuple, Optional


class ProductDatabase:
    """SQLite database for product inventory and order management."""

    def __init__(self, db_path: str = "products.db"):
        """Initialize SQLite database connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """Create products and requests tables."""
        cursor = self.conn.cursor()

        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                quantity INTEGER NOT NULL
            )
        ''')

        # Requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                address TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        self.conn.commit()
        print("Database tables created successfully.")

    def load_products_from_json(self, json_path: str):
        """Load products from JSON file into SQLite database."""
        with open(json_path, 'r', encoding='utf-8') as f:
            products = json.load(f)

        cursor = self.conn.cursor()

        # Clear existing products
        cursor.execute('DELETE FROM products')

        # Insert products
        for product in products:
            cursor.execute('''
                INSERT INTO products (id, name, description, quantity)
                VALUES (?, ?, ?, ?)
            ''', (product['id'], product['name'], product['description'], product['quantity']))

        self.conn.commit()
        print(f"Loaded {len(products)} products into database.")

    def make_request(self, user_name: str, address: str, product_id: int) -> Tuple[bool, str]:
        """
        Create a product request: reduce quantity by 1 and record the request.

        Returns:
            Tuple[bool, str]: (success, message)
        """
        cursor = self.conn.cursor()

        try:
            # Check if product exists and has quantity
            cursor.execute(
                'SELECT name, quantity FROM products WHERE id = ?',
                (product_id,)
            )
            result = cursor.fetchone()

            if not result:
                return False, f"Product with ID {product_id} not found."

            product_name, quantity = result

            if quantity <= 0:
                return False, f"Product '{product_name}' is out of stock."

            # Reduce quantity by 1
            cursor.execute(
                'UPDATE products SET quantity = quantity - 1 WHERE id = ?',
                (product_id,)
            )

            # Insert request record
            cursor.execute('''
                INSERT INTO requests (user_name, address, product_id, product_name)
                VALUES (?, ?, ?, ?)
            ''', (user_name, address, product_id, product_name))

            self.conn.commit()

            return True, f"Request created successfully for '{product_name}'. Remaining quantity: {quantity - 1}"

        except Exception as e:
            self.conn.rollback()
            return False, f"Error creating request: {str(e)}"

    def get_product_info(self, product_id: int) -> Optional[Dict]:
        """Get product information by ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, name, description, quantity FROM products WHERE id = ?',
            (product_id,)
        )
        result = cursor.fetchone()

        if result:
            return {
                'id': result[0],
                'name': result[1],
                'description': result[2],
                'quantity': result[3]
            }
        return None

    def get_all_requests(self) -> List[Dict]:
        """Get all product requests."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT request_id, user_name, address, product_id, product_name, request_time
            FROM requests
            ORDER BY request_time DESC
        ''')

        requests = []
        for row in cursor.fetchall():
            requests.append({
                'request_id': row[0],
                'user_name': row[1],
                'address': row[2],
                'product_id': row[3],
                'product_name': row[4],
                'request_time': row[5]
            })

        return requests

    def close(self):
        """Close database connection."""
        self.conn.close()