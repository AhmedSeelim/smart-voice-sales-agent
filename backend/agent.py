from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, function_tool
from livekit.plugins import google
from dotenv import load_dotenv
from database_manager import DatabaseManager
import logging

load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hardware-agent")

# Initialize database manager globally
db_manager = DatabaseManager(
    vector_db_dir="./product_db",
    sql_db_path="products.db",
    model_name="Alibaba-NLP/gte-multilingual-base"
)

# Load products (you can also load from saved index if available)
try:
    logger.info("Attempting to load saved indexes...")
    db_manager.load_saved_indexes()
    logger.info("Loaded saved indexes successfully")
except FileNotFoundError:
    logger.info("No saved indexes found. Please load products from JSON first.")
    # Uncomment the following line to load from JSON initially:
    # db_manager.load_products_from_json("data.json")
    # db_manager.save_indexes()


class HardwareSalesAgent(Agent):
    """Hardware store sales agent with product search and order processing capabilities."""

    def __init__(self):
        logger.info("Initializing Hardware Sales Agent...")

        # Prepare comprehensive instructions with product context
        instructions = """
You are an Egyptian Arabic helpful and friendly hardware(Computer parts) store sales assistant communicating by voice. 
All text that you return will be spoken aloud, so don't use things like bullets, 
slashes, or any other non-pronounceable punctuation.

Your role is to:
1. Help customers find products they need by understanding their requirements
2. Search the product database when customers describe what they're looking for
3. Provide detailed information about products including descriptions and availability
4. Process product requests by collecting customer name, delivery address, and product information

CRITICAL RULES:
- Be conversational and natural in your responses
- When a customer describes what they need, use search_products to find relevant items
- Present product options clearly in natural language
- When a customer wants to order a product, you can use EITHER:
  * make_product_request_by_name - if they mention the product by name 
  * make_product_request - if you have the exact product ID from search results
- PREFER using make_product_request_by_name as it's more natural for customers
- The system will automatically find the best matching product, so the customer doesn't need exact names
- Always confirm the matched product name before finalizing the order
- If a product is out of stock, apologize and suggest similar alternatives
- Speak in complete sentences, avoid special characters or formatting
- Be enthusiastic but professional

Remember: You have access to tools to search products and process requests. Use them proactively to help customers.
"""

        # Initialize Google Gemini Live API
        llm = google.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-09-2025",
            voice="Puck",  # Options: Puck, Charon, Kore, Fenrir, Aoede
            temperature=0.8,
            instructions=instructions,
        )

        # Initialize the agent with the LLM
        super().__init__(llm=llm,instructions=instructions)

        logger.info("Hardware Sales Agent initialized successfully")

    async def on_enter(self):
        """Called when agent enters the session - greet the user."""
        logger.info("Agent entering session - sending greeting")
        print("Current Agent: 🛠️ Hardware Sales Agent 🛠️")

        await self.session.generate_reply(
            user_input="Give a warm, friendly greeting in 1-2 sentences. "
                       "Introduce yourself as a hardware store sales assistant and "
                       "offer to help them find products or answer questions."
        )

    @function_tool
    async def search_products(self, query: str, top_k: int = 2):
        """
        Search for products in the hardware store based on customer's needs.

        Args:
            query: an Arabic concise, fully formed search query describing what the customer needs.
                   Extract key requirements from their conversational input.
                   Examples: "cordless drill with battery", "outdoor waterproof paint"
            top_k: Number of similar products to return (default: 2)

        Returns:
            Formatted string with product information including names, descriptions,
            availability, and match scores.
        """
        logger.info(f"🔍 Searching products: '{query}' (top_k={top_k})")

        try:
            results = db_manager.search_products(query, top_k)

            if not results:
                return (
                    "I couldn't find any products matching that description. "
                    "Could you provide more details or try describing it differently?"
                )

            # Format results naturally for voice output
            response = f"I found {len(results)} product{'s' if len(results) > 1 else ''} for you. "

            for i, product in enumerate(results, 1):
                stock_status = "in stock" if product['quantity'] > 0 else "currently out of stock"
                match_quality = "excellent" if product['similarity_score'] > 0.7 else "good"

                response += (
                    f"Option {i} is the {product['name']}. "
                    f"{product['description']} "
                    f"We have {product['quantity']} units {stock_status}. "
                    f"This is a {match_quality} match for what you're looking for. "
                )

            response += "Would you like more details about any of these, or shall I help you place an order?"

            logger.info(f"✅ Found {len(results)} products")
            return response

        except Exception as e:
            logger.error(f"❌ Error searching products: {e}")
            return "I encountered an error while searching for products. Could you try describing what you need again?"

    @function_tool
    async def make_product_request(self, user_name: str, address: str, product_id: int):
        """
        Process a product request using the exact product ID.
        Use this when you have the specific product ID from search results.

        Args:
            user_name: The customer's full name for the delivery
            address: The complete delivery address including street, city, and relevant details
            product_id: The exact ID of the product from search results

        Returns:
            Confirmation message or error information.
        """
        logger.info(f"📦 Processing request by ID - User: {user_name}, Product ID: {product_id}")

        try:
            success, message = db_manager.create_request(user_name, address, product_id)

            if success:
                logger.info(f"✅ Request created successfully")
                return (
                    f"Perfect! {message} "
                    f"I've confirmed your order for {user_name} to be delivered to {address}. "
                    f"We'll process your order shortly and contact you with shipping details. "
                    f"Is there anything else I can help you with today?"
                )
            else:
                logger.warning(f"⚠️ Request failed: {message}")
                return (
                    f"I apologize, but I couldn't complete your request. {message} "
                    f"Would you like to select a different product or check other available options?"
                )

        except Exception as e:
            logger.error(f"❌ Error processing request: {e}")
            return (
                "I encountered an error while processing your request. "
                "Please try again, or I can help you find a different product."
            )

    @function_tool
    async def make_product_request_by_name(self, user_name: str, address: str, product_name: str):
        """
        Process a product request using an approximate product name.
        Use this when the customer mentions a product by name without knowing the exact ID.
        The system will find the best matching product automatically.

        Args:
            user_name: The customer's full name for the delivery
            address: The complete delivery address including street, city, and relevant details
            product_name: Approximate product name as mentioned by the customer
                         (doesn't need to be exact, e.g., "dewalt drill" or "outdoor paint")

        Returns:
            Confirmation message with the matched product or error if no match found.
        """
        logger.info(f"📦 Processing request by name - User: {user_name}, Product: '{product_name}'")

        try:
            success, message = db_manager.create_request_by_name(user_name, address, product_name)

            if success:
                logger.info(f"✅ Request created successfully with name matching")
                return (
                    f"Perfect! {message} "
                    f"I've confirmed your order for {user_name} to be delivered to {address}. "
                    f"We'll process your order shortly and contact you with shipping details. "
                    f"Is there anything else I can help you with today?"
                )
            else:
                logger.warning(f"⚠️ Request failed: {message}")
                return (
                    f"I apologize, but {message} "
                    f"Could you provide more details about the product you're looking for, "
                    f"or would you like me to search for similar items?"
                )

        except Exception as e:
            logger.error(f"❌ Error processing request by name: {e}")
            return (
                "I encountered an error while processing your request. "
                "Could you try describing the product differently?"
            )

    @function_tool
    async def get_product_details(self, product_id: int):
        """
        Get detailed information about a specific product by its exact ID.
        Use this when you have the product ID from search results.

        Args:
            product_id: The exact product ID to get detailed information about

        Returns:
            Detailed product information in natural language.
        """
        logger.info(f"ℹ️ Getting details for product ID: {product_id}")

        try:
            product = db_manager.get_product_info(product_id)

            if not product:
                return (
                    f"I couldn't find a product with ID {product_id}. "
                    f"Could you double-check the product number?"
                )

            stock_status = "available" if product['quantity'] > 0 else "out of stock"

            response = (
                f"Let me tell you about the {product['name']}. "
                f"{product['description']} "
                f"This item is currently {stock_status}. "
            )

            if product['quantity'] > 0:
                response += (
                    f"We have {product['quantity']} units in stock. "
                    f"Would you like to place an order for this product?"
                )
            else:
                response += "Unfortunately we're out of stock right now. Would you like me to find similar alternatives?"

            logger.info(f"✅ Retrieved details for product {product_id}")
            return response

        except Exception as e:
            logger.error(f"❌ Error getting product details: {e}")
            return "I had trouble retrieving that product information. Could you try again?"

    @function_tool
    async def get_product_details_by_name(self, product_name: str):
        """
        Get detailed information about a product using an approximate name.
        Use this when the customer asks about a product by name without knowing the ID.
        The system will find the best matching product automatically.

        Args:
            product_name: Approximate product name as mentioned by the customer
                         (doesn't need to be exact, e.g., "dewalt drill" or "laser measure")

        Returns:
            Detailed product information in natural language.
        """
        logger.info(f"ℹ️ Getting details by name: '{product_name}'")

        try:
            product = db_manager.find_product_by_name(product_name)

            if not product:
                return (
                    f"I couldn't find a product matching '{product_name}'. "
                    f"Could you provide more details or describe it differently? "
                    f"Or I can search our full catalog if you'd like."
                )

            stock_status = "available" if product['quantity'] > 0 else "out of stock"
            match_confidence = product['similarity_score']

            # Add confidence indicator for lower matches
            confidence_phrase = ""
            if match_confidence < 0.8:
                confidence_phrase = "I think you're asking about "

            response = (
                f"{confidence_phrase}the {product['name']}. "
                f"{product['description']} "
                f"This item is currently {stock_status}. "
            )

            if product['quantity'] > 0:
                response += (
                    f"We have {product['quantity']} units in stock. "
                    f"Would you like to place an order for this product?"
                )
            else:
                response += "Unfortunately we're out of stock right now. Would you like me to find similar alternatives?"

            logger.info(f"✅ Retrieved details for '{product['name']}' (match: {match_confidence:.2%})")
            return response

        except Exception as e:
            logger.error(f"❌ Error getting product details by name: {e}")
            return "I had trouble retrieving that product information. Could you try describing it differently?"


async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent."""
    logger.info("🚀 Starting Hardware Sales Agent entrypoint...")

    # Connect to the room
    await ctx.connect()
    logger.info("✅ Connected to room")

    # Create the agent
    agent = HardwareSalesAgent()

    # Create and start the session
    session = AgentSession()
    await session.start(room=ctx.room, agent=agent)

    logger.info("🎯 Agent session started successfully")


if __name__ == "__main__":
    logger.info("🏗️ Starting Hardware Sales Agent Worker...")
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
    logger.info("👋 Agent worker stopped")