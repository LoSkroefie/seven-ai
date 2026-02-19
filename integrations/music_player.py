"""
Music Player Integration - Seven Can Play Music!

Seven picks songs based on mood, context, or user request,
searches YouTube, and plays audio through pygame.mixer.

Requires: yt-dlp, pygame
"""

import os
import re
import logging
import threading
import tempfile
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger("MusicPlayer")

# Check for yt-dlp
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    logger.warning("yt-dlp not installed — music playback unavailable. pip install yt-dlp")

# Check for pygame
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class MusicPlayer:
    """
    Seven's music playback system.
    
    - Searches YouTube for songs
    - Downloads audio to temp file
    - Plays through pygame.mixer
    - Tracks what's playing for conversational awareness
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.logger = logging.getLogger("MusicPlayer")
        self.available = YT_DLP_AVAILABLE and PYGAME_AVAILABLE
        
        # Cache directory for downloaded audio
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / "Documents" / "Seven" / "music_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self.currently_playing = None  # {title, artist, url, file}
        self.play_history = []
        self.is_playing = False
        self._play_lock = threading.Lock()
        
        # Initialize pygame mixer if not already done
        if PYGAME_AVAILABLE:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
                self.logger.info("[OK] Music player ready")
            except Exception as e:
                self.logger.error(f"pygame mixer init failed: {e}")
                self.available = False
        
        if not self.available:
            self.logger.warning("Music player not available (missing yt-dlp or pygame)")
    
    def search_and_play(self, query: str) -> Dict:
        """
        Search YouTube for a song and play it.
        
        Args:
            query: Song name, artist, or description like "something upbeat"
            
        Returns:
            Dict with 'success', 'title', 'message'
        """
        if not self.available:
            return {
                'success': False,
                'title': None,
                'message': "Music playback isn't available. Install yt-dlp: pip install yt-dlp"
            }
        
        self.logger.info(f"Searching for: {query}")
        
        try:
            # Search YouTube
            info = self._search_youtube(query)
            if not info:
                return {
                    'success': False,
                    'title': None,
                    'message': f"I couldn't find anything for '{query}'"
                }
            
            title = info.get('title', 'Unknown')
            artist = info.get('artist') or info.get('uploader', 'Unknown')
            url = info.get('webpage_url', '')
            
            # Download audio
            audio_file = self._download_audio(info)
            if not audio_file:
                # Fallback: open in browser
                self._open_in_browser(url)
                return {
                    'success': True,
                    'title': title,
                    'message': f"I found '{title}' but couldn't download the audio. I've opened it in your browser instead."
                }
            
            # Play it
            self._play_audio(audio_file, title, artist, url)
            
            return {
                'success': True,
                'title': title,
                'message': f"Now playing: {title} by {artist}"
            }
            
        except Exception as e:
            self.logger.error(f"Music search/play failed: {e}")
            return {
                'success': False,
                'title': None,
                'message': f"Something went wrong trying to play music: {str(e)[:100]}"
            }
    
    def stop(self):
        """Stop currently playing music"""
        if PYGAME_AVAILABLE and pygame.mixer.get_init():
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except Exception:
                pass
        self.is_playing = False
        self.currently_playing = None
        return "Music stopped."
    
    def pause(self):
        """Pause currently playing music"""
        if PYGAME_AVAILABLE and self.is_playing:
            pygame.mixer.music.pause()
            return "Music paused."
        return "Nothing is playing."
    
    def resume(self):
        """Resume paused music"""
        if PYGAME_AVAILABLE and self.currently_playing:
            pygame.mixer.music.unpause()
            self.is_playing = True
            return f"Resuming: {self.currently_playing.get('title', 'music')}"
        return "Nothing to resume."
    
    def get_now_playing(self) -> Optional[str]:
        """Get what's currently playing"""
        if self.is_playing and self.currently_playing:
            return f"{self.currently_playing['title']} by {self.currently_playing.get('artist', 'Unknown')}"
        return None
    
    def _search_youtube(self, query: str) -> Optional[Dict]:
        """Search YouTube and return first result info"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'noplaylist': True,
            'default_search': 'ytsearch1',  # Search YouTube, return 1 result
            'format': 'bestaudio/best',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                
                if info and 'entries' in info and info['entries']:
                    return info['entries'][0]
                elif info and 'title' in info:
                    return info
                    
        except Exception as e:
            self.logger.error(f"YouTube search failed: {e}")
        
        return None
    
    def _download_audio(self, info: Dict) -> Optional[str]:
        """Download audio from YouTube video info"""
        video_id = info.get('id', 'unknown')
        
        # Check cache first
        cached = self.cache_dir / f"{video_id}.mp3"
        if cached.exists():
            self.logger.info(f"Cache hit: {cached}")
            return str(cached)
        
        # Download
        output_template = str(self.cache_dir / f"{video_id}.%(ext)s")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([info['webpage_url']])
            
            # Find the downloaded file
            mp3_file = self.cache_dir / f"{video_id}.mp3"
            if mp3_file.exists():
                self.logger.info(f"Downloaded: {mp3_file}")
                return str(mp3_file)
            
            # Try other extensions
            for ext in ['m4a', 'webm', 'ogg', 'opus', 'wav']:
                alt = self.cache_dir / f"{video_id}.{ext}"
                if alt.exists():
                    self.logger.info(f"Downloaded (non-mp3): {alt}")
                    return str(alt)
                    
        except Exception as e:
            self.logger.error(f"Audio download failed: {e}")
            # FFmpeg might not be available — try direct stream
            return self._try_direct_stream(info)
        
        return None
    
    def _try_direct_stream(self, info: Dict) -> Optional[str]:
        """Try to get a direct audio URL without FFmpeg conversion"""
        video_id = info.get('id', 'unknown')
        output_template = str(self.cache_dir / f"{video_id}.%(ext)s")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'noplaylist': True,
            # No postprocessors — skip FFmpeg
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([info['webpage_url']])
            
            # Find whatever was downloaded
            for f in self.cache_dir.iterdir():
                if f.stem == video_id and f.suffix in ['.webm', '.m4a', '.ogg', '.opus', '.mp3', '.wav']:
                    self.logger.info(f"Direct download: {f}")
                    return str(f)
        except Exception as e:
            self.logger.error(f"Direct stream also failed: {e}")
        
        return None
    
    def _play_audio(self, filepath: str, title: str, artist: str, url: str):
        """Play audio file through pygame.mixer"""
        with self._play_lock:
            try:
                # Stop anything currently playing
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                
                pygame.mixer.music.load(filepath)
                pygame.mixer.music.play()
                
                self.currently_playing = {
                    'title': title,
                    'artist': artist,
                    'url': url,
                    'file': filepath
                }
                self.is_playing = True
                
                # Add to history
                self.play_history.append({
                    'title': title,
                    'artist': artist,
                })
                # Keep history reasonable
                if len(self.play_history) > 50:
                    self.play_history = self.play_history[-50:]
                
                self.logger.info(f"Now playing: {title} by {artist}")
                
            except Exception as e:
                self.logger.error(f"Playback failed: {e}")
                self.is_playing = False
                # Fallback to browser
                self._open_in_browser(url)
    
    def _open_in_browser(self, url: str):
        """Fallback: open URL in browser"""
        if url:
            try:
                import webbrowser
                webbrowser.open(url)
            except Exception:
                pass
    
    def cleanup_cache(self, max_files: int = 50):
        """Clean up old cached audio files"""
        try:
            files = sorted(self.cache_dir.iterdir(), key=lambda f: f.stat().st_mtime)
            if len(files) > max_files:
                for f in files[:len(files) - max_files]:
                    f.unlink()
                self.logger.info(f"Cleaned up {len(files) - max_files} cached audio files")
        except Exception as e:
            self.logger.warning(f"Cache cleanup failed: {e}")
