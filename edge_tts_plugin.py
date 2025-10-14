"""
LiveKit-compatible Edge TTS Plugin
Uses Microsoft Edge TTS with gTTS as fallback

This plugin inherits from LiveKit's TTS base class and implements the required interface.
"""

import asyncio
import io
import logging
import subprocess
import tempfile
import os
from typing import AsyncIterable

import edge_tts
from gtts import gTTS

from livekit import agents, rtc
from livekit.agents import tts
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS, APIConnectOptions

logger = logging.getLogger(__name__)


class EdgeTTSChunkedStream(tts.ChunkedStream):
    """ChunkedStream implementation for Edge TTS"""
    
    def __init__(
        self,
        *,
        tts_instance: "EdgeTTS",
        input_text: str,
        conn_options: APIConnectOptions,
    ):
        self._tts_instance = tts_instance
        super().__init__(
            tts=tts_instance,
            input_text=input_text,
            conn_options=conn_options,
        )
    
    async def _run(self, output_emitter: tts.AudioEmitter) -> None:
        """Implementation of the _run method required by ChunkedStream"""
        request_id = f"edge_tts_{id(self)}"
        
        try:
            # Initialize the output emitter
            output_emitter.initialize(
                request_id=request_id,
                sample_rate=self._tts_instance._sample_rate,
                num_channels=self._tts_instance._num_channels,
                mime_type="audio/pcm",
            )
            
            # Generate audio using Edge TTS or fallback
            audio_data = await self._tts_instance._generate_audio(self._input_text)
            
            # Convert MP3 to PCM
            pcm_data = await self._tts_instance._convert_mp3_to_pcm(audio_data)
            
            # Push the PCM data
            output_emitter.push(pcm_data)
            
        except Exception as e:
            logger.error(f"Error in Edge TTS synthesis: {e}")
            raise


class EdgeTTS(tts.TTS):
    """
    LiveKit-compatible Edge TTS wrapper
    
    This converts Edge TTS (which generates MP3 files) into LiveKit's streaming format.
    """
    
    def __init__(
        self,
        voice: str = "en-US-AriaNeural",
        rate: str = "+0%",
        volume: str = "+0%",
        pitch: str = "+0Hz",
        use_fallback: bool = True,
        fallback_lang: str = "en",
        sample_rate: int = 24000,
        num_channels: int = 1,
    ):
        """
        Initialize Edge TTS
        
        Args:
            voice: Voice name (e.g., "en-US-AriaNeural", "en-US-GuyNeural")
            rate: Speech rate (-50% to +100%)
            volume: Volume level (-50% to +50%)
            pitch: Pitch adjustment (-50Hz to +50Hz)
            use_fallback: Whether to use gTTS as fallback
            fallback_lang: Language code for gTTS fallback
            sample_rate: Audio sample rate (default: 24000 Hz)
            num_channels: Number of audio channels (default: 1 for mono)
        """
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=num_channels,
        )
        
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self.use_fallback = use_fallback
        self.fallback_lang = fallback_lang
        
        # Store references to TTS engines
        self._edge_tts = edge_tts
        self._gtts = gTTS
        
        logger.info(f"🎙️ Edge TTS initialized with voice: {voice}")
    
    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> "EdgeTTSChunkedStream":
        """
        Synthesize text to audio (LiveKit interface)
        
        Args:
            text: Text to synthesize
            conn_options: API connection options
            
        Returns:
            EdgeTTSChunkedStream containing the synthesized audio
        """
        return EdgeTTSChunkedStream(
            tts_instance=self,
            input_text=text,
            conn_options=conn_options,
        )
    
    async def _generate_audio(self, text: str) -> bytes:
        """
        Generate audio using Edge TTS or gTTS fallback
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data as bytes (MP3 format)
        """
        try:
            if self._edge_tts is not None:
                return await self._synthesize_edge_tts(text)
            elif self._gtts is not None and self.use_fallback:
                return await self._synthesize_gtts(text)
            else:
                raise RuntimeError("No TTS engine available")
        except Exception as e:
            if self.use_fallback and self._gtts is not None:
                logger.warning(f"Edge TTS failed ({e}), falling back to gTTS")
                return await self._synthesize_gtts(text)
            raise
    
    async def _convert_mp3_to_pcm(self, audio_data: bytes) -> bytes:
        """
        Convert MP3 audio data to PCM format
        
        Args:
            audio_data: MP3 audio data
            
        Returns:
            PCM audio data (16-bit signed, little-endian)
        """
        # Write MP3 to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
            tmp_mp3.write(audio_data)
            tmp_mp3_path = tmp_mp3.name
        
        try:
            # Use ffmpeg to convert MP3 to raw PCM
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", tmp_mp3_path,
                    "-f", "s16le",  # 16-bit PCM
                    "-acodec", "pcm_s16le",
                    "-ar", str(self._sample_rate),
                    "-ac", str(self._num_channels),
                    "-",  # Output to stdout
                ],
                capture_output=True,
                check=True,
            )
            return result.stdout
        finally:
            # Clean up temp file
            os.unlink(tmp_mp3_path)
    
    async def _synthesize_impl(self, text: str) -> AsyncIterable[tts.SynthesizedAudio]:
        """
        Internal implementation that yields SynthesizedAudio chunks
        
        Args:
            text: Text to synthesize
            
        Yields:
            SynthesizedAudio objects containing audio frames
        """
        try:
            if self._edge_tts is not None:
                audio_data = await self._synthesize_edge_tts(text)
            elif self._gtts is not None and self.use_fallback:
                audio_data = await self._synthesize_gtts(text)
            else:
                raise RuntimeError("No TTS engine available")
        except Exception as e:
            if self.use_fallback and self._gtts is not None:
                logger.warning(f"Edge TTS failed ({e}), falling back to gTTS")
                audio_data = await self._synthesize_gtts(text)
            else:
                raise
        
        # Convert MP3 audio data to PCM frames
        # Edge TTS and gTTS return MP3 data, but LiveKit needs PCM
        import subprocess
        import tempfile
        import os
        
        # Write MP3 to temp file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
            tmp_mp3.write(audio_data)
            tmp_mp3_path = tmp_mp3.name
        
        try:
            # Use ffmpeg to convert MP3 to raw PCM
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", tmp_mp3_path,
                    "-f", "s16le",  # 16-bit PCM
                    "-acodec", "pcm_s16le",
                    "-ar", str(self._sample_rate),
                    "-ac", str(self._num_channels),
                    "-",  # Output to stdout
                ],
                capture_output=True,
                check=True,
            )
            pcm_data = result.stdout
        finally:
            # Clean up temp file
            os.unlink(tmp_mp3_path)
        
        # Create audio frames (chunk into smaller pieces for streaming feel)
        chunk_size = self._sample_rate * 2 * self._num_channels  # 1 second chunks
        request_id = text[:20]  # Use first 20 chars as request ID
        
        for i in range(0, len(pcm_data), chunk_size):
            chunk = pcm_data[i:i + chunk_size]
            
            # Create audio frame
            frame = tts.SynthesizedAudio(
                request_id=request_id,
                frame=agents.audio.AudioFrame(
                    data=chunk,
                    sample_rate=self._sample_rate,
                    num_channels=self._num_channels,
                    samples_per_channel=len(chunk) // (2 * self._num_channels),
                ),
            )
            
            yield frame

    
    async def _synthesize_edge_tts(self, text: str) -> bytes:
        """Synthesize using Edge TTS"""
        logger.debug(f"🔊 Synthesizing with Edge TTS: {text[:50]}...")
        
        # Create communicate object
        communicate = self._edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch,
        )
        
        # Collect audio chunks
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio" and "data" in chunk:
                audio_chunks.append(chunk["data"])
        
        if not audio_chunks:
            raise RuntimeError("No audio data received from Edge TTS")
        
        # Combine all chunks
        audio_data = b"".join(audio_chunks)
        logger.debug(f"✅ Edge TTS synthesis complete ({len(audio_data)} bytes)")
        
        return audio_data
    
    async def _synthesize_gtts(self, text: str) -> bytes:
        """Synthesize using gTTS as fallback"""
        logger.debug(f"🔊 Synthesizing with gTTS: {text[:50]}...")
        
        # Run gTTS in executor (it's synchronous)
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(
            None,
            self._gtts_sync,
            text,
        )
        
        logger.debug(f"✅ gTTS synthesis complete ({len(audio_data)} bytes)")
        return audio_data
    
    def _gtts_sync(self, text: str) -> bytes:
        """Synchronous gTTS synthesis"""
        tts_obj = self._gtts(text=text, lang=self.fallback_lang, slow=False)
        
        # Save to bytes buffer
        fp = io.BytesIO()
        tts_obj.write_to_fp(fp)
        fp.seek(0)
        return fp.read()


