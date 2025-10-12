"""
AI Voice Agent using LiveKit Agents 1.0+ and Cerebras Inference API
Updated for latest API compatibility and best practices
"""

import asyncio
import logging
import os
from typing import Annotated

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    Agent,
    AgentSession, 
    JobContext, 
    WorkerOptions, 
    cli,
    RoomInputOptions
)
from livekit.plugins import deepgram, openai, silero, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prewarm(proc: agents.JobProcess):
    """Preload models to reduce cold start times"""
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent using latest LiveKit Agents API"""
    
    logger.info(f"Connecting to room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    
    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"Starting voice assistant for participant {participant.identity}")
    
    # Create the agent with instructions
    agent = Agent(
        instructions=(
            "You are a helpful AI voice assistant. "
            "Keep your responses concise and conversational. "
            "You are speaking, not writing, so avoid using special characters or formatting. "
            "Be friendly, helpful, and natural in your responses."
        )
    )
    
    # Initialize the agent session with the latest API
    session = AgentSession(
        # Use VAD from userdata (prewarmed)
        vad=ctx.proc.userdata["vad"],
        
        # Speech-to-Text using Deepgram
        stt=deepgram.STT(
            model="nova-2",
            language="en",
            smart_format=True,
        ),
        
        # LLM using Cerebras via OpenAI-compatible endpoint
        llm=openai.LLM.with_cerebras(
            model="llama3.1-70b",  # Using Cerebras's fast Llama 3.1 70B
            temperature=0.7,
            max_tokens=1024,
        ),
        
        # Text-to-Speech using OpenAI
        tts=openai.TTS(
            model="tts-1",
            voice="alloy",
            speed=1.0,
        ),
        
        # Advanced turn detection for natural conversations
        turn_detection=MultilingualModel(),
        
        # Additional configurations
        allow_interruptions=True,
        int_min_words=0,  # Allow interruption at any point
        int_speech_duration=0.5,  # Interrupt after 500ms of speech
        
        # Enable false interruption detection and auto-resume
        false_interruption_timeout=3.0,
        resume_false_interruption=True,
    )
    
    # Start the session with enhanced room input options
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # Enhanced noise cancellation (requires LiveKit Cloud or compatible server)
            noise_cancellation=noise_cancellation.BVC(),
            
            # Auto-subscribe to audio tracks
            auto_subscribe=True,
        )
    )
    
    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user warmly and ask how you can help them today."
    )
    
    logger.info("Voice assistant started successfully with latest LiveKit Agents API")


def main():
    """Run the voice agent worker with optimized configuration"""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,  # Add prewarming for better performance
            
            # Worker configuration for production
            num_idle_workers=1,
            max_retry=3,
            ws_url=os.getenv("LIVEKIT_URL"),
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
        )
    )


if __name__ == "__main__":
    main()