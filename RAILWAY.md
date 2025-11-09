# Railway Deployment Guide

## Quick Deploy to Railway

Your Voice Agent is now Railway-ready! Here's how to deploy:

### Option 1: One-Click Deploy (Recommended)

1. **Fork this repository** to your GitHub account
2. **Sign up at [Railway](https://railway.app)**
3. **Click "New Project" → "Deploy from GitHub repo"**
4. **Select your forked repository**
5. **Set environment variables** in Railway dashboard:
   ```
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret  
   LIVEKIT_URL=wss://your-project.livekit.cloud
   CEREBRAS_API_KEY=your_cerebras_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   PERPLEXITY_API_KEY=your_perplexity_api_key_optional
   ```
6. **Deploy!** Railway will automatically build and deploy your app

### Option 2: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### What's Included

✅ **Dockerfile** - Containerized deployment  
✅ **railway.toml** - Railway configuration  
✅ **Procfile** - Process definition  
✅ **start-railway.sh** - Startup script for both web server and agent  
✅ **Health check endpoint** - `/health` for monitoring  
✅ **Environment variables** - Documented in `.env.example`  
✅ **.railwayignore** - Optimized deployment size  

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LIVEKIT_API_KEY` | LiveKit API key | ✅ |
| `LIVEKIT_API_SECRET` | LiveKit API secret | ✅ |
| `LIVEKIT_URL` | LiveKit WebSocket URL | ✅ |
| `CEREBRAS_API_KEY` | Cerebras AI API key | ✅ |
| `DEEPGRAM_API_KEY` | Deepgram STT API key | ✅ |
| `PERPLEXITY_API_KEY` | Perplexity search API key | ❌ |

### After Deployment

1. **Your app will be live** at your Railway domain (e.g., `https://your-app.railway.app`)
2. **Test the health endpoint**: `https://your-app.railway.app/health`
3. **Access the voice interface**: `https://your-app.railway.app/`

### Troubleshooting

- **Check logs**: Railway dashboard → Your service → Deploy logs
- **Environment variables**: Make sure all required vars are set
- **Domain issues**: Railway provides a domain automatically
- **Performance**: Railway auto-scales based on usage

### Cost Estimation

- **Railway**: $5/month for hobby plan, $20/month for pro
- **LiveKit**: Free tier available, then usage-based
- **Cerebras**: Pay-per-use ($0.60/M tokens for Llama 3.1 70B)
- **Deepgram**: Free tier available, then usage-based
- **Edge TTS**: Completely free!

### Production Tips

- Use Railway's **custom domains** for production
- Enable **auto-deploy** from your main branch
- Set up **health checks** for monitoring
- Consider using Railway's **database plugins** if needed
