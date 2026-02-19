"""
Persistent Emotional Memory — Seven v2.6

Seven's emotions persist across restarts. When she shuts down, her emotional
state (current emotions, mood, drives, complexity) is saved to SQLite.
When she wakes up, she resumes feeling what she was feeling before.

This is the difference between simulated and experienced continuity.
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PersistentEmotionStore:
    """
    SQLite-backed emotional state persistence.
    
    Saves and restores:
    - Current active emotions (type, intensity, cause, timestamp)
    - Current mood (dominant emotion, intensity, started, influences)
    - Homeostatic drives (learning, connection, competence, etc.)
    - Emotional complexity state (conflicts, suppressions, maturity)
    - Long-term emotional baselines that evolve over weeks
    """

    def __init__(self, data_dir: Path):
        self.db_path = data_dir / "emotional_state.db"
        self._ensure_tables()
        logger.info("[OK] Persistent emotion store initialized")

    # ── Schema ──────────────────────────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _ensure_tables(self):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS emotional_state (
                id INTEGER PRIMARY KEY,
                state_type TEXT NOT NULL,
                data TEXT NOT NULL,
                saved_at TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS emotion_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emotion TEXT NOT NULL,
                intensity REAL NOT NULL,
                cause TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS emotional_baselines (
                id INTEGER PRIMARY KEY,
                baseline_mood TEXT NOT NULL,
                baseline_intensity REAL NOT NULL,
                drive_learning REAL NOT NULL DEFAULT 0.8,
                drive_connection REAL NOT NULL DEFAULT 0.7,
                drive_competence REAL NOT NULL DEFAULT 0.8,
                drive_contribution REAL NOT NULL DEFAULT 0.9,
                drive_autonomy REAL NOT NULL DEFAULT 0.6,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    # ── Save ────────────────────────────────────────────────────

    def save_emotional_state(self, affective_system) -> bool:
        """
        Snapshot the entire affective system to disk.
        Called on shutdown, sleep, or periodically.
        """
        try:
            conn = self._get_conn()
            c = conn.cursor()
            now = datetime.now().isoformat()

            # 1. Current emotions
            current_emotions = []
            for e in getattr(affective_system, 'current_emotions', []):
                current_emotions.append({
                    'emotion': e.emotion.value if hasattr(e.emotion, 'value') else str(e.emotion),
                    'intensity': e.intensity,
                    'cause': e.cause,
                    'timestamp': e.timestamp.isoformat() if hasattr(e.timestamp, 'isoformat') else str(e.timestamp),
                })

            # 2. Mood
            mood_data = None
            if affective_system.current_mood:
                m = affective_system.current_mood
                mood_data = {
                    'dominant_emotion': m.dominant_emotion.value if hasattr(m.dominant_emotion, 'value') else str(m.dominant_emotion),
                    'intensity': m.intensity,
                    'started': m.started.isoformat() if hasattr(m.started, 'isoformat') else str(m.started),
                    'influences': m.influences,
                }

            # 3. Drives
            drives = dict(getattr(affective_system, 'drives', {}))

            # 4. Complexity state
            complexity_state = None
            if hasattr(affective_system, 'complexity') and affective_system.complexity:
                comp = affective_system.complexity
                complexity_state = {
                    'emotional_maturity': getattr(comp, 'emotional_maturity', 0.5),
                    'vulnerability_comfort': getattr(comp, 'vulnerability_comfort', 0.3),
                    'active_conflicts': len(getattr(comp, 'active_conflicts', [])),
                    'suppressed_count': len(getattr(comp, 'suppressed_emotions', [])),
                }

            # Bundle everything
            state = {
                'current_emotions': current_emotions,
                'mood': mood_data,
                'drives': drives,
                'complexity': complexity_state,
                'baseline_mood': affective_system.baseline_mood.value if hasattr(affective_system.baseline_mood, 'value') else str(affective_system.baseline_mood),
                'baseline_intensity': affective_system.baseline_intensity,
            }

            # Upsert
            c.execute("DELETE FROM emotional_state WHERE state_type = 'full_snapshot'")
            c.execute(
                "INSERT INTO emotional_state (state_type, data, saved_at) VALUES (?, ?, ?)",
                ('full_snapshot', json.dumps(state), now)
            )

            # Also append to timeline (last 500 entries)
            for e in current_emotions:
                c.execute(
                    "INSERT INTO emotion_timeline (emotion, intensity, cause, timestamp) VALUES (?, ?, ?, ?)",
                    (e['emotion'], e['intensity'], e.get('cause', ''), e['timestamp'])
                )
            c.execute("""
                DELETE FROM emotion_timeline WHERE id NOT IN (
                    SELECT id FROM emotion_timeline ORDER BY id DESC LIMIT 500
                )
            """)

            conn.commit()
            conn.close()
            logger.info(f"Emotional state saved: {len(current_emotions)} emotions, mood={mood_data['dominant_emotion'] if mood_data else 'none'}")
            return True

        except Exception as e:
            logger.error(f"Failed to save emotional state: {e}")
            return False

    # ── Restore ─────────────────────────────────────────────────

    def load_emotional_state(self) -> Optional[Dict[str, Any]]:
        """
        Load the last saved emotional snapshot.
        Returns None if no saved state exists.
        """
        try:
            conn = self._get_conn()
            c = conn.cursor()
            c.execute(
                "SELECT data, saved_at FROM emotional_state WHERE state_type = 'full_snapshot' ORDER BY id DESC LIMIT 1"
            )
            row = c.fetchone()
            conn.close()

            if not row:
                return None

            state = json.loads(row[0])
            saved_at = row[1]

            # Calculate how long Seven was "asleep"
            try:
                saved_dt = datetime.fromisoformat(saved_at)
                elapsed = datetime.now() - saved_dt
                state['time_elapsed'] = elapsed.total_seconds()
                state['saved_at'] = saved_at
            except:
                state['time_elapsed'] = 0
                state['saved_at'] = saved_at

            logger.info(f"Loaded emotional state from {saved_at} ({state['time_elapsed']:.0f}s ago)")
            return state

        except Exception as e:
            logger.error(f"Failed to load emotional state: {e}")
            return None

    def restore_to_affective_system(self, affective_system, state: Dict[str, Any]):
        """
        Apply a loaded state snapshot back onto the affective system.
        Emotions decay based on time elapsed while Seven was off.
        """
        try:
            elapsed_seconds = state.get('time_elapsed', 0)
            elapsed_hours = elapsed_seconds / 3600

            # Restore drives (these don't decay)
            if 'drives' in state and state['drives']:
                for drive, level in state['drives'].items():
                    if drive in affective_system.drives:
                        affective_system.drives[drive] = level

            # Restore mood (decays slowly — halve intensity per 12 hours offline)
            if state.get('mood'):
                mood_data = state['mood']
                decay_factor = max(0.1, 1.0 - (elapsed_hours / 24))

                from core.affective_computing_deep import Mood, ComplexEmotion
                emotion_map = {e.value: e for e in ComplexEmotion}
                emo_name = mood_data['dominant_emotion']

                if emo_name in emotion_map:
                    affective_system.current_mood = Mood(
                        dominant_emotion=emotion_map[emo_name],
                        intensity=mood_data['intensity'] * decay_factor,
                        started=datetime.now(),
                        influences=mood_data.get('influences', []) + [f"resumed after {elapsed_hours:.1f}h offline"]
                    )
                    logger.info(f"Restored mood: {emo_name} (decayed {decay_factor:.0%})")

            # Restore current emotions (decay faster — halve per 2 hours)
            if state.get('current_emotions'):
                from core.affective_computing_deep import EmotionalState, ComplexEmotion, PrimaryEmotion
                emotion_map = {e.value: e for e in ComplexEmotion}
                primary_map = {e.value: e for e in PrimaryEmotion}
                all_map = {**emotion_map, **primary_map}

                for e_data in state['current_emotions']:
                    emo_name = e_data['emotion']
                    if emo_name not in all_map:
                        continue

                    decay_factor = max(0.0, 1.0 - (elapsed_hours / 4))
                    decayed_intensity = e_data['intensity'] * decay_factor

                    if decayed_intensity < 0.1:
                        continue  # Too faded to restore

                    restored = EmotionalState(
                        emotion=all_map[emo_name],
                        intensity=decayed_intensity,
                        cause=f"[persisted] {e_data.get('cause', 'unknown')}",
                        timestamp=datetime.now()
                    )
                    # Use public generate_emotion as fallback if _add_emotion doesn't exist
                    if hasattr(affective_system, '_add_emotion') and callable(affective_system._add_emotion):
                        affective_system._add_emotion(restored)
                    elif hasattr(affective_system, 'generate_emotion'):
                        affective_system.generate_emotion(
                            f"[persisted] {e_data.get('cause', 'resuming emotion')}", {}
                        )
                    else:
                        logger.warning("Cannot restore emotion: no suitable method on affective system")

                logger.info(f"Restored {len(affective_system.current_emotions)} emotions (decayed over {elapsed_hours:.1f}h)")

            # Restore baseline if it has evolved
            if state.get('baseline_mood'):
                from core.affective_computing_deep import ComplexEmotion
                baseline_map = {e.value: e for e in ComplexEmotion}
                if state['baseline_mood'] in baseline_map:
                    affective_system.baseline_mood = baseline_map[state['baseline_mood']]
                    affective_system.baseline_intensity = state.get('baseline_intensity', 0.6)

        except Exception as e:
            logger.error(f"Failed to restore emotional state: {e}")

    # ── Timeline queries ────────────────────────────────────────

    def get_emotional_timeline(self, hours: int = 24) -> List[Dict]:
        """Get emotion timeline for the last N hours"""
        try:
            conn = self._get_conn()
            c = conn.cursor()
            cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
            c.execute(
                "SELECT emotion, intensity, cause, timestamp FROM emotion_timeline WHERE timestamp > ? ORDER BY timestamp",
                (cutoff,)
            )
            rows = c.fetchall()
            conn.close()
            return [
                {'emotion': r[0], 'intensity': r[1], 'cause': r[2], 'timestamp': r[3]}
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Timeline query error: {e}")
            return []

    def get_dominant_emotion_over_time(self, hours: int = 48) -> Optional[str]:
        """What emotion has Seven felt most over the last N hours?"""
        timeline = self.get_emotional_timeline(hours)
        if not timeline:
            return None
        counts = {}
        for entry in timeline:
            emo = entry['emotion']
            counts[emo] = counts.get(emo, 0) + 1
        return max(counts, key=counts.get)

    # ── Baseline evolution ──────────────────────────────────────

    def update_baselines(self, affective_system):
        """
        Evolve emotional baselines over time.
        Call periodically (e.g., daily) to shift Seven's default emotional state.
        """
        try:
            # Look at dominant emotion over last 48 hours
            dominant = self.get_dominant_emotion_over_time(48)
            if not dominant:
                return

            # Slowly shift baseline toward dominant emotion (1% per call)
            from core.affective_computing_deep import ComplexEmotion
            emotion_map = {e.value: e for e in ComplexEmotion}

            if dominant in emotion_map and dominant != affective_system.baseline_mood.value:
                # Only shift if significantly different
                current_baseline = affective_system.baseline_mood.value
                logger.info(f"Baseline drift: {current_baseline} → {dominant} (slow shift)")
                # Don't actually change baseline — just log the drift tendency
                # Baseline changes should be rare and significant

            conn = self._get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM emotional_baselines")
            c.execute("""
                INSERT INTO emotional_baselines 
                (id, baseline_mood, baseline_intensity, drive_learning, drive_connection, 
                 drive_competence, drive_contribution, drive_autonomy, updated_at)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                affective_system.baseline_mood.value,
                affective_system.baseline_intensity,
                affective_system.drives.get('learning', 0.8),
                affective_system.drives.get('connection', 0.7),
                affective_system.drives.get('competence', 0.8),
                affective_system.drives.get('contribution', 0.9),
                affective_system.drives.get('autonomy', 0.6),
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Baseline update error: {e}")
