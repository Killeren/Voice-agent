"""
Web server for the Voice Agent interface
Handles token generation and serves the frontend
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta

from aiohttp import web
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TokenGenerator:
    """Generate Livekit access tokens"""
    
    def __init__(self):
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")
        self.url = os.getenv("LIVEKIT_URL")
        
        if not all([self.api_key, self.api_secret, self.url]):
            raise ValueError("Missing required Livekit configuration")
    
    async def generate_token(self, room_name: str, participant_name: str) -> dict:
        """Generate an access token for a participant"""
        try:
            token = api.AccessToken(self.api_key, self.api_secret)
            token.with_identity(participant_name)
            token.with_name(participant_name)
            token.with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            
            jwt_token = token.to_jwt()
            
            return {
                "token": jwt_token,
                "url": self.url,
                "room": room_name
            }
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            raise


async def handle_token_request(request):
    """Handle token generation requests"""
    try:
        data = await request.json()
        room_name = data.get("room", "voice-agent-room")
        participant_name = data.get("participant", f"user-{datetime.now().timestamp()}")
        
        token_gen = TokenGenerator()
        token_data = await token_gen.generate_token(room_name, participant_name)
        
        return web.json_response(token_data)
    except Exception as e:
        logger.error(f"Error in token request: {e}")
        return web.json_response(
            {"error": str(e)},
            status=500
        )


async def handle_index(request):
    """Serve the main HTML page"""
    with open("index.html", "r") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")


def create_app():
    """Create and configure the web application"""
    app = web.Application()
    
    # Add routes
    app.router.add_get("/", handle_index)
    app.router.add_post("/api/token", handle_token_request)
    app.router.add_static("/static", "static", name="static")
    
    return app


def main():
    """Run the web server"""
    app = create_app()
    logger.info("Starting web server on http://localhost:8080")
    web.run_app(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
