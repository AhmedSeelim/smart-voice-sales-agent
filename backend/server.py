import os
import uuid
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from livekit import api
from livekit.api import LiveKitAPI, ListRoomsRequest
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi-server")

app = FastAPI(
    title="Hardware Sales Agent API",
    description="API for LiveKit room management and token generation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def generate_room_name() -> str:
    """Generate a unique room name."""
    name = "room-" + str(uuid.uuid4())[:8]
    rooms = await get_rooms()
    while name in rooms:
        name = "room-" + str(uuid.uuid4())[:8]
    return name


async def get_rooms() -> list[str]:
    """Get list of active room names."""
    lk_api = LiveKitAPI()
    try:
        rooms = await lk_api.room.list_rooms(ListRoomsRequest())
        return [room.name for room in rooms.rooms]
    finally:
        await lk_api.aclose()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Hardware Sales Agent API",
        "version": "1.0.0",
        "endpoints": {
            "get_token": "/getToken",
            "health": "/health"
        }
    }


@app.get("/getToken")
async def get_token(
        name: str = Query(default="Customer", description="Participant name"),
        room: Optional[str] = Query(default=None, description="Room name (auto-generated if not provided)")
):
    """
    Generate a LiveKit access token for joining a room.

    Args:
        name: Participant's name
        room: Room name (optional, will be auto-generated if not provided)

    Returns:
        JWT token string for room access
    """
    logger.info(f"Token request - Name: {name}, Room: {room}")

    # Generate room name if not provided
    if not room:
        room = await generate_room_name()
        logger.info(f"Generated room name: {room}")

    # Get API credentials from environment
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        logger.error("LiveKit API credentials not found in environment")
        return {"error": "Server configuration error"}

    # Create access token
    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(name)
        .with_name(name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room
            )
        )
    )

    jwt_token = token.to_jwt()
    logger.info(f"Token generated successfully for {name} in room {room}")

    return {
        "token": jwt_token,
        "room": room,
        "name": name
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "hardware-sales-agent"
    }


@app.get("/rooms")
async def list_rooms():
    """List all active rooms."""
    try:
        rooms = await get_rooms()
        return {
            "rooms": rooms,
            "count": len(rooms)
        }
    except Exception as e:
        logger.error(f"Error listing rooms: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=5001,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
