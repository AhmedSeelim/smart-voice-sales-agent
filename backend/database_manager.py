import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from vector_db import ProductVectorDB
from sql_db import ProductDatabase
import logging

logger = logging.getLogger("database-manager")
logger.setLevel(logging.INFO)


class DatabaseManager:
    """
    Unified database manager that handles both vector similarity search
    and SQL-based product inventory and order management.
    """

    def __init__(
            self,
            vector_db_dir: str = "./product_db",
            sql_db_path: str = "products.db",
            model_name: str = "Alibaba-NLP/gte-multilingual-base"
    ):
        """
        Initialize both vector and SQL databases.

        Args:
            vector_db_dir: Directory for FAISS index storage
            sql_db_path: Path to SQLite database file
            model_name: Name of the sentence transformer model
        """
        logger.info("Initializing Database Manager...")

        # Initialize vector database for similarity search
        self.vector_db = ProductVectorDB(
            model_name=model_name,
            db_directory=vector_db_dir
        )

        # Initialize SQL database for inventory management
        self.sql_db = ProductDatabase(db_path=sql_db_path)

        logger.info("Database Manager initialized successfully")

    def load_products_from_json(self, json_path: str):
        """
        Load products into both vector and SQL databases from JSON file.

        Args:
            json_path: Path to products JSON file
        """
        logger.info(f"Loading products from {json_path}")

        # Load into vector database for similarity search
        self.vector_db.load_from_json(json_path)

        # Load into SQL database for inventory management
        self.sql_db.load_products_from_json(json_path)

        logger.info("Products loaded into both databases")

    def load_saved_indexes(self):
        """Load previously saved FAISS index and products data."""
        logger.info("Loading saved indexes...")
        self.vector_db.load_index()
        logger.info("Indexes loaded successfully")

    def save_indexes(self):
        """Save FAISS index and products data to disk."""
        logger.info("Saving indexes...")
        self.vector_db.save_index()
        logger.info("Indexes saved successfully")

    def search_products(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search for similar products using vector similarity.
        Results include real-time inventory quantities from SQL database.

        Args:
            query: Search query describing product needs
            top_k: Number of top results to return

        Returns:
            List of product dictionaries with similarity scores and current quantities
        """
        logger.info(f"Searching for products: '{query}' (top_k={top_k})")

        # Get similar products from vector database
        similar_products = self.vector_db.search_similar_products(query, top_k)

        # Enrich with real-time quantities from SQL database
        enriched_products = []
        for product in similar_products:
            product_info = self.sql_db.get_product_info(product['id'])
            if product_info:
                # Update quantity with real-time data
                product['quantity'] = product_info['quantity']
                enriched_products.append(product)

        return enriched_products

    def get_product_info(self, product_id: int) -> Optional[Dict]:
        """
        Get detailed product information by ID.

        Args:
            product_id: Product ID

        Returns:
            Product dictionary or None if not found
        """
        return self.sql_db.get_product_info(product_id)

    def find_product_by_name(self, product_name: str, threshold: float = 0.5) -> Optional[Dict]:
        """
        Find product by approximate name using vector similarity.
        The LLM can provide an approximate name and this will find the best match.

        Args:
            product_name: Approximate or partial product name
            threshold: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            Best matching product dictionary or None if no good match found
        """
        logger.info(f"Finding product by name: '{product_name}' (threshold={threshold})")

        try:
            # Use vector search to find similar products
            results = self.vector_db.search_similar_products(product_name, top_k=1)

            if results and results[0]['similarity_score'] >= threshold:
                product = results[0]
                # Enrich with real-time quantity from SQL database
                product_info = self.sql_db.get_product_info(product['id'])
                if product_info:
                    product['quantity'] = product_info['quantity']
                    logger.info(f"Found match: {product['name']} (score: {product['similarity_score']:.2%})")
                    return product

            logger.warning(f"No good match found for '{product_name}'")
            return None

        except Exception as e:
            logger.error(f"Error finding product by name: {e}")
            return None

    def create_request(
            self,
            user_name: str,
            address: str,
            product_id: int
    ) -> Tuple[bool, str]:
        """
        Create a product request and update inventory.

        Args:
            user_name: Customer name
            address: Delivery address
            product_id: ID of requested product

        Returns:
            Tuple of (success: bool, message: str)
        """
        logger.info(f"Creating request for user '{user_name}', product ID: {product_id}")
        return self.sql_db.make_request(user_name, address, product_id)

    def create_request_by_name(
            self,
            user_name: str,
            address: str,
            product_name: str,
            threshold: float = 0.5
    ) -> Tuple[bool, str]:
        """
        Create a product request using approximate product name.
        Finds the best matching product and creates the request.

        Args:
            user_name: Customer name
            address: Delivery address
            product_name: Approximate or partial product name
            threshold: Minimum similarity threshold for matching

        Returns:
            Tuple of (success: bool, message: str)
        """
        logger.info(f"Creating request by name for '{product_name}'")

        # Find product by approximate name
        product = self.find_product_by_name(product_name, threshold)

        if not product:
            return False, f"Could not find a product matching '{product_name}'. Please provide more details or try a different description."

        # Create request with the found product ID
        logger.info(f"Matched to product: {product['name']} (ID: {product['id']})")
        success, message = self.sql_db.make_request(user_name, address, product['id'])

        # Add the matched product name to the message for clarity
        if success:
            return True, f"Matched to '{product['name']}'. {message}"
        else:
            return False, message

    def get_all_requests(self) -> List[Dict]:
        """
        Get all product requests.

        Returns:
            List of request dictionaries
        """
        return self.sql_db.get_all_requests()

    def close(self):
        """Close database connections."""
        logger.info("Closing database connections...")
        self.sql_db.close()
        logger.info("Database connections closed")