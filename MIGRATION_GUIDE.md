# Voice Agent - Migration to LiveKit Agents 1.2+ and Cerebras Integration

## 🚀 What's New

This updated version of the voice agent leverages the latest LiveKit Agents 1.2+ API and integrates directly with Cerebras for ultra-fast inference speeds (up to 70x faster than GPU solutions).

### Key Improvements

1. **LiveKit Agents 1.2+ API**: Updated to use `AgentSession` instead of deprecated `VoiceAssistant`
2. **Native Cerebras Integration**: Direct integration via `openai.LLM.with_cerebras()` 
3. **Enhanced Performance**: Prewarming, optimized turn detection, and false interruption handling
4. **Production Ready**: Better error handling, logging, and worker configuration
5. **Advanced Features**: Noise cancellation, multilingual turn detection, auto-resume

## 📋 Migration Steps

### 1. Update Dependencies

Replace your old `requirements.txt` with the new one:

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Your `.env` file should now include:

```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Cerebras Configuration (replaces custom implementation)
CEREBRAS_API_KEY=your_cerebras_key

# Speech Services
DEEPGRAM_API_KEY=your_deepgram_key
OPENAI_API_KEY=your_openai_key
```

### 3. Run the Updated Agent

```bash
# Start the agent in development mode
python agent.py dev

# Or in production mode
python agent.py start
```

## 🔄 API Changes Breakdown

### Old vs New Architecture

**Old Implementation (VoiceAssistant)**:
```python
from livekit.agents.voice_assistant import VoiceAssistant

# Custom Cerebras wrapper required
class CerebrasLLM:
    # Custom implementation...

assistant = VoiceAssistant(
    vad=silero.VAD.load(),
    stt=stt,
    llm=llm,  # Custom wrapper
    tts=tts_plugin,
    chat_ctx=initial_ctx,
)
assistant.start(ctx.room)
```

**New Implementation (AgentSession)**:
```python
from livekit.agents import AgentSession, Agent
from livekit.plugins import openai

# Native Cerebras support
session = AgentSession(
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=openai.LLM.with_cerebras(model="llama3.1-70b"),  # Native integration!
    tts=openai.TTS(),
    turn_detection=MultilingualModel(),
)

await session.start(
    agent=Agent(instructions="..."),
    room=ctx.room,
)
```

### Benefits of the Update

1. **Faster Integration**: No need for custom Cerebras wrapper
2. **Better Performance**: Native optimizations and prewarming
3. **Enhanced Features**: Advanced turn detection, noise cancellation
4. **Production Ready**: Better error handling, auto-resume on false interruptions
5. **Future Proof**: Uses latest stable API that won't be deprecated

## 🛠️ Configuration Options

### Cerebras Model Options

```python
# Available Cerebras models via LiveKit
llm=openai.LLM.with_cerebras(
    model="llama3.1-70b",      # Recommended for best performance
    # model="llama3.1-8b",     # Faster but less capable
    # model="llama-3.3-70b",   # Latest model
    temperature=0.7,
    max_tokens=1024,
)
```

### Performance Tuning

```python
session = AgentSession(
    # Interruption handling
    allow_interruptions=True,
    int_min_words=0,                    # Allow immediate interruption
    int_speech_duration=0.5,            # 500ms before interruption
    
    # False interruption detection
    false_interruption_timeout=3.0,     # Wait 3s before resuming
    resume_false_interruption=True,     # Auto-resume
    
    # Turn detection sensitivity
    turn_detection=MultilingualModel(
        min_silence_duration=0.5,       # Minimum silence to detect turn end
    ),
)
```

## 🚀 Performance Improvements

### Cerebras Speed Benefits

- **70x faster** than GPU-based solutions
- **Sub-50ms response times** for Llama 3.1 70B
- **2,100+ tokens/second** generation speed
- **Original 16-bit precision** (no quality loss from quantization)

### LiveKit Agents 1.2+ Features

- **Prewarming**: Models loaded before first request
- **False Interruption Detection**: Handles spurious audio triggers
- **Advanced Turn Detection**: ML-based conversation flow
- **Enhanced Noise Cancellation**: Built-in background noise removal

## 🔧 Troubleshooting

### Common Migration Issues

1. **Import Errors**: Make sure to install all new dependencies
2. **Cerebras API Key**: Ensure `CEREBRAS_API_KEY` is set correctly
3. **Model Names**: Use correct Cerebras model identifiers
4. **LiveKit Server**: Ensure compatible with Agents 1.2+

### Debug Mode

```bash
# Run with debug logging
LIVEKIT_LOG_LEVEL=debug python agent.py dev
```

## 📚 Additional Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [Cerebras Inference API](https://inference-docs.cerebras.ai/)
- [LiveKit Cloud](https://livekit.io/)

## 🤝 Support

If you encounter issues during migration, check:
1. All environment variables are set correctly
2. Dependencies are installed with correct versions
3. LiveKit server is compatible with Agents 1.2+
4. Cerebras API key has sufficient credits

The new implementation is more robust, faster, and production-ready compared to the original version.