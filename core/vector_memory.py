"""
Vector-based semantic memory using ChromaDB
Enables bot to recall relevant conversations from any time in history
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from datetime import datetime
import config

class VectorMemory:
    """Semantic memory using vector embeddings"""
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB for vector memory
        
        Args:
            persist_directory: Where to store the database
        """
        if persist_directory is None:
            persist_directory = str(config.DATA_DIR / "chroma_db")
        
        print("[INIT] Initializing Vector Memory...")
        
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="conversations",
                metadata={"description": "All conversation history with semantic search"}
            )
            
            print(f"[OK] Vector Memory loaded ({self.collection.count()} memories)")
            
        except Exception as e:
            print(f"[ERROR] Error initializing vector memory: {e}")
            self.client = None
            self.collection = None
    
    def _sanitize_text(self, text: str) -> str:
        """
        Remove problematic Unicode characters for Windows console encoding
        
        Args:
            text: Input text that may contain emojis or special Unicode
            
        Returns:
            ASCII-safe text
        """
        if not text:
            return ""
        
        try:
            # Try to keep as much as possible while removing emojis
            # This keeps accented characters but removes emojis
            return text.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
        except:
            # Fallback: ASCII only
            return text.encode('ascii', 'ignore').decode('ascii')
    
    def store(
        self,
        user_input: str,
        bot_response: str,
        emotion: str = "neutral",
        metadata: Optional[Dict] = None
    ):
        """
        Store a conversation turn with vector embedding
        
        Args:
            user_input: What user said
            bot_response: What bot replied
            emotion: Bot's emotional state
            metadata: Additional context
        """
        if not self.collection:
            return
        
        try:
            # Sanitize inputs for Windows encoding compatibility
            user_input_safe = self._sanitize_text(user_input)
            bot_response_safe = self._sanitize_text(bot_response)
            
            # Create searchable text combining both sides
            conversation_text = f"User: {user_input_safe}\nBot: {bot_response_safe}"
            
            # Prepare metadata (keep original text in metadata)
            meta = {
                "timestamp": datetime.now().isoformat(),
                "emotion": emotion,
                "user_input": user_input_safe,
                "bot_response": bot_response_safe
            }
            if metadata:
                meta.update(metadata)
            
            # Generate unique ID
            doc_id = f"conv_{datetime.now().timestamp()}"
            
            # Add to vector store
            self.collection.add(
                documents=[conversation_text],
                metadatas=[meta],
                ids=[doc_id]
            )
            
        except Exception as e:
            print(f"[WARNING] Error storing to vector memory: {e}")
    
    def semantic_search(
        self,
        query: str,
        n_results: int = 5,
        filter_emotion: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar conversations semantically
        
        Args:
            query: What to search for
            n_results: How many results to return
            filter_emotion: Optional emotion filter
            
        Returns:
            List of relevant conversations with context
        """
        if not self.collection:
            return []
        
        try:
            # Build where clause if filtering
            where = {}
            if filter_emotion:
                where["emotion"] = filter_emotion
            
            # Query with semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where if where else None
            )
            
            # Format results
            memories = []
            if results and results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    memory = {
                        "text": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None
                    }
                    memories.append(memory)
            
            return memories
            
        except Exception as e:
            print(f"[WARNING] Error searching vector memory: {e}")
            return []
    
    def get_relevant_context(self, user_input: str, max_memories: int = 3) -> str:
        """
        Get relevant past conversations for current input
        
        Args:
            user_input: Current user query
            max_memories: Max relevant memories to retrieve
            
        Returns:
            Formatted context string
        """
        memories = self.semantic_search(user_input, n_results=max_memories)
        
        if not memories:
            return "No relevant past conversations found."
        
        context_parts = ["Relevant past conversations:"]
        for i, memory in enumerate(memories, 1):
            meta = memory['metadata']
            timestamp = meta.get('timestamp', 'unknown')
            context_parts.append(f"\n{i}. ({timestamp}):")
            context_parts.append(f"   User: {meta.get('user_input', 'N/A')}")
            context_parts.append(f"   Bot: {meta.get('bot_response', 'N/A')}")
        
        return "\n".join(context_parts)
    
    def count(self) -> int:
        """Get total number of stored memories"""
        if not self.collection:
            return 0
        return self.collection.count()
    
    def clear_all(self):
        """Clear all memories (use with caution!)"""
        if self.collection:
            self.client.delete_collection("conversations")
            self.collection = self.client.create_collection("conversations")
            print("[OK] All vector memories cleared")
