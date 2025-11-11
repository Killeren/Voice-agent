# Voice Agent
AI Voice Assistant with Web Interface using LiveKit Agents 1.2+ and Cerebras

> ⚡ **Updated for LiveKit Agents 1.2+ API** - Now with native Cerebras integration and free Edge TTS!

An interactive AI voice assistant that you can talk to directly in your browser. Built with LiveKit for real-time audio communication, Cerebras for ultra-fast AI responses, and Microsoft Edge TTS for free, high-quality voice synthesis.

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Voice-agent

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Start with Docker (requires Docker Desktop)
docker-compose up --build

# 4. Open http://localhost:8080 in your browser
```

## 🚀 Features

- 🎙️ **Real-time voice interaction** with AI
- 🌐 **Web-based interface** - no installation required for users
- ⚡ **Ultra-fast AI responses** powered by Cerebras (70x faster, 2,100+ tokens/sec)
- 🎯 **Advanced Voice Activity Detection** (VAD) with prewarming
- 📝 **Speech-to-Text** using Deepgram Nova-2
- 🔊 **Free Text-to-Speech** using Microsoft Edge TTS (26+ voices) with gTTS fallback
- 📧 **Email Integration** - send emails via voice commands with automatic email detection
- 🔍 **Current Information Search** using Perplexity API for up-to-date responses
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
├── Dockerfile               # Docker container configuration
├── docker-compose.yml       # Multi-service Docker setup
├── docker-setup.sh          # Automated setup script
├── Makefile                # Convenient Docker commands
├── .dockerignore           # Docker build optimization
└── README.md               # This documentation
```

## 🛠️ Prerequisites

