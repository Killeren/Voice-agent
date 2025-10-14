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
    cli
)
from livekit.plugins import deepgram, openai, silero, cartesia
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prewarm(proc: agents.JobProcess):
    """Preload models to reduce cold start times"""
    # Load VAD with more sensitive settings
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.2,  # Detect shorter speech (200ms)
        min_silence_duration=0.5,  # Wait less time for silence (500ms)  
        activation_threshold=0.4,  # Lower threshold = more sensitive (default 0.5)
        max_buffered_speech=60.0,  # Allow longer speech segments
    )


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
            model="llama3.1-8b",  # Using Cerebras's Llama 3.1 8B (fast and available)
            temperature=0.7,
        ),
        
        # Text-to-Speech using Cartesia (no quota limits on free tier)
        tts=cartesia.TTS(
            model="sonic-2-2025-03-07",
            voice="79a125e8-cd45-4c13-8a67-188112f4dd22",  # British Lady
            speed=1.0,
        ),
        
        # Advanced turn detection for natural conversations
        turn_detection=MultilingualModel(),
        
        # Additional configurations
        allow_interruptions=True,
    )
    
    # Track pause state
    is_paused = False
    
    # Set up event listeners for logging
    @session.on("user_input_transcribed")
    def on_user_transcribed(transcription: str):
        """Log user's transcribed speech"""
        logger.info(f"👤 USER SAID: {transcription}")
        print(f"\n{'='*60}")
        print(f"👤 USER: {transcription}")
        print(f"{'='*60}\n")
        
        # If paused, don't process the transcription
        if is_paused:
            logger.info("⏸️ Agent is paused - ignoring user input")
            return
    
    @session.on("conversation_item_added")
    def on_conversation_item(item):
        """Log conversation items and handle pause state"""
        if hasattr(item, 'role') and hasattr(item, 'content'):
            if item.role == 'assistant':
                logger.info(f"🤖 AGENT RESPONDED: {item.content}")
                print(f"\n{'='*60}")
                print(f"🤖 AGENT: {item.content}")
                print(f"{'='*60}\n")
        
        # If we're paused, don't generate responses
        if is_paused and hasattr(item, 'role') and item.role == 'user':
            logger.info("⏸️ Agent is paused - not generating response")
            return
    
    @session.on("user_state_changed")
    def on_user_state_changed(state):
        """Log when user state changes (listening, speaking, etc)"""
        logger.info(f"🎤 USER STATE: {state}")
    
    @session.on("agent_state_changed")
    def on_agent_state_changed(state):
        """Log when agent state changes"""
        logger.info(f"🤖 AGENT STATE: {state}")
    
    # Add data message handling for pause/resume
    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        """Handle data messages from frontend (pause/resume)"""
        nonlocal is_paused
        try:
            import json
            message = json.loads(data.data.decode())
            action = message.get('action')
            
            if action == 'pause':
                logger.info("⏸️ PAUSE REQUEST: Agent paused by user")
                is_paused = True
                # Stop current TTS if playing by interrupting the session
                session.interrupt()
                
            elif action == 'resume':
                logger.info("▶️ RESUME REQUEST: Agent resuming...")
                is_paused = False
                
                if message.get('requestGreeting', False):
                    # Generate a very short greeting when resuming, but only if not paused
                    if not is_paused:
                        # Schedule the greeting generation without await
                        session.generate_reply(
                            instructions="Say a very brief greeting in 1-4 words like 'Hi again' or 'I'm back' or 'Hello there'"
                        )
                    
        except Exception as e:
            logger.warning(f"Failed to parse data message: {e}")
    
    # Start the session
    await session.start(
        agent=agent,
        room=ctx.room,
    )
    
    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user warmly and ask how you can help them today."
    )
    
    logger.info("Voice assistant started successfully with latest LiveKit Agents API")


def main():
    """Run the voice agent worker with optimized configuration"""
    # Ensure required environment variables are set
    livekit_url = os.getenv("LIVEKIT_URL")
    livekit_api_key = os.getenv("LIVEKIT_API_KEY")
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not all([livekit_url, livekit_api_key, livekit_api_secret]):
        raise ValueError("Missing required environment variables: LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET")
    
    # Type assertions after validation
    assert livekit_url is not None
    assert livekit_api_key is not None
    assert livekit_api_secret is not None
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,  # Add prewarming for better performance
        )
    )


if __name__ == "__main__":
    main()