# Available voices for Edge TTS
EDGE_VOICES = {
    # English (US)
    "en-US-AriaNeural": "Female, friendly",
    "en-US-GuyNeural": "Male, casual",
    "en-US-JennyNeural": "Female, professional",
    "en-US-DavisNeural": "Male, professional",
    "en-US-AmberNeural": "Female, young",
    "en-US-AnaNeural": "Female, child",
    "en-US-AndrewNeural": "Male, warm",
    "en-US-AshleyNeural": "Female, warm",
    "en-US-BrandonNeural": "Male, energetic",
    "en-US-ChristopherNeural": "Male, mature",
    "en-US-CoraNeural": "Female, mature",
    "en-US-ElizabethNeural": "Female, classic",
    "en-US-EricNeural": "Male, clear",
    "en-US-JacobNeural": "Male, young",
    "en-US-MichelleNeural": "Female, expressive",
    "en-US-MonicaNeural": "Female, confident",
    "en-US-RogerNeural": "Male, authoritative",
    "en-US-SaraNeural": "Female, conversational",
    "en-US-SteffanNeural": "Male, conversational",
    
    # English (UK)
    "en-GB-SoniaNeural": "Female, British",
    "en-GB-RyanNeural": "Male, British",
    "en-GB-LibbyNeural": "Female, British casual",
    
    # English (Australia)
    "en-AU-NatashaNeural": "Female, Australian",
    "en-AU-WilliamNeural": "Male, Australian",
    
    # English (India)
    "en-IN-NeerjaNeural": "Female, Indian",
    "en-IN-PrabhatNeural": "Male, Indian",
}


def list_voices():
    """Print all available Edge TTS voices"""
    print("\n🎙️ Available Edge TTS Voices:")
    print("=" * 60)
    for voice, description in EDGE_VOICES.items():
        print(f"  {voice:<30} - {description}")
    print("=" * 60 + "\n")
