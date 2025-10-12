/**
 * Voice Agent Web Interface
 * Handles connection to Livekit room and voice interaction
 */

class VoiceAgentClient {
    constructor() {
        this.room = null;
        this.localAudioTrack = null;
        this.remoteAudioTrack = null;
        this.isMicEnabled = false;
        this.isSpeakerEnabled = false;
        
        this.initializeUI();
        this.attachEventListeners();
    }
    
    initializeUI() {
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.connectBtn = document.getElementById('connectBtn');
        this.disconnectBtn = document.getElementById('disconnectBtn');
        this.micToggle = document.getElementById('micToggle');
        this.speakerToggle = document.getElementById('speakerToggle');
        this.transcription = document.getElementById('transcription');
        this.audioElement = document.getElementById('audioElement');
    }
    
    attachEventListeners() {
        this.connectBtn.addEventListener('click', () => this.connect());
        this.disconnectBtn.addEventListener('click', () => this.disconnect());
        this.micToggle.addEventListener('click', () => this.toggleMicrophone());
        this.speakerToggle.addEventListener('click', () => this.toggleSpeaker());
    }
    
    updateStatus(status, isConnected = false) {
        this.statusText.textContent = status;
        if (isConnected) {
            this.statusIndicator.classList.add('connected');
        } else {
            this.statusIndicator.classList.remove('connected');
        }
    }
    
