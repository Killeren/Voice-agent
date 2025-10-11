# Voice-agent
AI Voice Assistant with Web Interface using Livekit and Cerebras

An interactive AI voice assistant that you can talk to directly in your browser. Built with Livekit for real-time audio communication and Cerebras for fast AI responses.

## Features

- 🎙️ Real-time voice interaction with AI
- 🌐 Web-based interface - no installation required for users
- 🚀 Fast AI responses powered by Cerebras
- 🎯 Voice Activity Detection (VAD) for natural conversations
- 📝 Speech-to-Text using Deepgram
- 🔊 Text-to-Speech using OpenAI TTS
- 🔒 Secure token-based authentication

## Architecture

- **Frontend**: HTML/CSS/JavaScript with Livekit Client SDK
- **Backend**: Python with aiohttp web server
- **Voice Agent**: Python with Livekit Agents SDK
- **LLM**: Cerebras API for fast inference
- **STT**: Deepgram for speech recognition
- **TTS**: OpenAI for voice synthesis

## Prerequisites

- Python 3.8 or higher
- Livekit server (local or cloud)
- API keys for:
  - Livekit (API key and secret)
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

### Livekit
1. Sign up at [Livekit Cloud](https://cloud.livekit.io/) or set up a local server
2. Create a new project and get your API credentials
3. For local development, you can run Livekit server with Docker:
```bash
docker run -d -p 7880:7880 -p 7881:7881 livekit/livekit-server --dev
```

### Cerebras
1. Sign up at [Cerebras Inference](https://inference.cerebras.ai/)
2. Get your API key from the dashboard

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

This will start the Livekit agent that handles voice interactions.

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
4. Start speaking - the AI will respond to you!
5. Use the microphone and speaker toggles to control audio
6. Click "Disconnect" when you're done

## Development

### Project Structure

```
Voice-agent/
├── agent.py              # Livekit voice agent with Cerebras LLM
├── server.py             # Web server for frontend and token generation
├── index.html            # Main web interface
├── static/
│   ├── style.css        # Styles for the web interface
│   └── app.js           # JavaScript for Livekit client
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

### Customization

#### Changing the AI's Personality

Edit the system message in `agent.py`:
```python
ChatMessage(
    role="system",
    content="Your custom instructions here..."
)
```

#### Changing the Voice

Modify the TTS configuration in `agent.py`:
```python
tts_plugin = openai.TTS(
    model="tts-1",
    voice="alloy",  # Options: alloy, echo, fable, onyx, nova, shimmer
)
```

#### Changing the LLM Model

Update the model in `agent.py`:
```python
llm = CerebrasLLM(api_key=cerebras_api_key, model="llama3.1-70b")
```

## Troubleshooting

### Microphone not working
- Check browser permissions for microphone access
- Ensure you're using HTTPS (or localhost)
- Try a different browser (Chrome/Edge recommended)

### Connection issues
- Verify your Livekit server is running
- Check that all API keys are correctly set in `.env`
- Review logs in the terminal for error messages

### Audio quality issues
- Ensure stable internet connection
- Try reducing background noise
- Check microphone settings in your OS

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
