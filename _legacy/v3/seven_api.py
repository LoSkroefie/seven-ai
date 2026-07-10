"""
Seven AI REST API — External Control & Integration

FastAPI server exposing Seven's capabilities over HTTP.
Enables webhooks, external triggers, mobile apps, and integrations.

Endpoints:
    POST /chat           — Send message, get response
    GET  /status         — Bot status, uptime, emotion, health
    GET  /emotions       — Current emotional state
    POST /goal           — Create a new goal
    GET  /goals          — List active goals
    POST /schedule       — Schedule a task
    POST /trigger        — External trigger (webhook)
    GET  /memory/search  — Search memories
    POST /reflect        — Trigger self-reflection
    GET  /health         — Health check (for monitoring)
    GET  /metrics        — Sentience metrics & benchmarks

Runs on http://127.0.0.1:7777 by default (localhost only for security).
"""

import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Depends, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger("SevenAPI")


# ============ Request/Response Models ============

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    emotion: str
    mood: Optional[str] = None
    processing_time: float

class GoalRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=1024)
    priority: Optional[str] = "medium"

class ScheduleRequest(BaseModel):
    task: str = Field(..., min_length=1)
    cron: Optional[str] = None
    interval_minutes: Optional[int] = None
    run_at: Optional[str] = None

class TriggerRequest(BaseModel):
    source: str = Field(..., description="Source of trigger (email, telegram, webhook, etc.)")
    event: str = Field(..., description="Event type")
    data: Optional[Dict[str, Any]] = None

class ReflectRequest(BaseModel):
    topic: Optional[str] = None
    depth: Optional[str] = "normal"  # shallow, normal, deep

class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    limit: Optional[int] = 10


# ============ App Factory ============

