# Deployment Guide

This guide covers deploying the Voice Agent to production environments.

## Architecture Overview

The Voice Agent consists of three main components:

1. **Livekit Server** - Handles real-time WebRTC connections
2. **Voice Agent Worker** - Processes voice interactions with AI
3. **Web Server** - Serves the frontend and generates access tokens

## Production Deployment Options

### Option 1: Cloud Deployment with Managed Services

#### Requirements
- Livekit Cloud account
- VPS or cloud instance (AWS, GCP, Azure, etc.)
- Domain name (optional but recommended)

#### Steps

1. **Set up Livekit Cloud**
   - Create account at https://cloud.livekit.io/
   - Create a new project
   - Note your WebSocket URL and API credentials

2. **Deploy the Application**

   **On Ubuntu/Debian VPS:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install python3.10 python3.10-venv python3-pip nginx -y
   
   # Clone repository
   cd /opt
   sudo git clone https://github.com/Killeren/Voice-agent.git
   cd Voice-agent
   
   # Set up virtual environment
   sudo python3 -m venv venv
   sudo venv/bin/pip install -r requirements.txt
   
   # Configure environment
   sudo cp .env.example .env
   sudo nano .env  # Add your production API keys
   ```

3. **Create systemd services**

   **Voice Agent Service** (`/etc/systemd/system/voice-agent.service`):
   ```ini
   [Unit]
   Description=Voice Agent Worker
   After=network.target
   
   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/Voice-agent
   Environment="PATH=/opt/Voice-agent/venv/bin"
   ExecStart=/opt/Voice-agent/venv/bin/python agent.py start
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
   WorkingDirectory=/opt/Voice-agent
   Environment="PATH=/opt/Voice-agent/venv/bin"
   ExecStart=/opt/Voice-agent/venv/bin/python server.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start services:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable voice-agent voice-agent-web
   sudo systemctl start voice-agent voice-agent-web
   ```

4. **Configure Nginx as reverse proxy** (`/etc/nginx/sites-available/voice-agent`):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # Replace with your domain
       
       location / {
           proxy_pass http://localhost:8080;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

   Enable site:
   ```bash
   sudo ln -s /etc/nginx/sites-available/voice-agent /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

5. **Set up SSL with Let's Encrypt**:
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d your-domain.com
   ```

### Option 2: Docker Deployment

1. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   EXPOSE 8080
   
   CMD ["python", "server.py"]
   ```

2. **Create docker-compose.yml**:
   ```yaml
   version: '3.8'
   
   services:
     livekit:
       image: livekit/livekit-server:latest
       command: --dev
       ports:
         - "7880:7880"
         - "7881:7881"
       environment:
         - LIVEKIT_KEYS=devkey: devsecret
     
     voice-agent:
       build: .
       command: python agent.py start
       depends_on:
         - livekit
       env_file:
         - .env
       restart: unless-stopped
     
     web:
       build: .
       command: python server.py
       ports:
         - "8080:8080"
       depends_on:
         - livekit
       env_file:
         - .env
       restart: unless-stopped
   ```

3. **Deploy**:
   ```bash
   docker-compose up -d
   ```

## Security Best Practices

### 1. Environment Variables
- Never commit `.env` file to git
- Use strong, unique API keys
- Rotate keys regularly
- Use different keys for dev/staging/production

### 2. Network Security
- Always use HTTPS in production
- Configure firewall to restrict access
- Use VPC/private networks for backend services
- Implement rate limiting on token endpoint

### 3. Access Control
- Implement user authentication
- Add room access controls
- Monitor API usage
- Set up logging and alerting

## Monitoring and Logging

### Application Logs
```bash
# View agent logs
sudo journalctl -u voice-agent -f

# View web server logs
sudo journalctl -u voice-agent-web -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

Add health check endpoints to `server.py`:
```python
async def health_check(request):
    return web.json_response({"status": "healthy"})

app.router.add_get("/health", health_check)
```

### Monitoring Tools
- Use Prometheus + Grafana for metrics
- Set up Sentry for error tracking
- Use Livekit's built-in analytics

## Scaling

### Horizontal Scaling
- Run multiple agent workers
- Use load balancer for web servers
- Livekit handles room distribution automatically

### Vertical Scaling
- Increase VM resources for high load
- Optimize Python with pypy or Cython
- Use connection pooling for APIs

## Cost Optimization

1. **API Usage**
   - Monitor Cerebras token usage
   - Cache common responses
   - Implement conversation timeouts

2. **Infrastructure**
   - Use spot/preemptible instances
   - Auto-scale based on demand
   - Use Livekit Cloud's pay-as-you-go pricing

3. **Bandwidth**
   - Enable audio compression
   - Use CDN for static assets
   - Implement connection quality adaptation

## Backup and Recovery

1. **Configuration Backup**
   ```bash
   # Backup configuration
   sudo tar -czf voice-agent-backup.tar.gz /opt/Voice-agent/.env
   ```

2. **Database** (if you add persistence)
   - Regular automated backups
   - Test restore procedures
   - Store backups off-site

## Troubleshooting Production Issues

### High CPU Usage
- Check number of concurrent connections
- Monitor agent worker performance
- Consider scaling horizontally

### Memory Leaks
- Monitor memory usage over time
- Restart services periodically
- Check for unclosed resources

### Connection Issues
- Verify Livekit server status
- Check firewall rules
- Test WebRTC connectivity with https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/

## Support

For production issues:
1. Check logs first
2. Review Livekit documentation
3. Open GitHub issue with logs and configuration (redact sensitive data)
