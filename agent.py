"""
AI Voice Agent using LiveKit Agents 1.0+ and Cerebras Inference API with Function Calling
"""

import asyncio
import logging
import os
import json
import aiohttp
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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


async def send_email_tool(recipient_email: str, subject: str, message_body: str) -> str:
    """Send an email using SMTP - used as a tool by the LLM"""
    try:
        # Get email configuration from environment variables
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        
        if not sender_email or not sender_password:
            return "Email configuration not found. Please set SENDER_EMAIL and SENDER_PASSWORD environment variables."
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, recipient_email):
            return f"Invalid email address format: {recipient_email}"
        
        print(f"🔧 TOOL CALLED: send_email_tool('{recipient_email}', '{subject}', '{message_body[:50]}...')")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(message_body, 'plain'))
        
        # Gmail SMTP configuration
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable security
        server.login(sender_email, sender_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        print(f"✅ EMAIL SENT successfully to {recipient_email}")
        return f"Email sent successfully to {recipient_email}"
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Email authentication failed")
        return "Email authentication failed. Please check your email credentials."
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"Email recipient refused: {recipient_email}")
        return f"Email address rejected: {recipient_email}"
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        return f"Failed to send email: {str(e)}"


def normalize_email_from_speech(text: str) -> str:
    """Normalize email addresses from speech-to-text conversion"""
    import re
    
    # Common speech-to-text patterns
    text = text.lower()
    
    # Specific handling for common email patterns
    if "arjan" in text and ("84" in text or "eighty" in text):
        # Handle variations of arjanvaily84@gmail.com
        arjan_patterns = [
            r'a\s*r\s*j\s*a\s*n\s*v\s*a?\s*[il]\s*l?\s*y\s*(eighty\s*four|84|eighty\s*4|eighty\s*for)',
            r'arjan\s*v?\s*[ai]\s*[il]\s*l?\s*y\s*(eighty\s*four|84|eighty\s*4)'
        ]
        
        for pattern in arjan_patterns:
            if re.search(pattern, text):
                return "arjanvaily84@gmail.com"
    
    # Replace common speech patterns
    replacements = {
        " at gmail dot com": "@gmail.com",
        " at gmail dot": "@gmail.com", 
        " at g mail dot com": "@gmail.com",
        " at yahoo dot com": "@yahoo.com",
        " at outlook dot com": "@outlook.com",
        " at hotmail dot com": "@hotmail.com",
        "eighty four": "84",
        "eighty-four": "84",
        "eighty 4": "84",
        "eighty for": "84",
        " dot ": ".",
        " at ": "@",
        "gmail dot": "gmail.",
        "g mail": "gmail"
    }
    
    for pattern, replacement in replacements.items():
        text = text.replace(pattern, replacement)
    
    # Remove extra spaces
    text = re.sub(r'\s+', '', text)
    
    # Extract email pattern
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    
    return match.group(0) if match else text


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
            },
            "send_email": {
                "function": send_email_tool,
                "description": "Send an email to a specified recipient. Use this when the user wants to send an email. Always confirm the email address with the user before sending.",
                "parameters": {
                    "recipient_email": "The email address to send to",
                    "subject": "The subject line of the email",
                    "message_body": "The content/body of the email"
                }
            }
        }
    
    async def generate_response(self, messages, instructions=None, stored_email=None):
        """Generate response with tool calling capability"""
        
        # First, check if the user's question needs current information
        tool_check_instructions = f"""
{instructions or "You are a helpful AI voice assistant."}

IMPORTANT: Analyze the user's question and determine what tool is needed. Consider the FULL conversation context.

STORED EMAIL: {stored_email if stored_email else "None"}

If the user's question requires current/recent information (like latest news, recent releases, current events, stock prices, weather, etc.), 
respond with EXACTLY this format:
TOOL_CALL: search_perplexity
QUERY: [search query here]

If the user wants to send an email, respond with EXACTLY this format:
TOOL_CALL: send_email
RECIPIENT: [use stored email if available and no specific recipient mentioned, otherwise extract email from speech]
SUBJECT: [suggested subject based on conversation]
MESSAGE: [email content based on user's request]

IMPORTANT EMAIL PARSING RULES:
- "arjanvaily84@gmail.com" variations should be normalized  
- Listen for patterns like "a r j a n v a i l y eighty four at gmail dot com"
- Common speech-to-text errors: "at Gmail dot" = "@gmail.com", "eighty four" = "84"
- If email sounds like "arjanvaily" + number + "@gmail.com", parse as arjanvaily[number]@gmail.com
- Use stored email when user says "send me an email" or "to the email address" without specifying
- Extract email from current message OR use stored email if available

If it's a general knowledge question that doesn't need tools, respond with:
NO_TOOL_NEEDED

Examples:
- "What's OpenAI's latest model?" → TOOL_CALL: search_perplexity\nQUERY: OpenAI latest model release
- "Send email about market" (with stored email) → TOOL_CALL: send_email\nRECIPIENT: [stored_email]\nSUBJECT: Market Information\nMESSAGE: [content]
- "Send to a r j a n v a i l y eighty four at gmail dot com" → TOOL_CALL: send_email\nRECIPIENT: arjanvaily84@gmail.com\nSUBJECT: [subject]\nMESSAGE: [message]
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
        if "TOOL_CALL:" in tool_decision:
            try:
                lines = tool_decision.split('\n')
                
                if "search_perplexity" in tool_decision:
                    # Handle search tool
                    query_line = [line for line in lines if line.startswith('QUERY:')]
                    if query_line:
                        query = query_line[0].replace('QUERY:', '').strip()
                        print(f"🔧 LLM REQUESTED TOOL: search_perplexity('{query}')")
                        
                        # Call the tool
                        tool_result = await search_perplexity_tool(query)
                        
                        # Generate final response with tool results
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
                
                elif "send_email" in tool_decision:
                    # Handle email tool
                    recipient_line = [line for line in lines if line.startswith('RECIPIENT:')]
                    subject_line = [line for line in lines if line.startswith('SUBJECT:')]
                    message_line = [line for line in lines if line.startswith('MESSAGE:')]
                    
                    if recipient_line and subject_line and message_line:
                        recipient = recipient_line[0].replace('RECIPIENT:', '').strip()
                        subject = subject_line[0].replace('SUBJECT:', '').strip()
                        message_body = message_line[0].replace('MESSAGE:', '').strip()
                        
                        # Normalize email from speech if it's not already stored
                        if recipient == "ASK_USER":
                            # Check if we have stored email first
                            if stored_email:
                                recipient = stored_email
                            else:
                                # Try to extract email from the original user message
                                original_message = messages[-1]["content"]
                                normalized_email = normalize_email_from_speech(original_message)
                                if "@" in normalized_email and len(normalized_email) > 5:
                                    recipient = normalized_email
                        elif recipient != "ASK_USER" and "@" not in recipient:
                            # Try to extract email from the original user message
                            original_message = messages[-1]["content"]
                            normalized_email = normalize_email_from_speech(original_message)
                            if "@" in normalized_email and len(normalized_email) > 5:
                                recipient = normalized_email
                        
                        print(f"🔧 LLM REQUESTED TOOL: send_email('{recipient}', '{subject}', '{message_body[:30]}...')")
                        
                        return {
                            "response": "",  # Will be set based on flow
                            "used_search": False,
                            "search_notification": None,
                            "email_request": {
                                "recipient": recipient,
                                "subject": subject,
                                "message": message_body,
                                "needs_processing": True
                            }
                        }
                    
            except Exception as e:
                logger.error(f"Tool calling error: {e}")
                return {
                    "response": "I encountered an error processing your request. Please try again.",
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
            "When you use search tools and find current information, mention that it's recent information."
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
    
    # Store user email and pending email data
    user_email = None
    pending_email_data = None
    conversation_history = []
    
    await session.start(agent=agent, room=ctx.room)
    
    # Send initial greeting since we disabled automatic LLM
    initial_greeting = "Hello! I'm your AI voice agent ready to help with questions or find current information."
    await session.say(initial_greeting)
    
    @session.on("user_input_transcribed")
    def on_user_transcribed(event):
        """Handle user transcription and generate response with tools"""
        nonlocal transcript_buffer, last_transcript_time, pending_email_data, user_email, conversation_history
        
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
                        nonlocal pending_email_data, user_email, conversation_history
                        async with processing_lock:
                            if not is_paused:
                                user_query = current_buffer
                                print(f"🤖 PROCESSING with tools: {user_query}")
                                
                                try:
                                    # Check if this is a confirmation for pending email
                                    if pending_email_data and pending_email_data.get("awaiting_confirmation"):
                                        user_lower = user_query.lower()
                                        if any(word in user_lower for word in ["yes", "yeah", "sure", "okay", "ok", "proceed", "send", "go ahead"]):
                                            # User confirmed - send the email
                                            await handle_confirmed_email(pending_email_data)
                                            pending_email_data = None
                                            return
                                        elif any(word in user_lower for word in ["no", "nope", "cancel", "don't", "stop"]):
                                            # User cancelled
                                            pending_email_data = None
                                            await session.say("Okay, I've cancelled the email.")
                                            return
                                    
                                    # Add to conversation history
                                    conversation_history.append({"role": "user", "content": user_query})
                                    
                                    # Keep last 10 messages for context (5 exchanges)
                                    if len(conversation_history) > 10:
                                        conversation_history = conversation_history[-10:]
                                    
                                    # Build conversation context with history
                                    messages = conversation_history.copy()
                                    
                                    # Generate response using our custom LLM with tools
                                    response_result = await custom_llm.generate_response(
                                        messages, 
                                        instructions=agent.instructions,
                                        stored_email=user_email
                                    )
                                    
                                    # Handle search notification first if needed
                                    if response_result["used_search"] and response_result["search_notification"]:
                                        print(f"🔍 IMMEDIATE SEARCH NOTIFICATION: {response_result['search_notification']}")
                                        await session.say(response_result["search_notification"])
                                        # Small delay to ensure search notification completes
                                        await asyncio.sleep(1.0)
                                    
                                    # Handle email requests
                                    if "email_request" in response_result:
                                        email_req = response_result["email_request"]
                                        if email_req["needs_processing"]:
                                            await handle_email_request(email_req)
                                        return
                                    
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
                                        
                                        # Add response to conversation history
                                        conversation_history.append({"role": "assistant", "content": response})
                                        
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
        """Handle data messages from frontend (pause/resume/email)"""
        nonlocal is_paused, user_email, pending_email_data
        
        async def handle_data_message():
            nonlocal is_paused, user_email, pending_email_data
            try:
                message = json.loads(data.data.decode())
                action = message.get('action')
                
                if action == 'pause':
                    is_paused = True
                    session.interrupt()
                elif action == 'resume':
                    is_paused = False
                    if message.get('requestGreeting', False) and not is_paused:
                        await session.say("Hi again!")
                elif action == 'store_email':
                    # Store user's email address
                    user_email = message.get('email')
                    print(f"📧 STORED USER EMAIL: {user_email}")
                    
                    # Send confirmation back to frontend
                    try:
                        confirmation_data = {
                            "type": "email_stored",
                            "email": user_email
                        }
                        await ctx.room.local_participant.publish_data(
                            json.dumps(confirmation_data).encode(),
                            reliable=True
                        )
                    except Exception as e:
                        logger.error(f"Failed to send email confirmation to frontend: {e}")
                elif action == 'provide_email':
                    # Use provided email for pending email operation
                    if pending_email_data:
                        provided_email = message.get('email')
                        if provided_email:
                            pending_email_data['recipient'] = provided_email
                            # Process the pending email
                            await handle_confirmed_email(pending_email_data)
                            pending_email_data = None
            except Exception as e:
                logger.error(f"Failed to parse data message: {e}")
        
        # Start the async handler
        asyncio.create_task(handle_data_message())
    
    async def handle_confirmed_email(email_data):
        """Handle confirmed email sending"""
        try:
            recipient = email_data.get('recipient')
            subject = email_data.get('subject')
            message_body = email_data.get('message')
            
            # Send the email
            result = await send_email_tool(recipient, subject, message_body)
            
            # Provide feedback to user
            if "successfully" in result.lower():
                await session.say(f"Email sent successfully to {recipient}!")
            else:
                await session.say(f"I encountered an issue sending the email: {result}")
                
        except Exception as e:
            logger.error(f"Error handling confirmed email: {e}")
            await session.say("I'm sorry, there was an error sending the email.")
    
    async def handle_email_request(email_req):
        """Handle email request workflow"""
        nonlocal pending_email_data, user_email
        
        recipient = email_req["recipient"]
        subject = email_req["subject"]
        message = email_req["message"]
        
        # If no recipient specified, check if we have stored email
        if recipient == "ASK_USER":
            if user_email:
                # Use stored email
                recipient = user_email
                confirmation_msg = f"I'll send an email to your stored address {user_email} with the subject '{subject}'. Should I proceed?"
            else:
                # Ask for email
                confirmation_msg = "I'd be happy to send an email for you. Could you please provide the recipient's email address?"
                pending_email_data = {
                    "subject": subject,
                    "message": message,
                    "needs_recipient": True
                }
        else:
            # Validate email format before proceeding
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, recipient):
                # Invalid email format
                confirmation_msg = f"The email address '{recipient}' doesn't appear to be valid. Could you please provide a correct email address?"
                pending_email_data = {
                    "subject": subject,
                    "message": message,
                    "needs_recipient": True
                }
            else:
                # Confirm with provided recipient
                confirmation_msg = f"I'm about to send an email to {recipient} with the subject '{subject}'. Should I proceed?"
        
        # Store pending email data for confirmation
        if (recipient != "ASK_USER" and re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', recipient)) or user_email:
            pending_email_data = {
                "recipient": recipient if recipient != "ASK_USER" else user_email,
                "subject": subject,
                "message": message,
                "awaiting_confirmation": True
            }
        
        # Send confirmation message
        try:
            response_data = {
                "type": "conversation", 
                "role": "assistant",
                "text": confirmation_msg
            }
            await ctx.room.local_participant.publish_data(
                json.dumps(response_data).encode(),
                reliable=True
            )
        except Exception as e:
            logger.error(f"Failed to send email confirmation to frontend: {e}")
        
        # Speak the confirmation
        await session.say(confirmation_msg)


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
