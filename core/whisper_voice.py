"""
Enhanced voice input using OpenAI Whisper for better accuracy
"""
import whisper
import numpy as np
import soundfile as sf
import tempfile
import speech_recognition as sr
from typing import Optional
from pathlib import Path
import config

class WhisperVoiceManager:
    """Manages speech recognition using Whisper (much better than Google)"""
    
    def __init__(self, model_size: str = "base"):
        """
        Initialize Whisper
        
        Args:
            model_size: tiny, base, small, medium, large
                       base = good balance of speed/accuracy
        """
        print(f"[INIT] Loading Whisper model ({model_size})...")
        try:
            self.model = whisper.load_model(model_size)
            self.recognizer = sr.Recognizer()
            print(f"[OK] Whisper loaded!")
        except Exception as e:
            print(f"[ERROR] Error loading Whisper: {e}")
            print("[TIP] Falling back to Google Speech Recognition")
            self.model = None
            self.recognizer = sr.Recognizer()
    
    def listen(self, timeout: int = 10) -> Optional[str]:
        """
        Listen and transcribe with Whisper
        
        Returns:
            Transcribed text or None
        """
        if not self.model:
            return self._listen_fallback(timeout)
        
        try:
            with sr.Microphone() as source:
                print("[MIC] Listening...")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen
                audio = self.recognizer.listen(source, timeout=timeout)
                
                # Convert to numpy array for Whisper
                audio_data = np.frombuffer(audio.get_wav_data(), dtype=np.int16)
                audio_float = audio_data.astype(np.float32) / 32768.0
                
                # Transcribe with Whisper
                result = self.model.transcribe(
                    audio_float,
                    language="en",
                    fp16=False  # Use FP32 for CPU
                )
                
                text = result["text"].strip()
                if text:
                    print(f"[NOTE] You said: {text}")
                    return text
                return None
                
        except sr.WaitTimeoutError:
            print("⏱️  Timeout waiting for speech")
            return None
        except Exception as e:
            print(f"[ERROR] Error in Whisper transcription: {e}")
            return self._listen_fallback(timeout)
    
    def _listen_fallback(self, timeout: int) -> Optional[str]:
        """Fallback to Google Speech Recognition"""
        try:
            with sr.Microphone() as source:
                print("[MIC] Listening (fallback)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)
                text = self.recognizer.recognize_google(audio)
                print(f"[NOTE] You said: {text}")
                return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[ERROR] Speech recognition error: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return None
