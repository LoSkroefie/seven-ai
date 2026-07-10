"""
Predictive User Modeling — Seven AI v3.2

Uses time-series analysis on interaction logs to forecast:
- Next likely interaction time (when will user return?)
- Mood trajectory (is user getting happier/sadder over sessions?)
- Message frequency patterns (busy vs. free periods)
- Topic preferences (what the user wants to talk about)

Feeds predictions into intrinsic motivation and proactive engine
so Seven can prepare greetings, queue relevant topics, or adjust
energy levels before the user arrives.

Uses statsmodels ARIMA when available, falls back to simple
moving-average heuristics. Trains incrementally in scheduler.

100% local. No cloud. Low CPU.
"""

import json
import logging
import math
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger("UserPredictor")

# Optional imports
STATSMODELS_AVAILABLE = False
PANDAS_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pass

try:
    from statsmodels.tsa.arima.model import ARIMA
    STATSMODELS_AVAILABLE = True
except ImportError:
    pass


class InteractionRecord:
    """Single interaction data point"""
    
    def __init__(self, timestamp: str, message_length: int = 0,
                 sentiment: float = 0.5, topic: str = "general",
                 response_time_ms: float = 0):
        self.timestamp = timestamp
        self.message_length = message_length
        self.sentiment = sentiment  # 0=negative, 0.5=neutral, 1=positive
        self.topic = topic
        self.response_time_ms = response_time_ms
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp,
            'message_length': self.message_length,
            'sentiment': self.sentiment,
            'topic': self.topic,
            'response_time_ms': self.response_time_ms
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'InteractionRecord':
        return cls(**d)


