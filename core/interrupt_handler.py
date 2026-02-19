"""
Interrupt handling for natural conversation flow
Allows user to interrupt bot mid-speech
"""
import threading
import time
import speech_recognition as sr
from typing import Optional, Callable

class InterruptHandler:
    """Manages conversation interrupts"""
    
    def __init__(self):
        self.speaking = False
        self.interrupted = False
        self.lock = threading.Lock()
    
    def start_speaking(self):
        """Mark that bot started speaking"""
        with self.lock:
            self.speaking = True
            self.interrupted = False
    
    def stop_speaking(self):
        """Mark that bot stopped speaking"""
        with self.lock:
            self.speaking = False
            self.interrupted = False
    
    def interrupt(self):
        """Trigger an interrupt"""
        with self.lock:
            if self.speaking:
                self.interrupted = True
                print("\n[INTERRUPTED]")
                return True
            return False
    
    def should_continue(self) -> bool:
        """Check if should continue speaking"""
        with self.lock:
            return not self.interrupted
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        with self.lock:
            return self.speaking
    
    def reset(self):
        """Reset interrupt state"""
        with self.lock:
            self.speaking = False
            self.interrupted = False


class InterruptibleTTS:
    """Text-to-speech that can be interrupted"""
    
    def __init__(self, tts_engine, interrupt_handler: InterruptHandler):
        self.engine = tts_engine
        self.interrupt_handler = interrupt_handler
        self.speaking_thread = None
        self.listener_thread = None
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Interrupt keywords
        self.interrupt_keywords = [
            'stop', 'shut up', 'shutup', 'be quiet', 
            'quiet', 'silence', 'enough', 'halt', 'pause'
        ]
    
    def speak_interruptible(self, text: str, emotion_config=None):
        """
        Speak text but allow interruption
        
        Args:
            text: Text to speak
            emotion_config: Voice emotion configuration
        """
        # Mark as speaking
        self.interrupt_handler.start_speaking()
        
        # Start background voice interrupt listener
        self._start_voice_listener()
        
        try:
            # Apply emotion if provided
            if emotion_config:
                self.engine.setProperty('rate', emotion_config.voice_rate)
                self.engine.setProperty('volume', emotion_config.voice_volume / 100)
            
            # Split into sentences for interruptibility
            sentences = self._split_sentences(text)
            
            for sentence in sentences:
                # Check for interrupt before each sentence
                if not self.interrupt_handler.should_continue():
                    print("[STOPPED] Speech interrupted")
                    break
                
                # Speak sentence
                self.engine.say(sentence)
                self.engine.runAndWait()
            
        finally:
            self._stop_voice_listener()
            self.interrupt_handler.stop_speaking()
    
    def _start_voice_listener(self):
        """Start background thread to listen for interrupt commands"""
        self.listener_thread = threading.Thread(
            target=self._listen_for_interrupts,
            daemon=True
        )
        self.listener_thread.start()
    
    def _stop_voice_listener(self):
        """Stop the voice listener thread"""
        # Thread will exit when speaking stops
        pass
    
    def _listen_for_interrupts(self):
        """Background thread that listens for interrupt keywords"""
        try:
            with self.microphone as source:
                # Adjust for ambient noise quickly
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                
                while self.interrupt_handler.is_speaking():
                    try:
                        # Listen with short timeout
                        audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=2)
                        
                        # Try to recognize
                        text = self.recognizer.recognize_google(audio).lower()
                        
                        # Check for interrupt keywords
                        if any(keyword in text for keyword in self.interrupt_keywords):
                            print(f"[VOICE INTERRUPT] Detected: '{text}'")
                            self.interrupt_handler.interrupt()
                            break
                            
                    except sr.WaitTimeoutError:
                        # No speech detected, continue listening
                        continue
                    except sr.UnknownValueError:
                        # Could not understand, continue listening
                        continue
                    except Exception:
                        # Any other error, stop listening
                        break
                        
        except Exception as e:
            # Microphone unavailable or other issue
            pass
    
    def _split_sentences(self, text: str) -> list:
        """Split text into sentences for interruptible speech"""
        import re
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
