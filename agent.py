"""
AI Voice Agent using LiveKit Agents 1.0+ and Cerebras Inference API
Updated for latest API compatibility and best practices
"""

import asyncio
import logging
import os
import json
import aiohttp
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


async def search_perplexity(query: str) -> str:
    """Search Perplexity API for context related to the user's query"""
    try:
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if not perplexity_api_key:
            logger.warning("PERPLEXITY_API_KEY not found in environment variables")
            return ""
        
        url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "user",
                    "content": f"Provide a brief summary of current information about: {query}"
                }
            ],
            "max_tokens": 300,
            "temperature": 0.2
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    if content:
                        logger.info(f"🔍 PERPLEXITY CONTEXT: {content[:100]}...")
                        return content
                    else:
                        logger.warning("No content received from Perplexity API")
                        return ""
                else:
                    error_text = await response.text()
                    logger.error(f"Perplexity API error {response.status}: {error_text}")
                    return ""
            
    except asyncio.TimeoutError:
        logger.error("Perplexity API request timed out")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error in Perplexity search: {e}")
        return ""


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
            "You are a helpful AI voice assistant with access to current information. "
            "When provided with context from search results, incorporate that information naturally into your responses. "
            "Keep your responses concise and conversational. "
            "You are speaking, not writing, so avoid using special characters or formatting. "
            "Be friendly, helpful, and natural in your responses. "
            "If you have recent information about a topic, mention that it's current or recent information."
        )
    )
    
    # Store the original LLM for context-aware responses
    base_llm = openai.LLM.with_cerebras(
        model="llama3.1-8b",
        temperature=0.7,
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
        llm=base_llm,
        
        # Text-to-Speech using OpenAI (more reliable than Cartesia free tier)
        tts=openai.TTS(
            voice="alloy",
            model="tts-1",
            speed=1.0,
        ),
        
        # Advanced turn detection for natural conversations
        turn_detection=MultilingualModel(),
        
        # Additional configurations
        allow_interruptions=True,
    )
    
    # Track pause state and search queries
    is_paused = False
    pending_search_queries = []
    
    # Set up event listeners for logging and Perplexity integration
    @session.on("user_input_transcribed")
    def on_user_transcribed(transcription: str):
        """Log user's transcribed speech and trigger Perplexity search if needed"""
        logger.info(f"👤 USER SAID: {transcription}")
        print(f"\n{'='*60}")
        print(f"👤 USER: {transcription}")
        print(f"{'='*60}\n")
        
        # If paused, don't process the transcription
        if is_paused:
            logger.info("⏸️ Agent is paused - ignoring user input")
            return
        
        # Check if the user's question would benefit from current information
        search_keywords = [
            'what is', 'who is', 'when did', 'how to', 'latest', 'recent', 'current', 
            'news', 'update', 'today', 'now', 'happening', 'what happened',
            'tell me about', 'explain', 'information about', 'search for',
            'find', 'look up', 'details about', 'facts about'
        ]
        
        # Check if the query contains search-worthy keywords and is substantial
        should_search = (
            any(keyword in transcription.lower() for keyword in search_keywords) and 
            len(transcription.strip()) > 10 and
            not is_paused
        )
        
        if should_search:
            logger.info(f"🔍 User query detected for Perplexity search: {transcription}")
            # Store the transcription for use in the conversation handler
            pending_search_queries.append(transcription)
    
    @session.on("conversation_item_added")
    def on_conversation_item(item):
        """Log conversation items and handle context enhancement with Perplexity"""
        async def handle_user_query():
            """Async handler for user queries with Perplexity search"""
            user_query = item.content
            search_keywords = [
                'what is', 'who is', 'when did', 'how to', 'latest', 'recent', 'current', 
                'news', 'update', 'today', 'now', 'happening', 'what happened',
                'tell me about', 'explain', 'information about'
            ]
            
            should_search = any(keyword in user_query.lower() for keyword in search_keywords)
            
            if should_search and len(user_query.strip()) > 10 and not is_paused:
                logger.info(f"🔍 Searching Perplexity for context: {user_query}")
                context = await search_perplexity(user_query)
                
                if context:
                    # Generate response with context
                    enhanced_instruction = (
                        f"Based on this current information: {context}\n\n"
                        f"Please respond to the user's question naturally and conversationally. "
                        f"Incorporate the relevant information from the context if it helps answer their question. "
                        f"Keep your response concise and natural for voice conversation."
                    )
                    
                    # Generate reply with enhanced context
                    await session.generate_reply(instructions=enhanced_instruction)
        
        if hasattr(item, 'role') and hasattr(item, 'content'):
            if item.role == 'user':
                # If we're paused, don't generate responses
                if is_paused:
                    logger.info("⏸️ Agent is paused - not generating response")
                    return
                
                # Create async task for handling user query with Perplexity
                asyncio.create_task(handle_user_query())
            
            elif item.role == 'assistant':
                logger.info(f"🤖 AGENT RESPONDED: {item.content}")
                print(f"\n{'='*60}")
                print(f"🤖 AGENT: {item.content}")
                print(f"{'='*60}\n")
    
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
            prewarm_fnc=prewarm,
        )
    )


if __name__ == "__main__":
    main()