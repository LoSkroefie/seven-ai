"""
Weather Reporter Extension — Seven AI

Fetches weather data for a configured location and provides
proactive weather context. Uses wttr.in (no API key needed).
"""

import logging
import json
from datetime import datetime
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("WeatherReporter")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class WeatherReporterExtension(SevenExtension):
    """Fetch and report weather conditions"""

    name = "Weather Reporter"
    version = "1.0"
    description = "Fetches weather data and provides proactive weather context"
    author = "Seven AI"

    schedule_interval_minutes = 180  # Every 3 hours
    needs_ollama = False

    def init(self, bot=None):
        self.bot = bot
        self.last_weather = None
        self.last_fetch = None
        self.location = None

        # Try to get location from config
        try:
            import config
            self.location = getattr(config, 'WEATHER_LOCATION', None)
        except ImportError:
            pass

    def run(self, context: dict = None) -> dict:
        if not HAS_REQUESTS:
            return {"message": "requests library not installed", "status": "unavailable"}

        location = self.location or "auto"  # wttr.in auto-detects from IP

        try:
            url = f"https://wttr.in/{location}?format=j1"
            resp = requests.get(url, timeout=10, headers={"User-Agent": "SevenAI/1.0"})
            resp.raise_for_status()
            data = resp.json()

            current = data.get("current_condition", [{}])[0]
            temp_c = current.get("temp_C", "?")
            feels_like = current.get("FeelsLikeC", "?")
            desc = current.get("weatherDesc", [{}])[0].get("value", "Unknown")
            humidity = current.get("humidity", "?")
            wind_kmph = current.get("windspeedKmph", "?")
            wind_dir = current.get("winddir16Point", "")

            # Location info
            area = data.get("nearest_area", [{}])[0]
            city = area.get("areaName", [{}])[0].get("value", "Unknown")
            country = area.get("country", [{}])[0].get("value", "")

            weather_str = (
                f"Weather in {city}, {country}: {desc}, {temp_c}C "
                f"(feels like {feels_like}C), "
                f"humidity {humidity}%, wind {wind_kmph} km/h {wind_dir}"
            )

            # Check for forecast alerts
            forecast = data.get("weather", [])
            alerts = []
            if forecast:
                today = forecast[0]
                max_temp = today.get("maxtempC", "?")
                min_temp = today.get("mintempC", "?")
                weather_str += f" | Today: {min_temp}C - {max_temp}C"

                # Simple alerts
                try:
                    if int(max_temp) > 35:
                        alerts.append("Extreme heat warning")
                    elif int(min_temp) < 0:
                        alerts.append("Freezing temperatures")
                    if int(wind_kmph) > 50:
                        alerts.append("Strong winds")
                except (ValueError, TypeError):
                    pass

            self.last_weather = {
                "description": desc,
                "temp_c": temp_c,
                "feels_like": feels_like,
                "humidity": humidity,
                "wind": f"{wind_kmph} km/h {wind_dir}",
                "city": city,
                "country": country,
                "alerts": alerts,
            }
            self.last_fetch = datetime.now().isoformat()

            result = {"message": weather_str, "weather": self.last_weather, "status": "ok"}
            if alerts:
                result["alerts"] = alerts
            return result

        except Exception as e:
            logger.warning(f"[Weather] Fetch failed: {e}")
            return {"message": f"Weather fetch failed: {e}", "status": "error"}

    def on_message(self, user_message: str, bot_response: str):
        """Provide weather context when relevant"""
        lower = user_message.lower()
        weather_words = ["weather", "temperature", "rain", "cold", "hot", "sunny",
                         "cloudy", "windy", "outside", "go out"]
        if any(w in lower for w in weather_words) and self.last_weather:
            w = self.last_weather
            return f"By the way, it's currently {w['description']}, {w['temp_c']}C in {w['city']}."
        return None

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "last_weather": self.last_weather,
            "last_fetch": self.last_fetch,
            "location": self.location or "auto-detect",
            "running": True,
        }
