"""
AI Voice Agent using Livekit and Cerebras
"""

import asyncio
import logging
import os
from typing import Annotated

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, tokenize, tts
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai, silero

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CerebrasLLM:
    """Custom LLM wrapper for Cerebras API"""
    
    def __init__(self, api_key: str, model: str = "llama3.1-8b"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.cerebras.ai/v1"
        
    async def chat(
        self,
        chat_ctx: ChatContext,
        fnc_ctx: None = None,
    ) -> "LLMStream":
        """Generate chat completion using Cerebras API"""
        import aiohttp
        
        messages = []
        for msg in chat_ctx.messages:
            role = msg.role
            if role == "model":
                role = "assistant"
            messages.append({
                "role": role,
                "content": msg.content
            })
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": 1024,
            "temperature": 0.7
        }
        
        return LLMStream(self.base_url, headers, data)


class LLMStream:
    """Stream handler for Cerebras LLM responses"""
    
    def __init__(self, base_url: str, headers: dict, data: dict):
        self.base_url = base_url
        self.headers = headers
        self.data = data
        self._session = None
        self._response = None
        
    async def __aiter__(self):
        import aiohttp
        import json
        
        self._session = aiohttp.ClientSession()
        try:
            self._response = await self._session.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=self.data
            )
            
            async for line in self._response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    line = line[6:]
                    if line == '[DONE]':
                        break
                    try:
                        chunk = json.loads(line)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            content = delta.get('content', '')
                            if content:
                                yield ChatChunk(content=content)
                    except json.JSONDecodeError:
                        continue
        finally:
            if self._response:
                self._response.close()
            if self._session:
                await self._session.close()


class ChatChunk:
    """Represents a chunk of LLM response"""
    
    def __init__(self, content: str):
        self.choices = [type('Choice', (), {
            'delta': type('Delta', (), {
                'content': content,
                'role': 'assistant'
            })()
        })()]


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent"""
    
    logger.info(f"Connecting to room: {ctx.room.name}")
    
    # Initialize speech-to-text
    stt = deepgram.STT(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
    )
    
    # Initialize text-to-speech
    tts_plugin = openai.TTS(
        model="tts-1",
        voice="alloy",
    )
    
    # Initialize Cerebras LLM
    cerebras_api_key = os.getenv("CEREBRAS_API_KEY")
    if not cerebras_api_key:
        logger.error("CEREBRAS_API_KEY not found in environment")
        return
        
    llm = CerebrasLLM(api_key=cerebras_api_key)
    
    # Create initial chat context
    initial_ctx = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content=(
                    "You are a helpful AI voice assistant. "
                    "Keep your responses concise and conversational. "
                    "You are speaking, not writing, so avoid using special characters or formatting."
                )
            )
        ]
    )
    
    # Create voice assistant
    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=stt,
        llm=llm,
        tts=tts_plugin,
        chat_ctx=initial_ctx,
    )
    
    # Start the assistant
    assistant.start(ctx.room)
    
    # Greet the user
    await assistant.say("Hello! I'm your AI voice assistant. How can I help you today?", allow_interruptions=True)
    
    logger.info("Voice assistant started successfully")


def main():
    """Run the voice agent worker"""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )


if __name__ == "__main__":
    main()
