# Voice-agent
AI Voice Assistant with Web Interface using LiveKit Agents 1.2+ and Cerebras

> ⚡ **Updated for LiveKit Agents 1.2+ API** - Now with native Cerebras integration for 70x faster inference!

An interactive AI voice assistant that you can talk to directly in your browser. Built with LiveKit for real-time audio communication and Cerebras for ultra-fast AI responses.

## 🚀 What's New (v2.0)

- **LiveKit Agents 1.2+ API**: Modern AgentSession architecture
- **Native Cerebras Integration**: No custom wrappers needed
- **70x Faster Inference**: Sub-50ms response times
- **Enhanced Features**: Advanced turn detection, noise cancellation, false interruption handling
- **Production Ready**: Improved error handling and performance optimizations

## Features

- 🎙️ Real-time voice interaction with AI
- 🌐 Web-based interface - no installation required for users
- ⚡ Ultra-fast AI responses powered by Cerebras (2,100+ tokens/sec)
- 🎯 Advanced Voice Activity Detection (VAD) with prewarming
- 📝 Speech-to-Text using Deepgram Nova-2
- 🔊 Text-to-Speech using OpenAI TTS
- 🔒 Secure token-based authentication
- 🛡️ Built-in noise cancellation
- 🌍 Multilingual turn detection
- 🔄 False interruption detection and auto-resume

## Architecture

- **Frontend**: HTML/CSS/JavaScript with LiveKit Client SDK
- **Backend**: Python with aiohttp web server
- **Voice Agent**: Python with LiveKit Agents 1.2+ SDK
- **LLM**: Cerebras API via native LiveKit integration
- **STT**: Deepgram Nova-2 for speech recognition
- **TTS**: OpenAI for voice synthesis

## Prerequisites

- Python 3.8 or higher
- LiveKit server (local or cloud)
- API keys for:
  - LiveKit (API key and secret)
  - Cerebras (API key)
  - Deepgram (API key)
  - OpenAI (API key for TTS)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Killeren/Voice-agent.git
cd Voice-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
CEREBRAS_API_KEY=your_cerebras_key
DEEPGRAM_API_KEY=your_deepgram_key
OPENAI_API_KEY=your_openai_key
```

## Getting API Keys

### LiveKit
1. Sign up at [LiveKit Cloud](https://cloud.livekit.io/) or set up a local server
2. Create a new project and get your API credentials
3. For local development, you can run LiveKit server with Docker:
```bash
docker run -d -p 7880:7880 -p 7881:7881 livekit/livekit-server --dev
```

### Cerebras
1. Sign up at [Cerebras Inference](https://inference.cerebras.ai/)
2. Get your API key from the dashboard
3. Enjoy 70x faster inference speeds!

### Deepgram
1. Sign up at [Deepgram](https://deepgram.com/)
2. Get your API key from the console

### OpenAI
1. Sign up at [OpenAI](https://platform.openai.com/)
2. Get your API key from the API section

## Usage

### Running the Voice Agent

Start the voice agent worker:
```bash
python agent.py dev
```

This will start the LiveKit agent that handles voice interactions with prewarming for optimal performance.

### Running the Web Server

In a separate terminal, start the web server:
```bash
python server.py
```

The web interface will be available at `http://localhost:8080`

### Using the Interface

1. Open your browser and navigate to `http://localhost:8080`
2. Click the "Connect" button to join the voice session
3. Allow microphone permissions when prompted
4. Start speaking - the AI will respond to you with lightning-fast speeds!
5. Use the microphone and speaker toggles to control audio
6. Click "Disconnect" when you're done

## Migration from v1.0

**Upgrading from the old version?** Check out our [Migration Guide](MIGRATION_GUIDE.md) for detailed instructions on updating to the new LiveKit Agents 1.2+ API.

## Development

### Project Structure

```
Voice-agent/
├── agent.py              # LiveKit voice agent with native Cerebras integration
├── server.py             # Web server for frontend and token generation
├── index.html            # Main web interface
├── static/
│   ├── style.css        # Styles for the web interface
│   └── app.js           # JavaScript for LiveKit client
├── requirements.txt     # Python dependencies (updated for v1.2+)
├── MIGRATION_GUIDE.md   # Migration guide from v1.0
├── .env.example        # Environment variables template
└── README.md           # This file
```

### Customization

#### Changing the AI's Personality

Edit the instructions in `agent.py`:
```python
agent = Agent(
    instructions="Your custom instructions here..."
)
```

#### Changing the Voice

Modify the TTS configuration in `agent.py`:
```python
tts=openai.TTS(
    model="tts-1",
    voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
    speed=1.0,
)
```

#### Changing the LLM Model

Update the model in `agent.py`:
```python
llm=openai.LLM.with_cerebras(
    model="llama3.1-70b",  # Or llama3.1-8b for faster responses
    temperature=0.7,
    max_tokens=1024,
)
```

#### Performance Tuning

```python
session = AgentSession(
    # Interruption settings
    allow_interruptions=True,
    int_min_words=0,                    # Allow immediate interruption
    int_speech_duration=0.5,            # 500ms before interruption
    
    # False interruption detection
    false_interruption_timeout=3.0,     # Wait 3s before resuming
    resume_false_interruption=True,     # Auto-resume
)
```

## Performance

### Cerebras Speed Benefits

- **70x faster** than GPU-based solutions
- **Sub-50ms response times** for Llama 3.1 70B
- **2,100+ tokens/second** generation speed
- **Original 16-bit precision** (no quality loss)

### LiveKit Agents 1.2+ Features

- **Prewarming**: Models loaded before first request
- **Advanced Turn Detection**: ML-based conversation flow
- **False Interruption Detection**: Handles spurious audio triggers
- **Enhanced Noise Cancellation**: Built-in background noise removal

## Troubleshooting

### Microphone not working
- Check browser permissions for microphone access
- Ensure you're using HTTPS (or localhost)
- Try a different browser (Chrome/Edge recommended)

### Connection issues
- Verify your LiveKit server is running and compatible with Agents 1.2+
- Check that all API keys are correctly set in `.env`
- Review logs in the terminal for error messages

### Performance issues
- Ensure Cerebras API key has sufficient credits
- Check internet connection stability
- Try adjusting interruption settings in `agent.py`

### Debug Mode

```bash
# Run with debug logging
LIVEKIT_LOG_LEVEL=debug python agent.py dev
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.

## Changelog

### v2.0.0 (Latest)
- Updated to LiveKit Agents 1.2+ API
- Native Cerebras integration
- Enhanced performance and reliability
- Advanced turn detection and noise cancellation
- Production-ready configuration

### v1.0.0
- Initial release with custom Cerebras wrapper
- Basic VoiceAssistant implementation