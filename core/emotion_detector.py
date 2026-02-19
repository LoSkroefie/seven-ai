"""
Emotion detection from voice tone analysis using librosa
"""
import numpy as np
import librosa
from typing import Optional, Tuple
from core.emotions import Emotion

class VoiceEmotionDetector:
    """Detect emotion from voice characteristics"""
    
    def __init__(self):
        self.emotions = {
            'happy': Emotion.HAPPINESS,
            'sad': Emotion.SADNESS,
            'angry': Emotion.ANGER,
            'calm': Emotion.CALMNESS,
            'excited': Emotion.EXCITEMENT,
            'anxious': Emotion.ANXIETY
        }
    
    def analyze_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Tuple[Emotion, float]:
        """
        Analyze audio to detect emotion
        
        Args:
            audio_data: Audio as numpy array
            sample_rate: Sample rate of audio
            
        Returns:
            (Detected emotion, confidence score)
        """
        try:
            # Extract features
            pitch_mean, pitch_std = self._extract_pitch(audio_data, sample_rate)
            energy = self._extract_energy(audio_data)
            tempo = self._extract_tempo(audio_data, sample_rate)
            spectral_centroid = self._extract_spectral_centroid(audio_data, sample_rate)
            
            # Simple rule-based emotion detection
            # (In production, would use ML model trained on emotion datasets)
            
            # High pitch + high energy + fast tempo = Excited/Happy
            if pitch_mean > 200 and energy > 0.05 and tempo > 120:
                return Emotion.EXCITEMENT, 0.8
            
            # High pitch + moderate energy = Happy
            if pitch_mean > 180 and energy > 0.03:
                return Emotion.HAPPINESS, 0.7
            
            # Low pitch + low energy + slow tempo = Sad
            if pitch_mean < 140 and energy < 0.02 and tempo < 90:
                return Emotion.SADNESS, 0.75
            
            # High energy + variable pitch = Angry
            if energy > 0.06 and pitch_std > 50:
                return Emotion.ANGER, 0.7
            
            # Moderate everything = Calm
            if 140 <= pitch_mean <= 180 and 0.02 <= energy <= 0.04:
                return Emotion.CALMNESS, 0.8
            
            # Default
            return Emotion.CALMNESS, 0.5
            
        except Exception as e:
            print(f"[WARNING]  Error analyzing emotion: {e}")
            return Emotion.CALMNESS, 0.0
    
    def _extract_pitch(self, audio: np.ndarray, sr: int) -> Tuple[float, float]:
        """Extract pitch (fundamental frequency) statistics"""
        try:
            pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
            pitch_values = []
            
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                return np.mean(pitch_values), np.std(pitch_values)
            return 150.0, 20.0  # Default
        except:
            return 150.0, 20.0
    
    def _extract_energy(self, audio: np.ndarray) -> float:
        """Extract energy (RMS) from audio"""
        try:
            rms = librosa.feature.rms(y=audio)
            return float(np.mean(rms))
        except:
            return 0.03
    
    def _extract_tempo(self, audio: np.ndarray, sr: int) -> float:
        """Extract tempo (speech rate)"""
        try:
            onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
            return float(tempo[0]) if len(tempo) > 0 else 100.0
        except:
            return 100.0
    
    def _extract_spectral_centroid(self, audio: np.ndarray, sr: int) -> float:
        """Extract spectral centroid (brightness of sound)"""
        try:
            centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            return float(np.mean(centroid))
        except:
            return 1000.0
