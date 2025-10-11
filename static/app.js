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
                    room: 'voice-agent-room',
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
            
            // Get access token
            const tokenData = await this.getToken();
            
            // Create room instance
            this.room = new LivekitClient.Room({
                adaptiveStream: true,
                dynacast: true,
            });
            
            // Set up event listeners
            this.setupRoomListeners();
            
            // Connect to room
            await this.room.connect(tokenData.url, tokenData.token);
            
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
            this.updateStatus('Connection failed');
            this.connectBtn.disabled = false;
            alert('Failed to connect to the voice agent. Please check your configuration and try again.');
        }
    }
    
    setupRoomListeners() {
        this.room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            console.log('Track subscribed:', track.kind);
            
            if (track.kind === LivekitClient.Track.Kind.Audio) {
                this.remoteAudioTrack = track;
                const audioElement = track.attach();
                this.audioElement.srcObject = new MediaStream([audioElement.srcObject.getAudioTracks()[0]]);
                
                // Try to play audio
                this.audioElement.play().catch(e => {
                    console.warn('Audio autoplay prevented:', e);
                });
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
            }
            
            this.localAudioTrack.unmute();
            this.isMicEnabled = true;
            this.micToggle.classList.add('active');
            this.micToggle.querySelector('.toggle-state').textContent = 'On';
            
        } catch (error) {
            console.error('Error enabling microphone:', error);
            alert('Failed to access microphone. Please check your permissions.');
        }
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
    const client = new VoiceAgentClient();
    console.log('Voice Agent Client initialized');
});
