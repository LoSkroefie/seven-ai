"""
Voice Activity Detection for smarter listening
Automatically detects when you start and stop speaking
"""
import webrtcvad
import collections
import pyaudio
import struct
from typing import Optional, Generator
import config

class VADListener:
    """Smart voice activity detection - knows when you're speaking"""
    
    def __init__(self, aggressiveness: int = 2):
        """
        Initialize VAD
        
        Args:
            aggressiveness: 0-3 (0=least aggressive, 3=most aggressive)
                          Higher = more strict about what counts as speech
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = 16000
        self.frame_duration_ms = 30  # 10, 20, or 30 ms
        self.padding_duration_ms = 300  # Continue recording for this long after speech stops
        self.audio = None
    
    def _frame_generator(self, audio_stream) -> Generator[bytes, None, None]:
        """Generate audio frames from stream"""
        frame_size = int(self.sample_rate * self.frame_duration_ms / 1000) * 2  # 2 bytes per sample
        while True:
            frame = audio_stream.read(frame_size)
            if not frame:
                break
            yield frame
    
    def listen_smart(self) -> Optional[bytes]:
        """
        Listen with VAD - automatically detects speech start/stop
        
        Returns:
            Raw audio bytes of speech or None
        """
        try:
            # Initialize PyAudio
            if not self.audio:
                self.audio = pyaudio.PyAudio()
            
            # Open stream
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )
            
            print("[MIC] Listening (VAD active - speak when ready)...")
            
            # Ringbuffer for padding
            num_padding_frames = int(self.padding_duration_ms / self.frame_duration_ms)
            ring_buffer = collections.deque(maxlen=num_padding_frames)
            triggered = False
            voiced_frames = []
            
            for frame in self._frame_generator(stream):
                is_speech = self.vad.is_speech(frame, self.sample_rate)
                
                if not triggered:
                    # Waiting for speech to start
                    ring_buffer.append((frame, is_speech))
                    num_voiced = len([f for f, speech in ring_buffer if speech])
                    
                    if num_voiced > 0.9 * ring_buffer.maxlen:
                        # Speech started!
                        print("🗣️  Speech detected...")
                        triggered = True
                        voiced_frames.extend([f for f, s in ring_buffer])
                        ring_buffer.clear()
                else:
                    # Currently in speech
                    voiced_frames.append(frame)
                    ring_buffer.append((frame, is_speech))
                    num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                    
                    if num_unvoiced > 0.9 * ring_buffer.maxlen:
                        # Speech ended!
                        print("[OK] Speech ended")
                        break
            
            stream.stop_stream()
            stream.close()
            
            if voiced_frames:
                # Return concatenated audio
                return b''.join(voiced_frames)
            
            return None
            
        except Exception as e:
            print(f"[ERROR] VAD error: {e}")
            if self.audio:
                self.audio.terminate()
                self.audio = None
            return None
    
    def cleanup(self):
        """Clean up audio resources"""
        if self.audio:
            self.audio.terminate()
            self.audio = None
