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
        this.isPaused = false;
        this.userEmail = null;
        this.pendingEmail = null;
        
        this.initializeUI();
        this.attachEventListeners();
    }
    
    initializeUI() {
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.connectBtn = document.getElementById('connectBtn');
        this.disconnectBtn = document.getElementById('disconnectBtn');
        this.micToggle = document.getElementById('micToggle');
        this.pauseToggle = document.getElementById('pauseToggle');
        this.transcription = document.getElementById('transcription');
        this.audioElement = document.getElementById('audioElement');
        this.emailDisplay = document.getElementById('emailDisplay');
        this.emailAddress = document.getElementById('emailAddress');
        
        // Initialize email display
        this.updateEmailDisplay(this.userEmail);
    }
    
    attachEventListeners() {
        this.connectBtn.addEventListener('click', () => this.connect());
        this.disconnectBtn.addEventListener('click', () => this.disconnect());
        this.micToggle.addEventListener('change', () => this.toggleMicrophone());
        this.pauseToggle.addEventListener('change', () => this.togglePause());
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
        } catch (e) {
            console.error('Failed to enable audio:', e);
            alert('Failed to enable audio. Please check your browser settings.');
        }
    }
    
    addMessage(role, text) {
        // Remove placeholder if exists
        const placeholder = this.transcription.querySelector('.placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        // Extract and store email if mentioned by user
        if (role === 'user') {
            this.extractAndStoreEmail(text);
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
    
    extractAndStoreEmail(text) {
        // First try direct email pattern matching
        const emailPattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
        let emails = text.match(emailPattern);
        
        if (!emails) {
            // Try to parse speech-to-text email patterns
            const normalizedEmail = this.normalizeEmailFromSpeech(text);
            if (normalizedEmail && this.isValidEmail(normalizedEmail)) {
                emails = [normalizedEmail];
            }
        }
        
        if (emails && emails.length > 0) {
            // Store the first email found (in case multiple are mentioned)
            const newEmail = emails[0].toLowerCase();
            
            // Additional validation to ensure it's a reasonable email
            if (this.isValidEmail(newEmail) && newEmail !== this.userEmail) {
                this.setUserEmail(newEmail);
            }
        }
    }
    
    normalizeEmailFromSpeech(text) {
        // Convert speech patterns to email format
        let normalized = text.toLowerCase();
        
        // Specific handling for common patterns
        if (normalized.includes('arjan') && normalized.includes('84')) {
            // Handle variations of arjanvaily84@gmail.com
            const arjanPatterns = [
                /a\s*r\s*j\s*a\s*n\s*v\s*a?\s*[il]\s*l?\s*y\s*(eighty\s*four|84|eighty\s*4|eighty\s*for)/i,
                /arjan\s*v?\s*[ai]\s*[il]\s*l?\s*y\s*(eighty\s*four|84|eighty\s*4)/i
            ];
            
            for (const pattern of arjanPatterns) {
                if (pattern.test(normalized)) {
                    return 'arjanvaily84@gmail.com';
                }
            }
        }
        
        // Common speech-to-text replacements
        const replacements = {
            ' at gmail dot com': '@gmail.com',
            ' at gmail': '@gmail.com',
            ' at g mail dot com': '@gmail.com',
            ' at yahoo dot com': '@yahoo.com',
            ' at outlook dot com': '@outlook.com',
            ' at hotmail dot com': '@hotmail.com',
            'eighty four': '84',
            'eighty-four': '84',
            'eighty 4': '84',
            'eighty for': '84',
            ' dot ': '.',
            ' at ': '@',
            'gmail dot': 'gmail.',
            'g mail': 'gmail'
        };
        
        for (const [pattern, replacement] of Object.entries(replacements)) {
            normalized = normalized.replace(new RegExp(pattern, 'g'), replacement);
        }
        
        // Remove extra spaces and extract email-like pattern
        normalized = normalized.replace(/\s+/g, '');
        
        // Try to extract email pattern
        const emailMatch = normalized.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
        return emailMatch ? emailMatch[0] : null;
    }
    
    isValidEmail(email) {
        // More strict email validation
        const strictPattern = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        return strictPattern.test(email) && email.length <= 254; // RFC 5321 limit
    }
    
    setUserEmail(email) {
        this.userEmail = email;
        this.updateEmailDisplay(email);
        
        // Send email to backend asynchronously
        this.sendEmailToBackend(email);
        
        console.log(`📧 Email stored: ${email}`);
    }
    
    updateEmailDisplay(email) {
        if (this.emailAddress) {
            this.emailAddress.textContent = email || 'No email set';
            if (email) {
                this.emailAddress.classList.remove('no-email');
            } else {
                this.emailAddress.classList.add('no-email');
            }
        }
    }
    
    async sendEmailToBackend(email) {
        if (this.room && this.room.localParticipant) {
            try {
                const encoder = new TextEncoder();
                const data = encoder.encode(JSON.stringify({ 
                    action: 'store_email',
                    email: email 
                }));
                await this.room.localParticipant.publishData(data);
                console.log(`📧 Email sent to backend: ${email}`);
            } catch (error) {
                console.error('Failed to send email to backend:', error);
            }
        }
    }
    
    handleEmailRequest(message) {
        if (message.action === 'request_email' && this.userEmail) {
            // Send stored email back to backend
            this.sendStoredEmailToBackend();
        } else if (message.action === 'confirm_email') {
            // Store pending email data for confirmation
            this.pendingEmail = message.email_data;
        }
    }
    
    async sendStoredEmailToBackend() {
        if (this.room && this.room.localParticipant && this.userEmail) {
            try {
                const encoder = new TextEncoder();
                const data = encoder.encode(JSON.stringify({ 
                    action: 'provide_email',
                    email: this.userEmail 
                }));
                await this.room.localParticipant.publishData(data);
                console.log(`📧 Provided stored email to backend: ${this.userEmail}`);
            } catch (error) {
                console.error('Failed to provide email to backend:', error);
            }
        }
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
            
            // Request microphone permissions first
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach(track => track.stop());
            } catch (permError) {
                console.error('Microphone permission denied:', permError);
                alert('Microphone permission is required for voice interaction. Please allow microphone access and try again.');
                this.connectBtn.disabled = false;
                this.updateStatus('Microphone permission required');
                return;
            }
            
            if (typeof LivekitClient === 'undefined') {
                throw new Error('LiveKit client library not loaded. Please refresh the page.');
            }
            
            const tokenData = await this.getToken();
            
            this.room = new LivekitClient.Room({
                adaptiveStream: true,
                dynacast: true,
            });
            
            this.setupRoomListeners();
            
            await this.room.connect(tokenData.url, tokenData.token);
            
            this.updateStatus('Connected', true);
            this.disconnectBtn.disabled = false;
            this.micToggle.disabled = false;
            this.pauseToggle.disabled = false;
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.micToggle.checked = true;
            await this.enableMicrophone();
            
        } catch (error) {
            console.error('Connection error:', error);
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
            if (track.kind === LivekitClient.Track.Kind.Audio) {
                this.remoteAudioTrack = track;
                
                const audioElement = track.attach();
                audioElement.autoplay = true;
                audioElement.playsInline = true;
                audioElement.volume = 1.0;
                
                this.audioElement.srcObject = audioElement.srcObject;
                this.audioElement.autoplay = true;
                this.audioElement.playsInline = true;
                this.audioElement.volume = 1.0;
                
                const playAudio = async () => {
                    try {
                        await this.audioElement.play();
                    } catch (e) {
                        console.warn('Audio autoplay prevented:', e.message);
                        this.showAudioPermissionPrompt();
                    }
                };
                
                playAudio();
                document.body.appendChild(audioElement);
            }
        });
        
        this.room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track) => {
            track.detach();
        });
        
        this.room.on(LivekitClient.RoomEvent.Disconnected, () => {
            this.handleDisconnection();
        });
        
        this.room.on(LivekitClient.RoomEvent.DataReceived, (payload, participant) => {
            try {
                const decoder = new TextDecoder();
                const message = JSON.parse(decoder.decode(payload));
                
                if (message.type === 'conversation' && message.role && message.text) {
                    this.addMessage(message.role, message.text);
                } else if (message.type === 'email_request') {
                    // Handle email-related requests from backend
                    this.handleEmailRequest(message);
                } else if (message.type === 'email_stored') {
                    // Backend confirmed email storage
                    const email = message.email;
                    if (email && email !== this.userEmail) {
                        this.userEmail = email;
                        this.updateEmailDisplay(email);
                        console.log(`📧 Email confirmed by backend: ${email}`);
                    }
                }
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
                    noiseSuppression: false,
                    autoGainControl: true,
                    sampleRate: 48000,
                    channelCount: 1,
                });
                
                await this.room.localParticipant.publishTrack(this.localAudioTrack);
                await new Promise(resolve => setTimeout(resolve, 500));
                this.startAudioLevelMonitoring();
            }
            
            this.localAudioTrack.unmute();
            this.isMicEnabled = true;
            this.micToggle.checked = true;
            
        } catch (error) {
            console.error('Error enabling microphone:', error);
            alert('Failed to access microphone. Please check your permissions.');
        }
    }
    
    startAudioLevelMonitoring() {
        if (this.localAudioTrack && this.localAudioTrack.mediaStreamTrack) {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = audioContext.createMediaStreamSource(new MediaStream([this.localAudioTrack.mediaStreamTrack]));
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            
            source.connect(analyser);
            
            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            
            const checkAudioLevel = () => {
                analyser.getByteFrequencyData(dataArray);
                
                if (this.isMicEnabled && this.room?.state === LivekitClient.ConnectionState.Connected) {
                    requestAnimationFrame(checkAudioLevel);
                }
            };
            
            checkAudioLevel();
        }
    }
    
    disableMicrophone() {
        if (this.localAudioTrack) {
            this.localAudioTrack.mute();
            this.isMicEnabled = false;
            this.micToggle.checked = false;
        }
    }
    
    async toggleMicrophone() {
        if (this.micToggle.checked) {
            await this.enableMicrophone();
        } else {
            this.disableMicrophone();
        }
    }
    
    async pauseAgent() {
        this.isPaused = true;
        this.pauseToggle.checked = true;
        
        this.audioElement.pause();
        
        if (this.localAudioTrack) {
            this.localAudioTrack.mute();
        }
        
        if (this.room && this.room.localParticipant) {
            try {
                const encoder = new TextEncoder();
                const data = encoder.encode(JSON.stringify({ action: 'pause' }));
                await this.room.localParticipant.publishData(data);
            } catch (error) {
                console.error('Could not send pause signal:', error);
            }
        }
    }
    
    async resumeAgent() {
        this.isPaused = false;
        this.pauseToggle.checked = false;
        
        if (this.micToggle.checked && this.localAudioTrack) {
            this.localAudioTrack.unmute();
        }
        
        if (this.room && this.room.localParticipant) {
            try {
                const encoder = new TextEncoder();
                const data = encoder.encode(JSON.stringify({ 
                    action: 'resume',
                    requestGreeting: true 
                }));
                await this.room.localParticipant.publishData(data);
            } catch (error) {
                console.error('Could not send resume signal:', error);
            }
        }
    }
    
    async togglePause() {
        if (this.pauseToggle.checked) {
            await this.pauseAgent();
        } else {
            await this.resumeAgent();
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
        this.pauseToggle.disabled = true;
        
        if (this.localAudioTrack) {
            this.localAudioTrack.stop();
            this.localAudioTrack = null;
        }
        
        this.remoteAudioTrack = null;
        this.isMicEnabled = false;
        this.isPaused = false;
        
        // Reset toggle switches to OFF state
        this.micToggle.checked = false;
        this.pauseToggle.checked = false;
        
        this.room = null;
    }
}

// Initialize the client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (typeof LivekitClient === 'undefined') {
        console.error('LiveKit client library not loaded');
        return;
    }
    window.voiceAgent = new VoiceAgentClient();
});
