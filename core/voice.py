"""
Voice input/output handling with emotion support
"""
import speech_recognition as sr
import pyttsx3
import re
import threading
import time
from typing import Optional
from core.emotions import EmotionConfig
import config

# Try to import keyboard for interrupt detection
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("[Warning] 'keyboard' module not installed. Keyboard interrupts disabled.")
    print("[Info] Install with: pip install keyboard")

class VoiceManager:
    """Manages speech recognition and text-to-speech"""
    
    def __init__(self, tts: bool = True):
        self.recognizer = sr.Recognizer()
        self.engine = None
        self.stop_speaking = False
        self.is_speaking = False
        self.interrupt_enabled = config.USE_INTERRUPTS and KEYBOARD_AVAILABLE
        self._calibrated = False
        if tts:
            self._init_tts()
        self._calibrate_mic()
        
        # Start interrupt monitor if enabled
        if self.interrupt_enabled:
            self._start_interrupt_monitor()
    
    def _calibrate_mic(self):
        """One-time microphone calibration for ambient noise."""
        try:
            with sr.Microphone() as source:
                print("[MIC] Calibrating for ambient noise (2s)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                # Set threshold — don't go too low or background noise triggers speech
                self.recognizer.energy_threshold = max(
                    self.recognizer.energy_threshold, 300
                )
                self.recognizer.dynamic_energy_threshold = True
                self._calibrated = True
                print(f"[MIC] Calibrated — energy threshold: {self.recognizer.energy_threshold:.0f}")
        except Exception as e:
            print(f"[MIC] Calibration failed: {e} — will calibrate per-listen")
            self._calibrated = False
    
    def _init_tts(self):
        """Initialize text-to-speech engine"""
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices')
            
            # Set voice (0=male, 1=female typically)
            if len(voices) > config.DEFAULT_VOICE_INDEX:
                self.engine.setProperty('voice', voices[config.DEFAULT_VOICE_INDEX].id)
            
            # Set default rate
            self.engine.setProperty('rate', config.DEFAULT_SPEECH_RATE)
            self.engine.setProperty('volume', config.DEFAULT_VOLUME)
        except Exception as e:
            print(f"Error initializing TTS: {e}")
            self.engine = None
    
    def _start_interrupt_monitor(self):
        """Start background thread to monitor for keyboard interrupts"""
        def monitor():
            while True:
                if self.is_speaking:
                    # Check for ESC or SPACE key
                    if keyboard.is_pressed('esc') or keyboard.is_pressed('space'):
                        self.stop_speaking = True
                        print("\n[⏹️ Interrupted by user - Press ESC or SPACE to stop]")
                        time.sleep(0.5)  # Debounce
                time.sleep(0.1)  # Check 10 times per second
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        print("[OK] Keyboard interrupt monitor started (ESC or SPACE to stop Seven)")
    
    def listen(self, timeout: int = 5, phrase_time_limit: int = 15) -> Optional[str]:
        """
        Listen for voice input from microphone
        
        Args:
            timeout: Seconds to wait for speech to start
            phrase_time_limit: Max seconds for phrase
            
        Returns:
            Recognized text or None
        """
        try:
            with sr.Microphone() as source:
                print("[Listening...]")
                
                # Only re-calibrate if startup calibration failed
                if not self._calibrated:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                # Listen
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
                
                # Recognize
                text = self.recognizer.recognize_google(audio)
                print(f"You said: {text}")
                return text
                
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("[...] Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"[Error] Speech recognition error: {e}")
            return None
        except Exception as e:
            print(f"[Error] Unexpected error during listening: {e}")
            return None
    
    def speak(self, text: str, emotion_config: Optional[EmotionConfig] = None):
        """
        Speak the given text with optional emotion
        Supports keyboard interrupts if enabled
        
        Args:
            text: Text to speak
            emotion_config: Emotion configuration for voice modulation
        """
        if not self.engine:
            print(f"[TTS unavailable] Would say: {text}")
            return
        
        try:
            self.stop_speaking = False
            self.is_speaking = True
            
            # Apply emotion configuration
            if emotion_config:
                self.engine.setProperty('rate', emotion_config.voice_rate)
                self.engine.setProperty('volume', emotion_config.voice_volume / 100)
                
                # Add emotion prefix
                text = emotion_config.emotion_prefix + text
            else:
                # Reset to defaults
                self.engine.setProperty('rate', config.DEFAULT_SPEECH_RATE)
                self.engine.setProperty('volume', config.DEFAULT_VOLUME)
            
            # Clean text for speech
            text = self._clean_for_speech(text)
            
            print(f"Bot: {text}")
            
            # If interrupts enabled, speak sentence by sentence
            if self.interrupt_enabled:
                sentences = self._split_sentences(text)
                for i, sentence in enumerate(sentences):
                    if self.stop_speaking:
                        print("[Speech interrupted]")
                        break
                    
                    self.engine.say(sentence)
                    self.engine.runAndWait()
            else:
                # Speak all at once (original behavior)
                self.engine.say(text)
                self.engine.runAndWait()
                
        except Exception as e:
            print(f"[Error] Error speaking: {e}")
            print(f"Would have said: {text}")
        finally:
            self.is_speaking = False
    
    def _split_sentences(self, text: str) -> list:
        """Split text into sentences for interruptible speech"""
        # Split on common sentence endings
        sentences = re.split(r'([.!?]+\s+)', text)
        
        # Recombine sentences with their punctuation
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            if sentence.strip():
                result.append(sentence.strip())
        
        # Handle last sentence if no punctuation
        if sentences and sentences[-1].strip():
            result.append(sentences[-1].strip())
        
        return result if result else [text]
    
    def _clean_for_speech(self, text: str) -> str:
        """Clean text for natural speech"""
        # Remove markdown formatting
        text = re.sub(r'\*\*', '', text)
        text = re.sub(r'__', '', text)
        text = re.sub(r'\*', '', text)
        text = re.sub(r'_', '', text)
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`.*?`', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Keep only speech-friendly characters
        text = re.sub(r'[^\w\s.,!?\'"()-]+', '', text)
        
        return text.strip()
    
    def test(self):
        """Test voice I/O"""
        print("\n[Test] Testing Voice I/O...")
        
        # Test TTS
        self.speak("Voice test. If you can hear me, speech output is working.")
        
        # Test listening
        print("\n[Listening] Say something to test speech recognition...")
        result = self.listen(timeout=10)
        
        if result:
            print(f"[OK] Speech recognition working! Heard: {result}")
            self.speak(f"I heard you say: {result}")
        else:
            print("[Error] Speech recognition test failed or timeout")