    showAudioPermissionPrompt() {
        const prompt = document.createElement('div');
        prompt.className = 'audio-permission-prompt';
        prompt.innerHTML = `
            <div class="prompt-content">
                <h3>🔊 Enable Audio</h3>
                <p>Click to enable audio playback for the voice assistant</p>
                <button onclick="this.parentElement.parentElement.remove(); window.voiceAgent.enableAudioPlayback()">Enable Audio</button>
            </div>
        `;
        prompt.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center;
            z-index: 1000;
        `;
        prompt.querySelector('.prompt-content').style.cssText = `
            background: white; padding: 20px; border-radius: 8px; text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        `;
        document.body.appendChild(prompt);
    }
    
    async enableAudioPlayback() {
        try {
            await this.audioElement.play();
            console.log('✅ Audio playback enabled by user interaction');
        } catch (e) {
            console.error('❌ Failed to enable audio:', e);
            alert('Failed to enable audio. Please check your browser settings.');
        }
    }
    
    addMessage(role, text) {
        // Remove placeholder if exists
        const placeholder = this.transcription.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.innerHTML = `
            <div class="role">${role === 'user' ? '👤 You' : '🤖 Assistant'}</div>
            <div class="text">${text}</div>
        `;
        
        this.transcription.appendChild(messageDiv);
        this.transcription.scrollTop = this.transcription.scrollHeight;
    }
    
    async getToken() {
        try {
            const response = await fetch('/api/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    participant: `user-${Date.now()}`
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get token');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error getting token:', error);
            throw error;
        }
    }
    
    async connect() {
        try {
            this.updateStatus('Connecting...');
            this.connectBtn.disabled = true;
            
            // Check if LiveKit client is loaded
            if (typeof LivekitClient === 'undefined') {
                throw new Error('LiveKit client library not loaded. Please refresh the page.');
            }
            
            // Get access token
            console.log('Fetching access token...');
            const tokenData = await this.getToken();
            console.log('Token received:', { url: tokenData.url, hasToken: !!tokenData.token });
            
            // Create room instance
            console.log('Creating room instance...');
            this.room = new LivekitClient.Room({
                adaptiveStream: true,
                dynacast: true,
            });
            
            // Set up event listeners
            this.setupRoomListeners();
            
            // Connect to room
            console.log('Connecting to room...');
            await this.room.connect(tokenData.url, tokenData.token);
            console.log('Connected successfully!');
            
            this.updateStatus('Connected', true);
            this.disconnectBtn.disabled = false;
            this.micToggle.disabled = false;
            this.speakerToggle.disabled = false;
            
            // Enable microphone by default
            await this.enableMicrophone();
            
            // Enable speaker by default
            await this.enableSpeaker();
            
            this.addMessage('assistant', 'Hello! I\'m your AI voice assistant. How can I help you today?');
            
        } catch (error) {
            console.error('Connection error:', error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            this.updateStatus('Connection failed');
            this.connectBtn.disabled = false;
            
            let errorMessage = 'Failed to connect to the voice agent. ';
            if (error.message.includes('LiveKit client')) {
                errorMessage += 'Please refresh the page and try again.';
            } else if (error.message.includes('token')) {
                errorMessage += 'Authentication error. Please check server logs.';
            } else {
                errorMessage += `Error: ${error.message}`;
            }
            
            alert(errorMessage);
        }
    }
    
    setupRoomListeners() {
        this.room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            console.log('Track subscribed:', track.kind, 'from participant:', participant.identity);
            
            if (track.kind === LivekitClient.Track.Kind.Audio) {
                this.remoteAudioTrack = track;
                const audioElement = track.attach();
                
                // Set up audio element for playback
                audioElement.autoplay = true;
                audioElement.playsInline = true;
                this.audioElement.srcObject = audioElement.srcObject;
                
                // Force audio play with user interaction context
                const playAudio = async () => {
                    try {
                        await this.audioElement.play();
                        console.log('✅ Audio playback started successfully');
                    } catch (e) {
                        console.warn('⚠️ Audio autoplay prevented:', e.message);
                        // Show user prompt to enable audio
                        this.showAudioPermissionPrompt();
                    }
                };
                
                // Try to play immediately
                playAudio();
            }
        });
        
        this.room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track) => {
            console.log('Track unsubscribed:', track.kind);
            track.detach();
        });
        
        this.room.on(LivekitClient.RoomEvent.Disconnected, () => {
            console.log('Disconnected from room');
            this.handleDisconnection();
        });
        
        this.room.on(LivekitClient.RoomEvent.DataReceived, (payload, participant) => {
            // Handle any data messages (e.g., transcriptions)
            try {
                const decoder = new TextDecoder();
                const message = JSON.parse(decoder.decode(payload));
                console.log('Data received:', message);
            } catch (error) {
                console.error('Error parsing data:', error);
            }
        });
    }
    
    async enableMicrophone() {
        try {
            if (!this.localAudioTrack) {
                this.localAudioTrack = await LivekitClient.createLocalAudioTrack({
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                });
                
                await this.room.localParticipant.publishTrack(this.localAudioTrack);
                
                // Monitor audio levels
                this.startAudioLevelMonitoring();
            }
            
            this.localAudioTrack.unmute();
            this.isMicEnabled = true;
            this.micToggle.classList.add('active');
            this.micToggle.querySelector('.toggle-state').textContent = 'On';
            
            console.log('✅ Microphone enabled and publishing audio');
            
        } catch (error) {
            console.error('Error enabling microphone:', error);
            alert('Failed to access microphone. Please check your permissions.');
        }
    }
    
    startAudioLevelMonitoring() {
        // Simply log that microphone is enabled and publishing
        console.log('💡 Speak into your microphone - the agent should respond');
    }
    
    disableMicrophone() {
        if (this.localAudioTrack) {
            this.localAudioTrack.mute();
            this.isMicEnabled = false;
            this.micToggle.classList.remove('active');
            this.micToggle.querySelector('.toggle-state').textContent = 'Off';
        }
    }
    
    async toggleMicrophone() {
        if (this.isMicEnabled) {
            this.disableMicrophone();
        } else {
            await this.enableMicrophone();
        }
    }
    
    async enableSpeaker() {
        this.isSpeakerEnabled = true;
        this.speakerToggle.classList.add('active');
        this.speakerToggle.querySelector('.toggle-state').textContent = 'On';
        this.audioElement.muted = false;
    }
    
    disableSpeaker() {
        this.isSpeakerEnabled = false;
        this.speakerToggle.classList.remove('active');
        this.speakerToggle.querySelector('.toggle-state').textContent = 'Off';
        this.audioElement.muted = true;
    }
    
    async toggleSpeaker() {
        if (this.isSpeakerEnabled) {
            this.disableSpeaker();
        } else {
            await this.enableSpeaker();
        }
    }
    
    async disconnect() {
        if (this.room) {
            await this.room.disconnect();
        }
        this.handleDisconnection();
    }
    
    handleDisconnection() {
        this.updateStatus('Disconnected');
        this.connectBtn.disabled = false;
        this.disconnectBtn.disabled = true;
        this.micToggle.disabled = true;
        this.speakerToggle.disabled = true;
        
        if (this.localAudioTrack) {
            this.localAudioTrack.stop();
            this.localAudioTrack = null;
        }
        
        this.remoteAudioTrack = null;
        this.isMicEnabled = false;
        this.isSpeakerEnabled = false;
        this.micToggle.classList.remove('active');
        this.speakerToggle.classList.remove('active');
        
        this.room = null;
    }
}

// Initialize the client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded');
    console.log('LivekitClient available:', typeof LivekitClient !== 'undefined');
    if (typeof LivekitClient !== 'undefined') {
        console.log('LivekitClient version:', LivekitClient.version || 'unknown');
    }
    window.voiceAgent = new VoiceAgentClient();
    console.log('Voice Agent Client initialized');
});
