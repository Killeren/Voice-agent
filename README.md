# Voice Agent
AI Voice Assistant with Web Interface using LiveKit Agents 1.2+ and Cerebras

> ⚡ **Updated for LiveKit Agents 1.2+ API** - Now with native Cerebras integration and free Edge TTS!

An interactive AI voice assistant that you can talk to directly in your browser. Built with LiveKit for real-time audio communication, Cerebras for ultra-fast AI responses, and Microsoft Edge TTS for free, high-quality voice synthesis.

## 🚀 Features

- 🎙️ **Real-time voice interaction** with AI
- 🌐 **Web-based interface** - no installation required for users
- ⚡ **Ultra-fast AI responses** powered by Cerebras (70x faster, 2,100+ tokens/sec)
- 🎯 **Advanced Voice Activity Detection** (VAD) with prewarming
- 📝 **Speech-to-Text** using Deepgram Nova-2
- 🔊 **Free Text-to-Speech** using Microsoft Edge TTS (26+ voices) with gTTS fallback
- 🔒 **Secure token-based authentication**
- 🛡️ **Built-in noise cancellation**
- 🌍 **Multilingual turn detection**
- 🔄 **False interruption detection** and auto-resume

## 📋 What's New (v2.0)

- **LiveKit Agents 1.2+ API**: Modern AgentSession architecture
- **Native Cerebras Integration**: No custom wrappers needed
- **Free TTS Solution**: Microsoft Edge TTS replaces paid services (saves $15/million chars)
- **70x Faster Inference**: Sub-50ms response times
- **Enhanced Features**: Advanced turn detection, noise cancellation
- **Production Ready**: Improved error handling and performance optimizations

## 🏗️ Architecture

- **Frontend**: HTML/CSS/JavaScript with LiveKit Client SDK
- **Backend**: Python with aiohttp web server
- **Voice Agent**: Python with LiveKit Agents 1.2+ SDK
- **LLM**: Cerebras API via native LiveKit integration
- **STT**: Deepgram Nova-2 for speech recognition
- **TTS**: Microsoft Edge TTS (free) with gTTS fallback

## 📂 Project Structure

```
Voice-agent/
├── agent.py                 # Main AI voice agent
├── server.py                # Web server and token generator
├── edge_tts_plugin.py       # Custom Edge TTS wrapper
├── index.html               # Web interface
├── static/
│   ├── app.js              # JavaScript client
│   └── style.css           # Web interface styling
├── requirements.txt         # Python dependencies
└── README.md               # This documentation
```

## 🛠️ Prerequisites

- **Python 3.8+** installed
- **FFmpeg** for audio processing:
  ```bash
  # macOS
  brew install ffmpeg
  
  # Ubuntu/Debian
  sudo apt install ffmpeg
  
  # Windows
  # Download from https://ffmpeg.org/download.html
  ```
- **Modern web browser** (Chrome, Firefox, or Edge)

## 🔑 API Keys Required

You'll need API keys from these services:

