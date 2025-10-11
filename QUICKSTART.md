# Quick Start Guide

This guide will help you get the Voice Agent up and running quickly.

## Step 1: Prerequisites

Make sure you have:
- Python 3.8+ installed
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, or Edge)

## Step 2: Get API Keys

You'll need API keys from these services:

### Required Services

1. **Livekit** - Real-time communication platform
   - Option A: Use Livekit Cloud at https://cloud.livekit.io/
   - Option B: Run locally with Docker:
     ```bash
     docker run -d -p 7880:7880 -p 7881:7881 \
       -e LIVEKIT_KEYS="devkey: devsecret" \
       livekit/livekit-server --dev
     ```
   - For local Docker: Use `LIVEKIT_URL=ws://localhost:7880`, `LIVEKIT_API_KEY=devkey`, `LIVEKIT_API_SECRET=devsecret`

2. **Cerebras** - Fast AI inference
   - Sign up at https://inference.cerebras.ai/
   - Get your API key from the dashboard

3. **Deepgram** - Speech-to-Text
   - Sign up at https://deepgram.com/
   - Get your API key from the console

4. **OpenAI** - Text-to-Speech
   - Sign up at https://platform.openai.com/
   - Get your API key from the API section

## Step 3: Installation

1. Clone and enter the repository:
   ```bash
   git clone https://github.com/Killeren/Voice-agent.git
   cd Voice-agent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   
   # On Linux/Mac:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your API keys:
   ```env
   LIVEKIT_URL=ws://localhost:7880
   LIVEKIT_API_KEY=devkey
   LIVEKIT_API_SECRET=devsecret
   CEREBRAS_API_KEY=your_cerebras_key_here
   DEEPGRAM_API_KEY=your_deepgram_key_here
   OPENAI_API_KEY=your_openai_key_here
   ```

## Step 4: Running the Application

You need to run two processes:

### Terminal 1 - Voice Agent
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python agent.py dev
```

Wait for the message: "Voice assistant started successfully"

### Terminal 2 - Web Server
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python server.py
```

Wait for the message: "Starting web server on http://localhost:8080"

## Step 5: Using the Interface

1. Open your browser and go to http://localhost:8080
2. Click the **"Connect"** button
3. Allow microphone access when prompted
4. Start talking! The AI will respond to your voice

### Controls

- **Connect/Disconnect** - Join or leave the voice session
- **Microphone Toggle** - Turn your mic on/off
- **Speaker Toggle** - Turn audio output on/off

## Troubleshooting

### "Connection failed" error
- Make sure Livekit server is running
- Check that the agent is running (`python agent.py dev`)
- Verify API keys in `.env` are correct

### Microphone not working
- Check browser permissions (usually a microphone icon in the address bar)
- Make sure you're using `http://localhost:8080` (not a different address)
- Try refreshing the page

### No audio from AI
- Check that the Speaker toggle is ON
- Verify your browser isn't muted
- Check your system audio settings

### "Module not found" errors
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

## Next Steps

- Customize the AI's personality in `agent.py`
- Change the voice in the TTS settings
- Explore different Cerebras models

For more details, see the full [README.md](README.md)
