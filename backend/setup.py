"""
Setup script to initialize the hardware sales database.
Run this script once to load your products from JSON into both databases.
"""

import json
from database_manager import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("setup")


def create_sample_products():
    """Create a sample products.json file for testing."""
    sample_products = [
        {
            "id": 1,
            "name": "DeWalt 20V Cordless Drill",
            "description": "Powerful 20V MAX lithium-ion cordless drill with variable speed trigger, LED light, and includes battery and charger. Perfect for drilling and fastening applications.",
            "quantity": 15
        },
        {
            "id": 2,
            "name": "Bosch Laser Distance Measure",
            "description": "Digital laser distance measuring tool with 165ft range, backlit display, and area/volume calculation. Accurate to 1/16 inch.",
            "quantity": 8
        },
        {
            "id": 3,
            "name": "Stanley 25ft Tape Measure",
            "description": "Heavy-duty tape measure with 25-foot blade, auto-lock feature, and durable steel construction. Ideal for construction and DIY projects.",
            "quantity": 30
        },
        {
            "id": 4,
            "name": "Rust-Oleum Outdoor Paint",
            "description": "Waterproof exterior paint, 1 gallon can, weather-resistant formula provides long-lasting protection against rain, sun, and temperature changes. Multiple colors available.",
            "quantity": 20
        },
        {
            "id": 5,
            "name": "Milwaukee Circular Saw",
            "description": "15 Amp corded circular saw with 7-1/4 inch blade, electric brake, and bevel capacity up to 50 degrees. Includes carbide blade.",
            "quantity": 5
        },
        {
            "id": 6,
            "name": "3M N95 Respirator Masks",
            "description": "NIOSH-approved N95 particulate filtering facepiece respirators. Pack of 20 masks, ideal for construction, woodworking, and dust protection.",
            "quantity": 50
        },
        {
            "id": 7,
            "name": "Irwin Quick-Grip Clamps Set",
            "description": "Set of 4 one-handed bar clamps with 6-inch and 12-inch sizes. Quick-release trigger, padded grips, and 140 lb clamping force.",
            "quantity": 12
        },
        {
            "id": 8,
            "name": "Klein Tools Screwdriver Set",
            "description": "10-piece cushion-grip screwdriver set with Phillips and flathead tips. Chrome-plated shafts and color-coded handles.",
            "quantity": 25
        },
        {
            "id": 9,
            "name": "Ryobi Electric Pressure Washer",
            "description": "1800 PSI electric pressure washer with 1.2 GPM flow rate. Includes turbo nozzle, soap applicator, and 20ft high-pressure hose.",
            "quantity": 7
        },
        {
            "id": 10,
            "name": "Gorilla Heavy Duty Glue",
            "description": "Waterproof polyurethane glue, 8 oz bottle. Bonds wood, stone, metal, ceramic, foam, glass and more. Expands 3 times for strong bonds.",
            "quantity": 40
        }
    ]

    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(sample_products, f, ensure_ascii=False, indent=2)

    logger.info("Created sample products.json file")


def main():
    """Main setup function."""
    logger.info("Starting database setup...")

    # Ask user if they want to create sample products
    response = input("Do you want to create a sample products.json file? (y/n): ")
    if response.lower() == 'y':
        create_sample_products()

    # Check if products.json exists
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            products = json.load(f)
            logger.info(f"Found products.json with {len(products)} products")
    except FileNotFoundError:
        logger.error("products.json not found. Please create this file first.")
        return

    # Initialize database manager
    logger.info("Initializing database manager...")
    db_manager = DatabaseManager(
        vector_db_dir="./product_db",
        sql_db_path="products.db",
        model_name="Alibaba-NLP/gte-multilingual-base"
    )

    # Load products into both databases
    logger.info("Loading products into databases...")
    db_manager.load_products_from_json("data.json")

    # Save the vector index
    logger.info("Saving vector index...")
    db_manager.save_indexes()

    # Test the setup with a sample search
    logger.info("\nTesting setup with sample search...")
    test_query = "معالج قوي للألعاب والمونتاج"
    results = db_manager.search_products(test_query, top_k=3)

    logger.info(f"\nSearch results for '{test_query}':")
    for i, product in enumerate(results, 1):
        logger.info(f"{i}. {product['name']} (Score: {product['similarity_score']:.2%})")

    # Close database connections
    db_manager.close()

    logger.info("\n✅ Database setup completed successfully!")
    logger.info("You can now run the agent with: python agent.py dev")


if __name__ == "__main__":
    main()