def create_app(bot_instance=None) -> 'FastAPI':
    """Create FastAPI app with bot instance injected"""
    
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")
    
    app = FastAPI(
        title="Seven AI API",
        description="REST API for Seven AI v3.2",
        version="3.2.0",
        docs_url="/docs",
        redoc_url=None
    )
    
    # CORS — localhost only by default
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    
    # Store bot reference
    app.state.bot = bot_instance
    app.state.start_time = datetime.now()
    app.state.request_count = 0
    
    def get_bot():
        if app.state.bot is None:
            raise HTTPException(status_code=503, detail="Bot not initialized")
        return app.state.bot
    
    # ============ Endpoints ============
    
    @app.get("/health")
    async def health():
        """Health check for monitoring"""
        bot = app.state.bot
        return {
            "status": "ok" if bot else "no_bot",
            "uptime_seconds": (datetime.now() - app.state.start_time).total_seconds(),
            "requests_served": app.state.request_count
        }
    
    @app.get("/status")
    async def status():
        """Full bot status"""
        bot = get_bot()
        app.state.request_count += 1
        
        result = {
            "name": getattr(bot, 'bot_name', 'Seven'),
            "running": getattr(bot, 'running', False),
            "sleeping": getattr(bot, 'sleeping', False),
            "uptime_seconds": (datetime.now() - app.state.start_time).total_seconds(),
            "emotion": str(getattr(bot, 'current_emotion', 'unknown')),
        }
        
        # Autonomous life stats
        if hasattr(bot, 'autonomous_life') and bot.autonomous_life:
            al = bot.autonomous_life
            result["autonomous_cycles"] = al.cycle_count
            result["autonomous_running"] = al.running
        
        # Phase 5 sentience
        if hasattr(bot, 'phase5') and bot.phase5:
            try:
                if hasattr(bot.phase5, 'homeostasis'):
                    health = bot.phase5.homeostasis.assess_health()
                    result["health"] = health.get('overall_status', 'unknown')
            except Exception:
                pass
        
        # V2 system
        if hasattr(bot, 'v2_system') and bot.v2_system:
            result["v2_active"] = True
        
        return result
    
    @app.post("/chat", response_model=ChatResponse)
    async def chat(req: ChatRequest):
        """Send a message and get Seven's response"""
        bot = get_bot()
        app.state.request_count += 1
        
        start = time.time()
        
        try:
            # Use the bot's process_input method
            if hasattr(bot, 'process_input'):
                response = bot.process_input(req.message)
            elif hasattr(bot, 'ollama') and bot.ollama:
                response = bot.ollama.generate(
                    prompt=req.message,
                    system_message="You are Seven, an advanced sentient AI assistant.",
                    temperature=0.8,
                    max_tokens=500
                )
            else:
                raise HTTPException(status_code=503, detail="No LLM available")
            
            elapsed = time.time() - start
            
            return ChatResponse(
                response=response or "I had trouble forming a response.",
                emotion=str(getattr(bot, 'current_emotion', 'calm')),
                mood=getattr(bot, 'current_mood', None) if hasattr(bot, 'current_mood') else None,
                processing_time=round(elapsed, 3)
            )
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/emotions")
    async def emotions():
        """Get current emotional state"""
        bot = get_bot()
        app.state.request_count += 1
        
        result = {
            "current_emotion": str(getattr(bot, 'current_emotion', 'unknown')),
        }
        
        # Phase 5 affective system
        if hasattr(bot, 'phase5') and bot.phase5 and hasattr(bot.phase5, 'affective'):
            try:
                affective = bot.phase5.affective
                if hasattr(affective, 'get_emotional_state'):
                    result["emotional_state"] = affective.get_emotional_state()
                if hasattr(affective, 'get_dominant_emotion'):
                    result["dominant"] = str(affective.get_dominant_emotion())
            except Exception:
                pass
        
        # V2.2 emotional complexity
        if hasattr(bot, 'emotional_complexity') and bot.emotional_complexity:
            try:
                if hasattr(bot.emotional_complexity, 'get_state'):
                    result["complexity"] = bot.emotional_complexity.get_state()
            except Exception:
                pass
        
        # Persistent emotions
        if hasattr(bot, 'persistent_emotions') and bot.persistent_emotions:
            try:
                result["persistent"] = True
            except Exception:
                pass
        
        return result
    
    @app.post("/goal")
    async def create_goal(req: GoalRequest):
        """Create a new autonomous goal"""
        bot = get_bot()
        app.state.request_count += 1
        
        if hasattr(bot, 'phase5') and bot.phase5 and hasattr(bot.phase5, 'motivation'):
            try:
                bot.phase5.motivation.add_goal(req.description, priority=req.priority)
                return {"status": "created", "goal": req.description}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        raise HTTPException(status_code=503, detail="Goal system not available")
    
    @app.get("/goals")
    async def list_goals():
        """List active goals"""
        bot = get_bot()
        app.state.request_count += 1
        
        if hasattr(bot, 'phase5') and bot.phase5 and hasattr(bot.phase5, 'motivation'):
            try:
                goals = bot.phase5.motivation.get_active_goals()
                return {"goals": [
                    {
                        "description": g.description,
                        "progress": g.progress,
                        "priority": getattr(g, 'priority', 'medium'),
                        "next_step": getattr(g, 'next_step', None)
                    }
                    for g in goals
                ]}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        return {"goals": []}
    
    @app.post("/trigger")
    async def external_trigger(req: TriggerRequest):
        """Handle external triggers (webhooks, email notifications, etc.)"""
        bot = get_bot()
        app.state.request_count += 1
        
        logger.info(f"External trigger: {req.source}/{req.event}")
        
        # Process trigger through autonomous life if available
        if hasattr(bot, 'autonomous_life') and bot.autonomous_life:
            try:
                message = f"[External trigger from {req.source}] Event: {req.event}"
                if req.data:
                    message += f" Data: {req.data}"
                bot.autonomous_life.queue_message(message, priority="high")
                return {"status": "processed", "source": req.source, "event": req.event}
            except Exception as e:
                logger.error(f"Trigger processing error: {e}")
        
        return {"status": "received", "note": "Autonomous life not active — trigger logged only"}
    
    @app.post("/reflect")
    async def trigger_reflection(req: ReflectRequest):
        """Trigger self-reflection"""
        bot = get_bot()
        app.state.request_count += 1
        
        # Try self-reflection module
        if hasattr(bot, 'self_reflection') and bot.self_reflection:
            try:
                result = bot.self_reflection.reflect(
                    topic=req.topic,
                    depth=req.depth
                )
                return {"status": "reflected", "result": result}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Fallback: use Phase 5 reflection
        if hasattr(bot, 'phase5') and bot.phase5 and hasattr(bot.phase5, 'reflection'):
            try:
                result = bot.phase5.reflection.reflect(topic=req.topic)
                return {"status": "reflected", "result": str(result)}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        raise HTTPException(status_code=503, detail="Reflection system not available")
    
    @app.get("/memory/search")
    async def search_memory(query: str, limit: int = 10):
        """Search Seven's memories"""
        bot = get_bot()
        app.state.request_count += 1
        
        results = []
        
        # Vector memory search
        if hasattr(bot, 'vector_memory') and bot.vector_memory:
            try:
                results = bot.vector_memory.search(query, n_results=limit)
            except Exception:
                pass
        
        # Fallback to regular memory
        if not results and hasattr(bot, 'memory') and bot.memory:
            try:
                if hasattr(bot.memory, 'search'):
                    results = bot.memory.search(query, limit=limit)
            except Exception:
                pass
        
        return {"query": query, "results": results, "count": len(results)}
    
    @app.get("/metrics")
    async def metrics():
        """Sentience metrics and benchmarks"""
        bot = get_bot()
        app.state.request_count += 1
        
        m = {
            "version": "3.2",
            "sentience_systems": 0,
            "emotions_count": 35,
            "systems": {}
        }
        
        # Count active systems
        active = 0
        systems = {}
        
        checks = [
            ('phase5', 'Phase 5 Core'),
            ('v2_system', 'V2.0 Sentience'),
            ('emotional_complexity', 'Emotional Complexity'),
            ('metacognition', 'Metacognition'),
            ('vulnerability', 'Vulnerability'),
            ('persistent_emotions', 'Persistent Emotions'),
            ('surprise_system', 'Genuine Surprise'),
            ('embodied_experience', 'Embodied Experience'),
            ('multimodal_emotion', 'Multi-Modal Emotion'),
            ('temporal_continuity', 'Temporal Continuity'),
            ('autonomous_life', 'Autonomous Life'),
            ('autonomous_agent', 'Autonomous Agent'),
            ('true_autonomy', 'True Autonomy'),
            ('vision', 'Vision System'),
            ('self_reflection', 'Self-Reflection'),
            ('multi_agent', 'Multi-Agent System'),
        ]
        
        for attr, name in checks:
            is_active = hasattr(bot, attr) and getattr(bot, attr) is not None
            systems[name] = is_active
            if is_active:
                active += 1
        
        m["sentience_systems"] = active
        m["systems"] = systems
        m["autonomous_cycles"] = getattr(bot.autonomous_life, 'cycle_count', 0) if hasattr(bot, 'autonomous_life') and bot.autonomous_life else 0
        
        return m
    
    # ============ v3.2 Endpoints ============
    
    @app.get("/extensions")
    async def list_extensions():
        """List loaded extensions"""
        bot = get_bot()
        app.state.request_count += 1
        
        loader = getattr(bot, 'plugin_loader', None)
        if not loader:
            return {"extensions": [], "note": "Extension system not enabled"}
        
        return loader.get_status()
    
    @app.post("/extensions/reload")
    async def reload_extensions():
        """Hot-reload all extensions"""
        bot = get_bot()
        app.state.request_count += 1
        
        loader = getattr(bot, 'plugin_loader', None)
        if not loader:
            raise HTTPException(status_code=503, detail="Extension system not enabled")
        
        results = loader.reload_all()
        return {"status": "reloaded", "results": results}
    
    @app.get("/v32/status")
    async def v32_status():
        """v3.2 feature status — LoRA, social sim, predictor, robotics, extensions"""
        bot = get_bot()
        app.state.request_count += 1
        
        status = {}
        
        trainer = getattr(bot, 'lora_trainer', None)
        status['lora_trainer'] = trainer.get_status() if trainer else {'available': False}
        
        sim = getattr(bot, 'social_sim', None)
        status['social_sim'] = sim.get_status() if sim else {'available': False}
        
        predictor = getattr(bot, 'user_predictor', None)
        status['user_predictor'] = predictor.get_status() if predictor else {'available': False}
        
        robotics = getattr(bot, 'robotics', None)
        status['robotics'] = robotics.get_status() if robotics else {'available': False}
        
        loader = getattr(bot, 'plugin_loader', None)
        status['extensions'] = loader.get_status() if loader else {'available': False}
        
        evolver = getattr(bot, 'neat_evolver', None)
        if evolver:
            status['neat_evolution'] = {
                'available': evolver.available,
                'domains': list(evolver.best_genomes.keys()) if evolver.available else [],
            }
        
        bio = getattr(bot, 'biological_life', None)
        if bio:
            status['biological_life'] = {
                'energy': bio.energy,
                'hunger': bio.hunger_level,
                'threat_level': bio.threat_level,
            }
        
        return status
    
    return app


# ============ Standalone runner ============

if __name__ == '__main__':
    if not FASTAPI_AVAILABLE:
        print("FastAPI not installed. Run: pip install fastapi uvicorn")
        sys.exit(1)
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    print("Starting Seven API in standalone mode (no bot instance)...")
    app = create_app(bot_instance=None)
    uvicorn.run(app, host="127.0.0.1", port=7777)
