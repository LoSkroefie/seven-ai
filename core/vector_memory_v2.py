"""
Seven AI — Enhanced Vector Memory v2

Upgrades the basic ChromaDB vector memory with:
- Multiple collections (conversations, knowledge, emotions, goals)
- Emotion-weighted recall (emotional memories are stronger)
- Time-decay scoring (recent memories rank higher)
- Metadata-rich storage (emotion, relationship stage, topic tags)
- Memory consolidation (compress old memories into summaries)
- Cross-collection search (find connections across memory types)

Inspired by PentAGI's layered memory: vector store + knowledge base + episodic.

Usage:
    from core.vector_memory_v2 import EnhancedVectorMemory

    mem = EnhancedVectorMemory()
    mem.store_conversation("What's your favorite color?", "I find blue calming", emotion="CALM")
    mem.store_knowledge("User prefers direct communication", source="observation")
    mem.store_emotion_event("Felt genuine surprise when user shared good news", intensity=0.9)

    results = mem.recall("color preferences", memory_type="all")
"""

import logging
import math
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

try:
    import config
    DATA_DIR = getattr(config, 'DATA_DIR', Path.home() / '.chatbot')
except ImportError:
    DATA_DIR = Path.home() / '.chatbot'


class MemoryType:
    """Memory collection types"""
    CONVERSATION = "conversations"
    KNOWLEDGE = "knowledge"
    EMOTION = "emotion_events"
    GOAL = "goals_and_plans"
    OBSERVATION = "user_observations"