- **Docker Desktop** installed ([docker.com](https://www.docker.com/products/docker-desktop/))
- **Modern web browser** (Chrome, Firefox, or Edge)
- **API Keys** (see next section)

> 🐳 **This project runs entirely in Docker containers** - no need to install Python, FFmpeg, or manage virtual environments!

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

# Build and start with Docker
docker-compose up --build
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

# Optional: Email functionality
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

For production, use your actual LiveKit Cloud credentials:
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_actual_api_key
LIVEKIT_API_SECRET=your_actual_secret
```

### 3. Run the Application

**Start all services with Docker:**
```bash
docker-compose up --build
```
Wait for both services to start:
- "Voice assistant started successfully" (agent service)
- "Starting web server on http://localhost:8080" (web service)

### 4. Use the Interface
1. Open browser to `http://localhost:8080`
2. Click **"Connect"** button
3. Allow microphone access when prompted
4. Start talking! The AI will respond with voice

### 📧 Email Features Usage

The voice agent now includes email functionality:

**Auto Email Detection:**
- When you mention an email address in conversation, it's automatically detected and stored
- The email appears in the "Guest" box in the top-right corner
- Example: "My email is john@example.com" - automatically stores the email

**Sending Emails:**
- Say: "Send an email to alice@company.com about the meeting tomorrow"
- Say: "Send an email" (uses your stored email address if available)
- The AI will confirm details before sending
- Respond with "yes" or "proceed" to send, "no" or "cancel" to abort

**Email Configuration:**
For email functionality, set these environment variables in your `.env` file:
```env
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password  # Use App Password for Gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**Gmail Setup:**
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: Google Account → Security → App passwords
3. Use the App Password (not your regular password) in `SENDER_PASSWORD`

## 🐳 Docker Setup & Commands

### Prerequisites for Docker Setup

1. **Docker Desktop** - Install from [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Environment Variables** - Copy `.env.example` to `.env` and fill in your API keys

### Docker Services

The application runs two services:

#### voice-agent-server
- **Purpose**: Web server serving the frontend interface
- **Port**: 8080
- **Access**: http://localhost:8080

#### voice-agent-worker  
- **Purpose**: LiveKit agent worker for voice processing
- **Dependencies**: Requires the server to be running

### Basic Operations
```bash
# Start services (builds automatically on first run)
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Rebuild after code changes
docker-compose up --build

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Development
```bash
# Quick rebuild and restart
make dev-restart

# View logs for specific service
docker-compose logs voice-agent-worker
docker-compose logs voice-agent-server

# Execute commands in running container
docker-compose exec voice-agent-server bash
```

### Development with Live Code Reloading

For development with live code reloading, you can mount the source code as a volume by modifying the docker-compose.yml:

```yaml
volumes:
  - .:/app
  - ./.env:/app/.env:ro
```

### Docker Troubleshooting

#### Port already in use:
If port 8080 is already in use, modify the port mapping in docker-compose.yml:
```yaml
ports:
  - "8081:8080"  # Use 8081 instead of 8080
```

#### LiveKit connection issues:
- Ensure LiveKit server is running and accessible
- For local LiveKit server, use `LIVEKIT_URL=ws://host.docker.internal:7880`
- For external LiveKit server, use the full URL

#### Environment variables not loading:
- Ensure `.env` file exists in the project root
- Check that all required variables are set
- Restart containers after changing .env: `docker-compose restart`

## 🎛️ Customization

### Change AI Personality
Edit the instructions in `agent.py`:
```python
agent = Agent(
    instructions="You are a helpful assistant. Be concise and friendly."
)
```

After making changes, restart the containers:
```bash
docker-compose restart
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

### Using Docker (Recommended)

1. **Deploy to server:**
   ```bash
   # Install Docker and Docker Compose on your server
   sudo apt update && sudo apt install docker.io docker-compose nginx -y
   sudo usermod -aG docker $USER
   
   # Clone and deploy
   cd /opt
   sudo git clone <your-repo> voice-agent
   cd voice-agent
   ```

2. **Configure environment:**
   ```bash
   sudo cp .env.example .env
   # Edit .env with your production API keys
   sudo nano .env
   ```

3. **Start with Docker Compose:**
   ```bash
   sudo docker-compose up -d --build
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

### Alternative: Manual Docker Build
```bash
# Build the Docker image
docker build -t voice-agent .

# Run the services manually
docker run -d --name voice-agent-server -p 8080:8080 --env-file .env voice-agent python server.py
docker run -d --name voice-agent-worker --env-file .env voice-agent python agent.py start
```

## 🐛 Troubleshooting

### Common Issues

**"Connection failed" error:**
- Make sure LiveKit server is running
- Verify services are running (`docker-compose ps`)
- Check API keys in `.env` file
- Check container logs (`docker-compose logs`)

**Microphone not working:**
- Check browser permissions (microphone icon in address bar)
- Use `http://localhost:8080` (not different addresses)
- Try refreshing the page

**No audio from AI:**
- Check Speaker toggle is ON
- Verify browser isn't muted
- Check system audio settings

**"Module not found" errors:**
- Rebuild Docker containers: `docker-compose down && docker-compose up --build`
- Check if all services are running: `docker-compose ps`

**Edge TTS fails:**
- Check internet connection
- FFmpeg must be installed
- gTTS will automatically be used as fallback

### Debug Mode
```bash
# View logs from Docker containers
docker-compose logs -f

# Debug specific service
docker-compose logs voice-agent-worker
docker-compose logs voice-agent-server

# Run with debug logging
LIVEKIT_LOG_LEVEL=debug docker-compose up
```

## 🔄 Migration from v1.0

If upgrading from an older version:

1. **Update containers:**
   ```bash
   docker-compose down
   docker-compose up --build
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

## 📦 Migration from Virtual Environment

This project has been **fully containerized with Docker**! If you were previously using virtual environments:

### What Changed
- ❌ **No more `venv/` directory** - everything runs in Docker containers
- ❌ **No more `pip install`** - dependencies are handled by Docker
- ❌ **No more Python version conflicts** - Docker ensures consistent environment
- ✅ **One command setup**: `docker-compose up --build`
- ✅ **Consistent across all platforms** - works the same on Windows, macOS, Linux

### Quick Migration
```bash
# Old way (don't do this anymore)
# python -m venv venv
# source venv/bin/activate
# pip install -r requirements.txt
# python server.py & python agent.py start

# New way (Docker)
docker-compose up --build
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💬 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Built with ❤️ using LiveKit, Cerebras, and Microsoft Edge TTS**
