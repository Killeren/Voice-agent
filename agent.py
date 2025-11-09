"""
AI Voice Agent using LiveKit Agents 1.0+ and Cerebras Inference API with Function Calling
"""

import asyncio
import logging
import os
import json
import aiohttp

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    Agent,
    AgentSession, 
    JobContext, 
    WorkerOptions, 
    cli
)
from livekit.plugins import deepgram, openai, silero

from edge_tts_plugin import EdgeTTS

load_dotenv()

# Configure logging for errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


async def search_perplexity_tool(query: str) -> str:
    """Search Perplexity API for context related to the user's query - used as a tool by the LLM"""
    try:
        perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        if not perplexity_api_key:
            return "Perplexity API key not configured"
        
        # Log when Perplexity search is called
        print(f"🔧 TOOL CALLED: search_perplexity_tool('{query}')")
        
        url = "https://api.perplexity.ai/chat/completions"
        headers = {
            "Authorization": f"Bearer {perplexity_api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "sonar",
            "messages": [{
                "role": "system",
                "content": "You are a helpful assistant that provides current, factual information. Always cite recent sources when available."
            }, {
                "role": "user", 
                "content": f"Please provide current information about: {query}. Include recent developments and cite sources if possible."
            }],
            "max_tokens": 400,
            "temperature": 0.2
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if content:
                        print(f"✅ PERPLEXITY TOOL RESULT: {len(content)} characters")
                        return content
                    else:
                        return "No search results found"
                else:
                    error_text = await response.text()
                    logger.error(f"Perplexity API error {response.status}: {error_text}")
                    return f"Search failed with error {response.status}"
            
    except asyncio.TimeoutError:
        logger.error("Perplexity API request timed out")
        return "Search timed out"
    except Exception as e:
        logger.error(f"Unexpected error in Perplexity search: {e}")
        return f"Search error: {str(e)}"


class CustomLLMWithTools:
    """Custom LLM wrapper that adds function calling capabilities to Cerebras"""
    
    def __init__(self, base_llm):
        self.base_llm = base_llm
        self.tools = {
            "search_perplexity": {
                "function": search_perplexity_tool,
                "description": "Search for current, up-to-date information about a topic. Use this when the user asks about recent events, latest news, current prices, weather, or anything that changes frequently.",
                "parameters": {
                    "query": "The search query - what to search for"
                }
            }
        }
    
    async def generate_response(self, messages, instructions=None):
        """Generate response with tool calling capability"""
        
        # First, check if the user's question needs current information
        tool_check_instructions = f"""
{instructions or "You are a helpful AI voice assistant."}

IMPORTANT: Analyze the user's question and determine if it requires current/recent information.

If the user's question requires current/recent information (like latest news, recent releases, current events, stock prices, weather, etc.), 
respond with EXACTLY this format:

TOOL_CALL: search_perplexity
QUERY: [search query here]

If it's a general knowledge question that doesn't need current info, respond with:

NO_TOOL_NEEDED

Examples:
- "What's OpenAI's latest model?" → TOOL_CALL: search_perplexity\nQUERY: OpenAI latest model release
- "How do I bake a cake?" → NO_TOOL_NEEDED
- "What's the weather today?" → TOOL_CALL: search_perplexity\nQUERY: current weather today
"""

        # Create messages for tool checking
        tool_check_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                tool_check_messages.append({
                    "role": "system", 
                    "content": tool_check_instructions
                })
            else:
                tool_check_messages.append(msg)
        
        # If no system message, add one
        if not any(msg.get("role") == "system" for msg in messages):
            tool_check_messages.insert(0, {
                "role": "system",
                "content": tool_check_instructions
            })
        
        # Check if tools are needed FIRST
        tool_decision = await self._call_llm(tool_check_messages)
        print(f"🧠 TOOL DECISION: {tool_decision.strip()}")
        
        # If tool is needed, use it BEFORE generating any response
        if "TOOL_CALL:" in tool_decision and "search_perplexity" in tool_decision:
            try:
                # Extract query from tool call
                lines = tool_decision.split('\n')
                query_line = [line for line in lines if line.startswith('QUERY:')]
                if query_line:
                    query = query_line[0].replace('QUERY:', '').strip()
                    print(f"🔧 LLM REQUESTED TOOL: search_perplexity('{query}')")
                    
                    # Call the tool
                    tool_result = await search_perplexity_tool(query)
                    
                    # Generate final response with tool results - NO intermediate response
                    final_instructions = f"""
{instructions or "You are a helpful AI voice assistant."}

Based on the search results provided, give a natural, conversational response that directly answers the user's question.
Do not mention that you searched - just provide the information naturally as if you always knew it.
Keep your response concise and conversational since this is a voice interaction.
"""
                    
                    final_messages = [
                        {"role": "system", "content": final_instructions},
                        {"role": "user", "content": messages[-1]["content"]},  # Original user question
                        {"role": "assistant", "content": f"Search results: {tool_result}"},
                        {"role": "user", "content": "Now answer my original question based on this current information."}
                    ]
                    
                    final_response = await self._call_llm(final_messages)
                    print(f"✅ FINAL TOOL-ENHANCED RESPONSE: {final_response[:100]}...")
                    return {
                        "response": final_response,
                        "used_search": True,
                        "search_notification": "Let me search for the latest information on that."
                    }
                    
            except Exception as e:
                logger.error(f"Tool calling error: {e}")
                return {
                    "response": "I tried to search for current information but encountered an error. Let me provide what I know from my training data.",
                    "used_search": False,
                    "search_notification": None
                }
        
        # If no tool needed, generate normal response
        normal_instructions = f"""
{instructions or "You are a helpful AI voice assistant."}

Provide a helpful, conversational response to the user's question.
Keep it concise since this is a voice interaction.
"""
        
        normal_messages = []
        for msg in messages:
            if msg.get("role") == "system":
                normal_messages.append({
                    "role": "system", 
                    "content": normal_instructions
                })
            else:
                normal_messages.append(msg)
        
        if not any(msg.get("role") == "system" for msg in messages):
            normal_messages.insert(0, {
                "role": "system",
                "content": normal_instructions
            })
        
        response = await self._call_llm(normal_messages)
        return {
            "response": response,
            "used_search": False,
            "search_notification": None
        }
    
    async def _call_llm(self, messages):
        """Call the underlying Cerebras LLM"""
        try:
            cerebras_api_key = os.getenv("CEREBRAS_API_KEY")
            if not cerebras_api_key:
                return "Cerebras API key not configured"
                
            url = "https://api.cerebras.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {cerebras_api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": "llama3.1-8b",
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7
            }
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return content
                    else:
                        error_text = await response.text()
                        logger.error(f"Cerebras API error {response.status}: {error_text}")
                        return "Sorry, I'm having trouble generating a response right now."
                        
        except Exception as e:
            logger.error(f"LLM call error: {e}")
            return "Sorry, I'm having trouble processing your request."