class EnhancedVectorMemory:
    """
    Multi-collection semantic memory with emotion-weighted recall.
    """

    COLLECTIONS = [
        MemoryType.CONVERSATION,
        MemoryType.KNOWLEDGE,
        MemoryType.EMOTION,
        MemoryType.GOAL,
        MemoryType.OBSERVATION,
    ]

    def __init__(self, persist_directory: Optional[str] = None,
                 logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("VectorMemoryV2")

        if not HAS_CHROMADB:
            self.logger.warning("ChromaDB not installed — vector memory disabled")
            self.client = None
            self._collections = {}
            return

        if persist_directory is None:
            persist_directory = str(Path(DATA_DIR) / "chroma_v2")

        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            self._collections = {}
            for name in self.COLLECTIONS:
                self._collections[name] = self.client.get_or_create_collection(
                    name=name,
                    metadata={"description": f"Seven AI {name} memory"}
                )
            total = sum(c.count() for c in self._collections.values())
            self.logger.info(f"Vector Memory v2 loaded: {total} total memories across {len(self.COLLECTIONS)} collections")
        except Exception as e:
            self.logger.error(f"Vector memory init error: {e}")
            self.client = None
            self._collections = {}

    def _get_collection(self, memory_type: str):
        """Get a collection by type"""
        return self._collections.get(memory_type)

    def _make_id(self, prefix: str = "mem") -> str:
        """Generate unique ID"""
        return f"{prefix}_{datetime.now().timestamp()}"

    def _sanitize(self, text: str) -> str:
        """Clean text for storage"""
        if not text:
            return ""
        return text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')

    # === Storage Methods ===

    def store_conversation(self, user_input: str, bot_response: str,
                           emotion: str = "neutral", topics: Optional[List[str]] = None,
                           relationship_stage: str = "",
                           metadata: Optional[Dict] = None):
        """Store a conversation turn"""
        col = self._get_collection(MemoryType.CONVERSATION)
        if not col:
            return

        user_safe = self._sanitize(user_input)
        bot_safe = self._sanitize(bot_response)
        doc = f"User: {user_safe}\nSeven: {bot_safe}"

        meta = {
            "timestamp": datetime.now().isoformat(),
            "emotion": emotion,
            "user_input": user_safe[:500],
            "bot_response": bot_safe[:500],
            "relationship_stage": relationship_stage,
            "topics": ",".join(topics) if topics else "",
        }
        if metadata:
            meta.update({k: str(v)[:200] for k, v in metadata.items()})

        try:
            col.add(documents=[doc], metadatas=[meta], ids=[self._make_id("conv")])
        except Exception as e:
            self.logger.warning(f"Error storing conversation: {e}")

    def store_knowledge(self, fact: str, source: str = "observation",
                        confidence: float = 0.8, category: str = "general"):
        """Store a knowledge fact about the user or world"""
        col = self._get_collection(MemoryType.KNOWLEDGE)
        if not col:
            return

        meta = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "confidence": str(confidence),
            "category": category,
        }
        try:
            col.add(
                documents=[self._sanitize(fact)],
                metadatas=[meta],
                ids=[self._make_id("know")]
            )
        except Exception as e:
            self.logger.warning(f"Error storing knowledge: {e}")

    def store_emotion_event(self, description: str, emotion: str = "",
                            intensity: float = 0.5, trigger: str = ""):
        """Store a significant emotional event"""
        col = self._get_collection(MemoryType.EMOTION)
        if not col:
            return

        meta = {
            "timestamp": datetime.now().isoformat(),
            "emotion": emotion,
            "intensity": str(intensity),
            "trigger": trigger[:200],
        }
        try:
            col.add(
                documents=[self._sanitize(description)],
                metadatas=[meta],
                ids=[self._make_id("emo")]
            )
        except Exception as e:
            self.logger.warning(f"Error storing emotion event: {e}")

    def store_goal(self, goal: str, status: str = "active",
                   priority: int = 5, context: str = ""):
        """Store a goal or plan"""
        col = self._get_collection(MemoryType.GOAL)
        if not col:
            return

        meta = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "priority": str(priority),
            "context": context[:200],
        }
        try:
            col.add(
                documents=[self._sanitize(goal)],
                metadatas=[meta],
                ids=[self._make_id("goal")]
            )
        except Exception as e:
            self.logger.warning(f"Error storing goal: {e}")

    def store_observation(self, observation: str, category: str = "behavior",
                          confidence: float = 0.7):
        """Store an observation about the user"""
        col = self._get_collection(MemoryType.OBSERVATION)
        if not col:
            return

        meta = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "confidence": str(confidence),
        }
        try:
            col.add(
                documents=[self._sanitize(observation)],
                metadatas=[meta],
                ids=[self._make_id("obs")]
            )
        except Exception as e:
            self.logger.warning(f"Error storing observation: {e}")

    # === Recall Methods ===

    def recall(self, query: str, memory_type: str = "all",
               n_results: int = 5, time_weight: float = 0.3) -> List[Dict]:
        """
        Semantic recall with optional time-decay weighting.

        Args:
            query: What to search for
            memory_type: Collection to search, or "all" for cross-collection
            n_results: Max results per collection
            time_weight: 0.0 = pure semantic, 1.0 = heavily favor recent

        Returns:
            List of memories sorted by combined relevance score
        """
        if not self._collections:
            return []

        if memory_type == "all":
            collections_to_search = list(self._collections.items())
        else:
            col = self._get_collection(memory_type)
            if not col:
                return []
            collections_to_search = [(memory_type, col)]

        all_results = []
        for col_name, col in collections_to_search:
            if col.count() == 0:
                continue
            try:
                actual_n = min(n_results, col.count())
                results = col.query(
                    query_texts=[query],
                    n_results=actual_n,
                )
                if results and results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        meta = results['metadatas'][0][i] if results['metadatas'] else {}
                        distance = results['distances'][0][i] if results['distances'] else 1.0

                        # Semantic score (lower distance = better match)
                        semantic_score = max(0, 1.0 - (distance / 2.0))

                        # Time decay score
                        time_score = self._time_decay_score(meta.get('timestamp', ''))

                        # Combined score
                        combined = (1 - time_weight) * semantic_score + time_weight * time_score

                        # Emotion intensity boost
                        intensity = float(meta.get('intensity', '0.5'))
                        if intensity > 0.7:
                            combined *= 1.0 + (intensity - 0.7) * 0.5

                        all_results.append({
                            'text': doc,
                            'collection': col_name,
                            'metadata': meta,
                            'semantic_score': round(semantic_score, 3),
                            'time_score': round(time_score, 3),
                            'combined_score': round(combined, 3),
                            'distance': distance,
                        })
            except Exception as e:
                self.logger.warning(f"Error searching {col_name}: {e}")

        # Sort by combined score descending
        all_results.sort(key=lambda x: -x['combined_score'])
        return all_results[:n_results * 2]  # Return extra from cross-collection

    def recall_conversations(self, query: str, n_results: int = 5) -> List[Dict]:
        """Shortcut: recall from conversations only"""
        return self.recall(query, MemoryType.CONVERSATION, n_results)

    def recall_about_user(self, query: str, n_results: int = 5) -> List[Dict]:
        """Recall knowledge and observations about the user"""
        knowledge = self.recall(query, MemoryType.KNOWLEDGE, n_results)
        observations = self.recall(query, MemoryType.OBSERVATION, n_results)
        combined = knowledge + observations
        combined.sort(key=lambda x: -x['combined_score'])
        return combined[:n_results]

    def get_emotional_context(self, n_recent: int = 5) -> List[Dict]:
        """Get recent emotional events for context"""
        col = self._get_collection(MemoryType.EMOTION)
        if not col or col.count() == 0:
            return []
        try:
            results = col.query(
                query_texts=["recent emotional state"],
                n_results=min(n_recent, col.count()),
            )
            if results and results['documents'] and results['documents'][0]:
                return [
                    {
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    }
                    for i in range(len(results['documents'][0]))
                ]
        except Exception as e:
            self.logger.warning(f"Error getting emotional context: {e}")
        return []

    def get_relevant_context(self, user_input: str, max_memories: int = 3) -> str:
        """
        Get formatted context string for prompt injection.
        Compatible with original VectorMemory interface.
        """
        memories = self.recall(user_input, "all", max_memories)
        if not memories:
            return "No relevant past context found."

        parts = ["Relevant memories:"]
        for i, mem in enumerate(memories, 1):
            meta = mem['metadata']
            col = mem['collection']
            timestamp = meta.get('timestamp', 'unknown')[:10]
            score = mem['combined_score']
            parts.append(f"\n{i}. [{col}] (relevance: {score}, date: {timestamp})")
            parts.append(f"   {mem['text'][:200]}")
        return "\n".join(parts)

    # === Utility Methods ===

    def _time_decay_score(self, timestamp_str: str) -> float:
        """Score from 0-1 based on recency (1.0 = just now, 0.0 = very old)"""
        if not timestamp_str:
            return 0.5
        try:
            ts = datetime.fromisoformat(timestamp_str)
            age_hours = (datetime.now() - ts).total_seconds() / 3600
            # Exponential decay: half-life of 48 hours
            return math.exp(-0.693 * age_hours / 48)
        except (ValueError, TypeError):
            return 0.5

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        stats = {}
        total = 0
        for name, col in self._collections.items():
            count = col.count() if col else 0
            stats[name] = count
            total += count
        stats['total'] = total
        return stats

    def count(self) -> int:
        """Total memories across all collections"""
        return sum(c.count() for c in self._collections.values() if c)

    def clear_collection(self, memory_type: str):
        """Clear a specific collection"""
        if self.client and memory_type in self._collections:
            self.client.delete_collection(memory_type)
            self._collections[memory_type] = self.client.create_collection(memory_type)
            self.logger.info(f"Cleared collection: {memory_type}")

    def clear_all(self):
        """Clear all memory collections"""
        for name in self.COLLECTIONS:
            self.clear_collection(name)
        self.logger.warning("All vector memories cleared")