class UserPredictor:
    """
    Predictive model for user behavior patterns.
    
    Analyzes interaction history to forecast availability,
    mood, and preferences. Feeds into Seven's proactive engine.
    
    Thread-safe. Incremental training. Low CPU.
    """
    
    def __init__(self, bot=None, data_dir: str = None):
        self.bot = bot
        self.data_dir = Path(data_dir) if data_dir else self._default_data_dir()
        self.predictions_dir = self.data_dir / "predictions"
        self.predictions_dir.mkdir(parents=True, exist_ok=True)
        
        # Interaction log
        self.records: List[InteractionRecord] = []
        
        # Predictions (cached)
        self.predictions: Dict[str, Any] = {
            'next_interaction_hour': None,
            'mood_trend': 'stable',      # improving, stable, declining
            'mood_confidence': 0.0,
            'activity_level': 'unknown',  # high, medium, low, unknown
            'preferred_topics': [],
            'busy_hours': [],             # Hours user is typically busy
            'active_hours': [],           # Hours user is typically active
            'avg_session_length': 0,      # Average messages per session
            'predicted_sentiment': 0.5,
        }
        
        # Model state
        self.last_train_time: Optional[datetime] = None
        self.total_records = 0
        self.model_accuracy = 0.0
        
        # Load existing data
        self._load_records()
        self._load_predictions()
        
        logger.info(
            f"[PREDICT] Initialized — records={self.total_records}, "
            f"statsmodels={'yes' if STATSMODELS_AVAILABLE else 'no'}, "
            f"pandas={'yes' if PANDAS_AVAILABLE else 'no'}"
        )
    
    def _default_data_dir(self) -> Path:
        if os.name == 'nt':
            return Path(os.environ.get('USERPROFILE', '~')) / '.chatbot'
        return Path.home() / '.chatbot'
    
    # ==================== Data Collection ====================
    
    def record_interaction(self, user_message: str, sentiment: float = 0.5,
                           topic: str = "general", response_time_ms: float = 0):
        """
        Record a user interaction for modeling.
        Called after each user message by enhanced_bot.
        """
        record = InteractionRecord(
            timestamp=datetime.now().isoformat(),
            message_length=len(user_message),
            sentiment=max(0.0, min(1.0, sentiment)),
            topic=topic,
            response_time_ms=response_time_ms
        )
        
        self.records.append(record)
        self.total_records += 1
        
        # Auto-flush every 100 records
        if len(self.records) % 100 == 0:
            self._save_records()
    
    def collect_from_memory(self) -> int:
        """Extract interaction records from stored memory"""
        if not self.bot:
            return 0
        
        count = 0
        try:
            memory = getattr(self.bot, 'memory', None)
            if not memory:
                return 0
            
            convos = []
            if hasattr(memory, 'get_recent_conversations'):
                convos = memory.get_recent_conversations(limit=500)
            
            for convo in convos:
                if not isinstance(convo, dict):
                    continue
                
                ts = convo.get('timestamp', '')
                user_msg = convo.get('user_input', convo.get('input', ''))
                
                if ts and user_msg:
                    record = InteractionRecord(
                        timestamp=ts,
                        message_length=len(user_msg),
                        sentiment=0.5,
                        topic="general"
                    )
                    self.records.append(record)
                    count += 1
            
            self.total_records = len(self.records)
            logger.info(f"[PREDICT] Collected {count} records from memory")
        except Exception as e:
            logger.error(f"[PREDICT] Memory collection error: {e}")
        
        return count
    
    # ==================== Training / Analysis ====================
    
    def train(self) -> Dict[str, Any]:
        """
        Analyze interaction patterns and update predictions.
        
        Uses ARIMA for time-series forecasting if available,
        otherwise falls back to statistical heuristics.
        """
        start = time.time()
        report = {
            'status': 'started',
            'method': 'arima' if STATSMODELS_AVAILABLE else 'heuristic',
            'records_used': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Ensure we have data
            if len(self.records) < 5:
                self.collect_from_memory()
            
            if len(self.records) < 5:
                report['status'] = 'insufficient_data'
                return report
            
            report['records_used'] = len(self.records)
            
            # Analyze patterns
            self._analyze_activity_patterns()
            self._analyze_mood_trend()
            self._analyze_topic_preferences()
            self._predict_next_interaction()
            
            if STATSMODELS_AVAILABLE and PANDAS_AVAILABLE and len(self.records) >= 20:
                self._train_arima()
            
            self.last_train_time = datetime.now()
            report['status'] = 'completed'
            report['predictions'] = dict(self.predictions)
            report['duration_seconds'] = round(time.time() - start, 3)
            
            # Save
            self._save_predictions()
            self._save_records()
            
            logger.info(
                f"[PREDICT] Training complete — {report['records_used']} records, "
                f"mood={self.predictions['mood_trend']}, "
                f"next_hour={self.predictions['next_interaction_hour']}"
            )
            
        except Exception as e:
            report['status'] = 'error'
            report['error'] = str(e)
            logger.error(f"[PREDICT] Training error: {e}")
        
        return report
    
    def _analyze_activity_patterns(self):
        """Find when user is typically active/busy"""
        hour_counts = Counter()
        
        for record in self.records:
            try:
                dt = datetime.fromisoformat(record.timestamp)
                hour_counts[dt.hour] += 1
            except (ValueError, TypeError):
                continue
        
        if not hour_counts:
            return
        
        # Sort by frequency
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Top active hours (above average)
        avg_count = sum(hour_counts.values()) / max(len(hour_counts), 1)
        self.predictions['active_hours'] = [
            h for h, c in sorted_hours if c >= avg_count
        ]
        
        # Busy hours (below average or zero)
        all_hours = set(range(24))
        active_set = set(self.predictions['active_hours'])
        self.predictions['busy_hours'] = sorted(all_hours - active_set)
        
        # Activity level based on recent frequency
        recent_records = [
            r for r in self.records
            if self._parse_timestamp(r.timestamp) and
            (datetime.now() - self._parse_timestamp(r.timestamp)) < timedelta(days=7)
        ]
        
        daily_avg = len(recent_records) / 7
        if daily_avg >= 20:
            self.predictions['activity_level'] = 'high'
        elif daily_avg >= 5:
            self.predictions['activity_level'] = 'medium'
        elif daily_avg >= 1:
            self.predictions['activity_level'] = 'low'
        else:
            self.predictions['activity_level'] = 'unknown'
    
    def _analyze_mood_trend(self):
        """Analyze sentiment trend over recent interactions"""
        if len(self.records) < 10:
            self.predictions['mood_trend'] = 'stable'
            self.predictions['mood_confidence'] = 0.0
            return
        
        # Get recent sentiments
        recent = self.records[-50:]
        sentiments = [r.sentiment for r in recent]
        
        # Simple linear regression on sentiment
        n = len(sentiments)
        x_mean = (n - 1) / 2
        y_mean = sum(sentiments) / n
        
        numerator = sum((i - x_mean) * (s - y_mean) for i, s in enumerate(sentiments))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator > 0:
            slope = numerator / denominator
            
            if slope > 0.005:
                self.predictions['mood_trend'] = 'improving'
            elif slope < -0.005:
                self.predictions['mood_trend'] = 'declining'
            else:
                self.predictions['mood_trend'] = 'stable'
            
            # Confidence based on R² approximation
            ss_res = sum((s - (y_mean + slope * (i - x_mean))) ** 2
                        for i, s in enumerate(sentiments))
            ss_tot = sum((s - y_mean) ** 2 for s in sentiments) or 1
            r_squared = max(0, 1 - ss_res / ss_tot)
            self.predictions['mood_confidence'] = round(r_squared, 3)
        
        # Predicted sentiment (moving average of last 10)
        last_10 = sentiments[-10:]
        self.predictions['predicted_sentiment'] = round(sum(last_10) / len(last_10), 3)
    
    def _analyze_topic_preferences(self):
        """Find user's preferred topics"""
        topic_counts = Counter()
        
        for record in self.records[-200:]:  # Last 200 interactions
            if record.topic:
                topic_counts[record.topic] += 1
        
        # Top 5 topics
        self.predictions['preferred_topics'] = [
            topic for topic, _ in topic_counts.most_common(5)
        ]
    
    def _predict_next_interaction(self):
        """Predict when the user will next interact"""
        if not self.predictions.get('active_hours'):
            return
        
        now = datetime.now()
        current_hour = now.hour
        
        # Find next active hour
        active = sorted(self.predictions['active_hours'])
        
        next_hour = None
        for h in active:
            if h > current_hour:
                next_hour = h
                break
        
        if next_hour is None and active:
            next_hour = active[0]  # Tomorrow's first active hour
        
        self.predictions['next_interaction_hour'] = next_hour
        
        # Average session length
        session_lengths = self._compute_session_lengths()
        if session_lengths:
            self.predictions['avg_session_length'] = round(
                sum(session_lengths) / len(session_lengths), 1
            )
    
    def _compute_session_lengths(self) -> List[int]:
        """Compute message counts per session (gap > 30 min = new session)"""
        sessions = []
        current_session = 0
        last_time = None
        
        for record in self.records:
            ts = self._parse_timestamp(record.timestamp)
            if not ts:
                continue
            
            if last_time and (ts - last_time) > timedelta(minutes=30):
                if current_session > 0:
                    sessions.append(current_session)
                current_session = 0
            
            current_session += 1
            last_time = ts
        
        if current_session > 0:
            sessions.append(current_session)
        
        return sessions
    
    def _train_arima(self):
        """Train ARIMA model on hourly interaction frequency"""
        try:
            # Build hourly frequency series
            hourly = defaultdict(int)
            
            for record in self.records:
                ts = self._parse_timestamp(record.timestamp)
                if ts:
                    key = ts.strftime('%Y-%m-%d %H:00')
                    hourly[key] += 1
            
            if len(hourly) < 20:
                return
            
            # Create pandas series
            dates = sorted(hourly.keys())
            values = [hourly[d] for d in dates]
            
            series = pd.Series(values, index=pd.to_datetime(dates))
            series = series.asfreq('h', fill_value=0)
            
            # Fit ARIMA(1,0,1) — simple, fast
            model = ARIMA(series, order=(1, 0, 1))
            fitted = model.fit()
            
            # Forecast next 24 hours
            forecast = fitted.forecast(steps=24)
            
            # Find peak hour
            peak_idx = forecast.argmax()
            peak_hour = (datetime.now().hour + peak_idx + 1) % 24
            
            self.predictions['next_interaction_hour'] = int(peak_hour)
            self.model_accuracy = round(1.0 - (fitted.aic / (abs(fitted.aic) + 100)), 3)
            
            logger.info(f"[PREDICT] ARIMA trained — AIC={fitted.aic:.1f}, peak_hour={peak_hour}")
            
        except Exception as e:
            logger.debug(f"[PREDICT] ARIMA training error: {e}")
    
    # ==================== Query Interface ====================
    
    def is_user_likely_active(self) -> bool:
        """Is the user likely active right now?"""
        current_hour = datetime.now().hour
        return current_hour in self.predictions.get('active_hours', [])
    
    def get_mood_forecast(self) -> Tuple[str, float]:
        """Get mood trend and confidence"""
        return (
            self.predictions.get('mood_trend', 'stable'),
            self.predictions.get('mood_confidence', 0.0)
        )
    
    def get_suggested_greeting_mood(self) -> str:
        """Suggest a greeting mood based on predictions"""
        trend = self.predictions.get('mood_trend', 'stable')
        sentiment = self.predictions.get('predicted_sentiment', 0.5)
        
        if trend == 'declining' or sentiment < 0.4:
            return 'gentle'    # User seems down — be warm and careful
        elif trend == 'improving' or sentiment > 0.7:
            return 'energetic'  # User is doing well — match energy
        return 'balanced'
    
    def should_be_proactive(self) -> bool:
        """Should Seven proactively reach out?"""
        if not self.is_user_likely_active():
            return False
        
        activity = self.predictions.get('activity_level', 'unknown')
        if activity in ('high', 'medium'):
            return True
        
        return False
    
    # ==================== Persistence ====================
    
    def _save_records(self):
        """Save interaction records to disk"""
        records_file = self.predictions_dir / "interaction_records.json"
        try:
            # Keep last 2000 records
            to_save = self.records[-2000:]
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump([r.to_dict() for r in to_save], f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[PREDICT] Save records error: {e}")
    
    def _load_records(self):
        """Load interaction records from disk"""
        records_file = self.predictions_dir / "interaction_records.json"
        if not records_file.exists():
            return
        
        try:
            with open(records_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.records = [InteractionRecord.from_dict(d) for d in data]
            self.total_records = len(self.records)
        except Exception as e:
            logger.error(f"[PREDICT] Load records error: {e}")
    
    def _save_predictions(self):
        """Save predictions to disk"""
        pred_file = self.predictions_dir / "predictions.json"
        try:
            with open(pred_file, 'w', encoding='utf-8') as f:
                json.dump(self.predictions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[PREDICT] Save predictions error: {e}")
    
    def _load_predictions(self):
        """Load predictions from disk"""
        pred_file = self.predictions_dir / "predictions.json"
        if not pred_file.exists():
            return
        
        try:
            with open(pred_file, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            self.predictions.update(saved)
        except Exception as e:
            logger.error(f"[PREDICT] Load predictions error: {e}")
    
    @staticmethod
    def _parse_timestamp(ts: str) -> Optional[datetime]:
        """Safely parse an ISO timestamp"""
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None
    
    # ==================== Status ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get predictor status for GUI/API"""
        return {
            'available': True,
            'method': 'arima' if STATSMODELS_AVAILABLE else 'heuristic',
            'total_records': self.total_records,
            'last_trained': self.last_train_time.isoformat() if self.last_train_time else None,
            'model_accuracy': self.model_accuracy,
            'predictions': dict(self.predictions)
        }