### 1. LiveKit (Required)
- **Option A**: LiveKit Cloud at [cloud.livekit.io](https://cloud.livekit.io/)
- **Option B**: Local Docker setup:
  ```bash
  docker run -d -p 7880:7880 -p 7881:7881 \
    -e LIVEKIT_KEYS="devkey: devsecret" \
    livekit/livekit-server --dev
  ```

### 2. Cerebras (Required)
- Sign up at [inference.cerebras.ai](https://inference.cerebras.ai/)
- Get your API key from the dashboard

### 3. Deepgram (Required) 
- Sign up at [deepgram.com](https://deepgram.com/)
- Get your API key from the console

### 4. Perplexity (Optional)
- Sign up at [perplexity.ai](https://www.perplexity.ai/) for web search capabilities

**Note**: OpenAI TTS is NO LONGER required - we use free Edge TTS!

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd Voice-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with your API keys:
```env
# LiveKit Configuration
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=devsecret

# AI Services
CEREBRAS_API_KEY=your_cerebras_key_here
DEEPGRAM_API_KEY=your_deepgram_key_here

# Optional: Web search
PERPLEXITY_API_KEY=your_perplexity_key_here
```

For production, use your actual LiveKit Cloud credentials:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_actual_api_key
LIVEKIT_API_SECRET=your_actual_secret
```

### 3. Run the Application

**Terminal 1 - Start Voice Agent:**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python agent.py dev
```
Wait for: "Voice assistant started successfully"

**Terminal 2 - Start Web Server:**
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python server.py
```
Wait for: "Starting web server on http://localhost:8080"

### 4. Use the Interface
1. Open browser to `http://localhost:8080`
2. Click **"Connect"** button
3. Allow microphone access when prompted
4. Start talking! The AI will respond with voice

## 🎛️ Customization

### Change AI Personality
Edit the instructions in `agent.py`:
```python
agent = Agent(
    instructions="You are a helpful assistant. Be concise and friendly."
)
```

### Change Voice (26+ Options Available)
Edit the TTS configuration in `agent.py`:
```python
from edge_tts_plugin import EdgeTTS

tts = EdgeTTS(
    voice="en-US-AriaNeural",    # Female, friendly
    # voice="en-US-GuyNeural",   # Male, casual  
    # voice="en-GB-SoniaNeural", # Female, British
    rate="+10%",                 # Speak 10% faster
    use_fallback=True            # Use gTTS if Edge TTS fails
)
```

**Available Voices:**
- `en-US-AriaNeural` - Female, friendly
- `en-US-GuyNeural` - Male, casual
- `en-US-JennyNeural` - Female, professional
- `en-GB-SoniaNeural` - Female, British
- `en-AU-NatashaNeural` - Female, Australian
- And 20+ more options!

### Change LLM Model
Update the model in `agent.py`:
```python
llm = openai.LLM.with_cerebras(
    model="llama3.1-70b",        # Or "llama3.1-8b" for faster responses
    temperature=0.7,
    max_tokens=1024,
)
```

### Performance Tuning
```python
session = AgentSession(
    allow_interruptions=True,
    int_min_words=0,                    # Allow immediate interruption
    int_speech_duration=0.5,            # 500ms before interruption
    false_interruption_timeout=3.0,     # Wait 3s before resuming
    resume_false_interruption=True,     # Auto-resume after false interruption
)
```

## 🚀 Production Deployment

### Using systemd (Linux)

1. **Deploy to server:**
   ```bash
   # On Ubuntu/Debian server
   sudo apt update && sudo apt install python3.10 python3.10-venv nginx -y
   cd /opt
   sudo git clone <your-repo> voice-agent
   cd voice-agent
   sudo python3 -m venv venv
   sudo venv/bin/pip install -r requirements.txt
   ```

2. **Create systemd services:**
   
   **Voice Agent Service** (`/etc/systemd/system/voice-agent.service`):
   ```ini
   [Unit]
   Description=Voice Agent Worker
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/voice-agent
   Environment="PATH=/opt/voice-agent/venv/bin"
   ExecStart=/opt/voice-agent/venv/bin/python agent.py start
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

   **Web Server Service** (`/etc/systemd/system/voice-agent-web.service`):
   ```ini
   [Unit]
   Description=Voice Agent Web Server
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/voice-agent
   Environment="PATH=/opt/voice-agent/venv/bin"
   ExecStart=/opt/voice-agent/venv/bin/python server.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable voice-agent voice-agent-web
   sudo systemctl start voice-agent voice-agent-web
   ```

4. **Configure Nginx** (`/etc/nginx/sites-available/voice-agent`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
   
       location / {
           proxy_pass http://127.0.0.1:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

### Using Docker
```dockerfile
FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python", "server.py"]
```

## 🐛 Troubleshooting

### Common Issues

**"Connection failed" error:**
- Make sure LiveKit server is running
- Verify agent is running (`python agent.py dev`)
- Check API keys in `.env` file

**Microphone not working:**
- Check browser permissions (microphone icon in address bar)
- Use `http://localhost:8080` (not different addresses)
- Try refreshing the page

**No audio from AI:**
- Check Speaker toggle is ON
- Verify browser isn't muted
- Check system audio settings

**"Module not found" errors:**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

**Edge TTS fails:**
- Check internet connection
- FFmpeg must be installed
- gTTS will automatically be used as fallback

### Debug Mode
```bash
LIVEKIT_LOG_LEVEL=debug python agent.py dev
```

## 🔄 Migration from v1.0

If upgrading from an older version:

1. **Update dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Remove old TTS configurations** from `agent.py` and use Edge TTS instead

3. **Update environment variables** - remove `OPENAI_API_KEY` (no longer needed for TTS)

## 🎭 Performance Benefits

### Cerebras Speed Comparison
- **70x faster** than GPU solutions
- **Sub-50ms response times** for Llama 3.1 70B
- **2,100+ tokens/second** generation speed
- **Original 16-bit precision** (no quality loss)

### Cost Savings with Edge TTS
- **Before**: OpenAI TTS at $15/million characters
- **After**: Edge TTS completely free
- **Savings**: 100% cost reduction for TTS

### LiveKit Agents 1.2+ Features
- **Prewarming**: Models loaded before first request
- **Advanced Turn Detection**: ML-based conversation flow
- **False Interruption Detection**: Handles spurious audio
- **Enhanced Noise Cancellation**: Built-in background noise removal

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💬 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Built with ❤️ using LiveKit, Cerebras, and Microsoft Edge TTS**