def prewarm(proc: agents.JobProcess):
    """Preload models to reduce cold start times"""
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.2,
        min_silence_duration=0.5,
        activation_threshold=0.4,
        max_buffered_speech=60.0,
    )


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent"""
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    participant = await ctx.wait_for_participant()
    
    # Create custom LLM with tools
    base_llm = openai.LLM.with_cerebras(
        model="llama3.1-8b",
        temperature=0.7,
    )
    
    custom_llm = CustomLLMWithTools(base_llm)
    
    agent = Agent(
        instructions=(
            "You are a helpful AI voice assistant with access to current information through search tools. "
            "Keep your responses concise and conversational. "
            "You are speaking, not writing, so avoid using special characters or formatting. "
            "Be friendly, helpful, and natural in your responses. "
            "When you use search tools and find current information, mention that it's recent/current information."
        )
    )
    
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=deepgram.STT(
            model="nova-2",
            language="en",
            smart_format=True,
        ),
        llm=None,  # Disable automatic LLM - we handle this manually with tools
        tts=EdgeTTS(
            voice="en-US-AriaNeural",
            rate="+10%",
            use_fallback=True,
        ),
        allow_interruptions=True,
    )
    
    is_paused = False
    processing_lock = asyncio.Lock()
    transcript_buffer = ""
    last_transcript_time = 0
    await session.start(agent=agent, room=ctx.room)
    
    # Send initial greeting since we disabled automatic LLM
    initial_greeting = "Hello! I'm your AI voice agent ready to help with questions or find current information."
    await session.say(initial_greeting)
    
    @session.on("user_input_transcribed")
    def on_user_transcribed(event):
        """Handle user transcription and generate response with tools"""
        nonlocal transcript_buffer, last_transcript_time
        
        if not hasattr(event, 'transcript') or not isinstance(event.transcript, str):
            logger.error("Invalid transcript event")
            return
            
        transcript_text = event.transcript
        is_final = hasattr(event, 'is_final') and event.is_final
        print(f"📝 TRANSCRIPT: {transcript_text} | Final: {is_final}")
        
        # Only process final transcripts to avoid duplicate processing
        if is_final and transcript_text.strip():
            import time
            current_time = time.time()
            
            # Check if this seems like a continuation of previous speech
            # If less than 2 seconds since last transcript, buffer it
            if current_time - last_transcript_time < 2.0 and transcript_buffer:
                transcript_buffer += " " + transcript_text.strip()
                print(f"🔄 BUFFERING: {transcript_buffer}")
            else:
                transcript_buffer = transcript_text.strip()
                
            last_transcript_time = current_time
            
            # Wait a bit to see if more speech is coming
            async def process_after_delay():
                nonlocal transcript_buffer
                await asyncio.sleep(1.5)  # Wait 1.5 seconds for potential continuation
                
                # Check if buffer was updated during wait  
                current_buffer = transcript_buffer
                if current_buffer:
                    print(f"🎯 FINAL PROCESSING: {current_buffer}")
                    
                    # Clear the buffer immediately to prevent reprocessing
                    transcript_buffer = ""
                    
                    try:
                        message_data = {
                            "type": "conversation",
                            "role": "user", 
                            "text": current_buffer
                        }
                        # Use asyncio.create_task to avoid blocking
                        asyncio.create_task(ctx.room.local_participant.publish_data(
                            json.dumps(message_data).encode(),
                            reliable=True
                        ))
                    except Exception as e:
                        logger.error(f"Failed to send user message to frontend: {e}")
                    
                    # Handle response generation with tools
                    async def handle_response_with_tools():
                        async with processing_lock:
                            if not is_paused:
                                user_query = current_buffer
                                print(f"🤖 PROCESSING with tools: {user_query}")
                                
                                try:
                                    # Build conversation context
                                    messages = [
                                        {"role": "user", "content": user_query}
                                    ]
                                    
                                    # Generate response using our custom LLM with tools
                                    response_result = await custom_llm.generate_response(
                                        messages, 
                                        instructions=agent.instructions
                                    )
                                    
                                    # Handle search notification first if needed
                                    if response_result["used_search"] and response_result["search_notification"]:
                                        print(f"🔍 IMMEDIATE SEARCH NOTIFICATION: {response_result['search_notification']}")
                                        await session.say(response_result["search_notification"])
                                        # Small delay to ensure search notification completes
                                        await asyncio.sleep(1.0)
                                    
                                    response = response_result["response"]
                                    
                                    # Send the response to speak ONLY if we have a complete response
                                    if response and response.strip():
                                        print(f"🎤 SPEAKING FINAL RESPONSE: {response[:100]}...")
                                        
                                        # Send assistant response to frontend
                                        try:
                                            response_data = {
                                                "type": "conversation", 
                                                "role": "assistant",
                                                "text": response
                                            }
                                            await ctx.room.local_participant.publish_data(
                                                json.dumps(response_data).encode(),
                                                reliable=True
                                            )
                                        except Exception as e:
                                            logger.error(f"Failed to send assistant response to frontend: {e}")
                                        
                                        # Speak the final response after search notification (if any) has completed
                                        await session.say(response)
                                        
                                except Exception as e:
                                    logger.error(f"Error in response generation: {e}")
                                    error_response = "I'm sorry, I encountered an error processing your request."
                                    await session.say(error_response)
                    
                    # Start the response handling
                    asyncio.create_task(handle_response_with_tools())
            
            # Start the delayed processing
            asyncio.create_task(process_after_delay())
    
    @ctx.room.on("data_received")
    def on_data_received(data: rtc.DataPacket):
        """Handle data messages from frontend (pause/resume)"""
        nonlocal is_paused
        try:
            message = json.loads(data.data.decode())
            action = message.get('action')
            
            if action == 'pause':
                is_paused = True
                session.interrupt()
            elif action == 'resume':
                is_paused = False
                if message.get('requestGreeting', False) and not is_paused:
                    asyncio.create_task(session.say("Hi again!"))
        except Exception as e:
            logger.error(f"Failed to parse data message: {e}")


def main():
    """Run the voice agent worker"""
    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]
    if not all(os.getenv(var) for var in required_vars):
        raise ValueError(f"Missing required environment variables: {', '.join(required_vars)}")
    
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        prewarm_fnc=prewarm,
    ))


if __name__ == "__main__":
    main()
