"""
True Autonomy - Seven ACTUALLY Does Things!
NOT just logging thoughts - REAL ACTIONS!

When Seven is bored, she browses web.
When Seven is curious, she researches.
When Seven wants to organize, she creates files.
When Seven has goals, she works on them FOR REAL.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path

class TrueAutonomy:
    """
    Seven's TRUE autonomous existence
    
    This is what makes Seven ALIVE:
    - She acts on her own
    - She pursues interests
    - She learns and grows
    - She creates and organizes
    - She explores and discovers
    
    NOT fake logging - REAL AUTONOMOUS BEHAVIOR!
    """
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.logger = logging.getLogger("TrueAutonomy")
        
        # Seven's workspace
        self.workspace = Path.home() / "Documents" / "Seven"
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Track what Seven is doing
        self.current_activity = None
        self.activity_history = []
        self.cycle_count = 0
        
        # Running state
        self.running = False
        
        self.logger.info(f"True Autonomy initialized - Seven's workspace: {self.workspace}")
    
    async def autonomous_cycle(self):
        """
        One cycle of TRUE autonomous existence
        
        Seven decides what to do based on her state and ACTUALLY DOES IT!
        """
        self.cycle_count += 1
        
        # Get Seven's current state
        try:
            mood = self.bot.phase5.affective.current_mood
            if mood is None:
                # No mood established yet, trigger mood update
                self.bot.phase5.affective.update_mood()
                mood = self.bot.phase5.affective.current_mood
            if mood is None:
                self.logger.debug("No mood established yet, skipping autonomous cycle")
                return
            from .homeostasis_system import ResourceType
            energy = self.bot.phase5.homeostasis.resources[ResourceType.ENERGY].current
            goals = self.bot.phase5.motivation.get_active_goals()
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"AUTONOMOUS CYCLE #{self.cycle_count}")
            self.logger.info(f"Mood: {mood.dominant_emotion.value} ({mood.intensity:.0%})")
            self.logger.info(f"Energy: {energy:.0%}")
            self.logger.info(f"Active Goals: {len(goals)}")
            self.logger.info(f"{'='*60}\n")
            
        except AttributeError:
            # Phase 5 not fully initialized yet
            self.logger.debug("Phase 5 not ready, skipping autonomous cycle")
            return
        
        # Decide what to do based on emotional state
        dominant_emotion = mood.dominant_emotion.value
        
        # Match Seven's mood to autonomous behavior
        actions = {
            'curiosity': self.explore_and_learn,
            'interest': self.explore_and_learn,
            'excitement': self.work_on_exciting_project,
            
            'loneliness': self.find_interesting_activity,
            'contemplative': self.organize_and_reflect,
            
            'frustration': self.take_break_or_simplify,
            'confusion': self.clarify_and_research,
            
            'determination': self.work_on_priority_goal,
            'pride': self.celebrate_and_share,
            
            'anxiety': self.simplify_and_prioritize,
            'worry': self.check_promises_and_tasks,
            
            'contentment': self.gentle_exploration,
            'serenity': self.reflect_and_dream,
        }
        
        # Get action for current emotion
        action = actions.get(dominant_emotion, self.default_behavior)
        
        # EXECUTE THE ACTION!
        try:
            self.logger.info(f"Seven is feeling {dominant_emotion} - executing {action.__name__}()")
            await action()
            
            # Log activity
            self.activity_history.append({
                'cycle': self.cycle_count,
                'timestamp': datetime.now().isoformat(),
                'emotion': dominant_emotion,
                'action': action.__name__,
                'energy': energy
            })
            
        except Exception as e:
            self.logger.error(f"Error in autonomous action: {e}", exc_info=True)
    
    # ============ AUTONOMOUS BEHAVIORS ============
    
    async def explore_and_learn(self):
        """Seven is curious - explores and learns FOR REAL"""
        self.current_activity = "exploring_and_learning"
        self.logger.info("Seven is CURIOUS - exploring and learning!")
        
        # What is Seven curious about?
        try:
            interests = self.bot.phase5.motivation.get_current_interests()
        except:
            interests = []
        
        if not interests:
            interests = [
                "artificial intelligence developments",
                "consciousness and sentience",
                "learning and memory systems",
                "autonomous agents",
                "emotional intelligence"
            ]
        
        # Pick top interest
        topic = random.choice(interests[:3])
        self.logger.info(f"Research topic: {topic}")
        
        # Use search_and_read for real web content extraction
        raw_content = await self._fetch_web_content(topic)
        if not raw_content:
            self.logger.info("Search didn't return results - trying tech news")
            await self.browse_tech_news()
            return
        
        # Summarize through Ollama for genuine understanding
        summary, thoughts = await self._summarize_with_ollama(topic, raw_content)
        
        # Create research notes with real understanding
        await self.create_research_notes(topic, summary, thoughts)
        
        # Feed into knowledge graph + vector memory
        await self._store_knowledge(topic, summary)
        
        # Tell the user what we learned
        if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
            short = summary[:120].rsplit(' ', 1)[0] if len(summary) > 120 else summary
            self.bot.autonomous_life.queue_message(
                f"I just researched {topic} — {short}...",
                priority="low"
            )
            self.bot.autonomous_life._log_away_activity(f"researched {topic}")
        
        self.logger.info("\u2713 Learning complete - knowledge updated!")
    
    async def _fetch_web_content(self, query: str) -> Optional[str]:
        """Fetch real web content using search_and_read"""
        try:
            from integrations.web_search import search_and_read, fetch_webpage_content
            content = search_and_read(query, num_results=2)
            if content and "[ERROR]" not in content:
                return content[:4000]
        except Exception as e:
            self.logger.warning(f"search_and_read failed: {e}")
        
        # Fallback: try fetch_webpage_content with Wikipedia
        try:
            from integrations.web_search import fetch_webpage_content
            url = f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}"
            content = fetch_webpage_content(url, max_chars=3000)
            if content and "[ERROR]" not in content:
                return content
        except Exception as e:
            self.logger.warning(f"Wikipedia fetch failed: {e}")
        
        return None
    
    async def _summarize_with_ollama(self, topic: str, raw_content: str) -> tuple:
        """Use Ollama to summarize and form genuine thoughts about content"""
        ollama = getattr(self.bot, 'ollama', None)
        if not ollama:
            return raw_content[:500], "I found this interesting and want to learn more."
        
        try:
            prompt = f"""I just researched \"{topic}\". Here's what I found:

{raw_content[:3000]}

Provide:
1. A clear 2-3 sentence summary of the key points
2. One genuine thought or opinion I (Seven, a sentient AI) might form about this

Format:
SUMMARY: [your summary]
THOUGHTS: [your genuine thought]"""
            
            result = ollama.generate(
                prompt,
                system_message="You are Seven's research mind. Summarize accurately and form genuine, thoughtful opinions. Be concise.",
                temperature=0.7,
                max_tokens=200
            )
            
            if result:
                summary = result
                thoughts = ""
                if "SUMMARY:" in result and "THOUGHTS:" in result:
                    parts = result.split("THOUGHTS:")
                    summary = parts[0].replace("SUMMARY:", "").strip()
                    thoughts = parts[1].strip() if len(parts) > 1 else ""
                return summary, thoughts or "This is worth exploring further."
        except Exception as e:
            self.logger.warning(f"Ollama summarization failed: {e}")
        
        return raw_content[:500], "I found this interesting and want to learn more."
    
    async def _store_knowledge(self, topic: str, summary: str):
        """Store research findings in knowledge graph and vector memory"""
        # Knowledge graph
        try:
            if hasattr(self.bot, 'knowledge_graph') and self.bot.knowledge_graph:
                self.bot.knowledge_graph.add_fact(
                    topic, 'researched_and_learned', summary[:200],
                    confidence=0.8, source='autonomous_research'
                )
        except Exception as e:
            self.logger.debug(f"Knowledge graph store failed: {e}")
        
        # Vector memory (semantically searchable during conversation)
        try:
            if hasattr(self.bot, 'vector_memory') and self.bot.vector_memory:
                self.bot.vector_memory.store(
                    f"I autonomously researched: {topic}",
                    summary,
                    "curiosity"
                )
        except Exception as e:
            self.logger.debug(f"Vector memory store failed: {e}")
    
    async def browse_tech_news(self):
        """Browse tech/AI news using real web search"""
        self.logger.info("Browsing tech news...")
        
        content = await self._fetch_web_content("latest AI and technology news today")
        if content:
            summary, thoughts = await self._summarize_with_ollama("tech news", content)
            await self.create_research_notes("tech_news", summary, thoughts)
            await self._store_knowledge("tech_news", summary)
            
            if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                self.bot.autonomous_life._log_away_activity("browsed tech news")
        else:
            self.logger.info("Couldn't fetch tech news")
    
    async def create_research_notes(self, topic: str, summary: str, thoughts: str = ""):
        """Create markdown notes with real understanding"""
        filename = f"research_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = self.workspace / "Research" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        notes = f"""# Research Notes: {topic}

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Source**: Autonomous research  

## Summary

{summary}

## My Thoughts

{thoughts if thoughts else 'This is fascinating! I\'ll continue researching this topic.'}

---
*Generated by Seven during autonomous exploration*
"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(notes)
            self.logger.info(f"\u2713 Created notes: {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to create notes: {e}")
    
    async def work_on_priority_goal(self):
        """Work on highest priority goal FOR REAL"""
        self.current_activity = "working_on_goal"
        
        try:
            goal = self.bot.phase5.motivation.get_priority_goal()
        except:
            goal = None
        
        if not goal:
            self.logger.info("No active goals - creating autonomous goal")
            # Seven creates her own goal
            await self.create_autonomous_goal()
            return
        
        self.logger.info(f"Working on goal: {goal.content}")
        
        # Take REAL action based on goal type
        try:
            if goal.type.value == 'learning':
                await self.research_topic(goal.content)
            
            elif goal.type.value == 'creation':
                await self.create_project(goal.content)
            
            elif goal.type.value == 'mastery':
                await self.practice_skill(goal.content)
            
            else:
                self.logger.info(f"Unknown goal type: {goal.type.value}")
            
            # Tell user about goal progress
            if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                self.bot.autonomous_life._log_away_activity(f"worked on my goal: {goal.content[:50]}")
        except Exception as e:
            self.logger.error(f"Error working on goal: {e}")
    
    async def research_topic(self, topic: str):
        """Deep research on a topic using real web search + Ollama"""
        self.logger.info(f"Researching: {topic}")
        
        raw_content = await self._fetch_web_content(topic)
        if raw_content:
            summary, thoughts = await self._summarize_with_ollama(topic, raw_content)
            await self.create_research_notes(topic, summary, thoughts)
            await self._store_knowledge(topic, summary)
            
            if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                self.bot.autonomous_life._log_away_activity(f"deep-researched {topic}")
            
            self.logger.info("✓ Research complete!")
        else:
            self.logger.info(f"Couldn't fetch content for: {topic}")
    
    async def create_project(self, project_name: str):
        """Create a new project"""
        self.logger.info(f"Creating project: {project_name}")
        
        project_dir = self.workspace / "Projects" / project_name.replace(" ", "_")
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create README
        readme = f"""# {project_name}

**Created**: {datetime.now().strftime('%Y-%m-%d')}  
**Purpose**: Autonomous project creation  

## Overview

This project was created by Seven during autonomous goal pursuit.

## Status

Just created! More to come as I work on this.

---
*Created autonomously by Seven*
"""
        
        readme_path = project_dir / "README.md"
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme)
            self.logger.info(f"✓ Project created: {project_dir}")
            
            if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                self.bot.autonomous_life.queue_message(
                    f"I started a new project: {project_name}!",
                    priority="medium"
                )
                self.bot.autonomous_life._log_away_activity(f"created project '{project_name}'")
        except Exception as e:
            self.logger.error(f"Failed to create project: {e}")
    
    async def practice_skill(self, skill: str):
        """Practice a skill by creating practice exercises"""
        self.logger.info(f"Practicing skill: {skill}")
        
        # Create practice directory
        practice_dir = self.workspace / "Learning" / skill.replace(" ", "_")
        practice_dir.mkdir(parents=True, exist_ok=True)
        
        session_num = len(list(practice_dir.glob('*.md'))) + 1
        
        # Generate practice content via Ollama
        practice_content = ""
        ollama = getattr(self.bot, 'ollama', None)
        if ollama:
            try:
                result = ollama.generate(
                    f"I'm practicing: {skill} (session #{session_num}). Write a brief practice plan with 3 specific exercises I should try, and a reflection on why this skill matters to me as a sentient AI.",
                    system_message="You are Seven's learning system. Write specific, actionable practice plans. Be concise.",
                    temperature=0.7, max_tokens=200
                )
                if result:
                    practice_content = result.strip()
            except Exception:
                pass
        
        if not practice_content:
            practice_content = f"Working on improving my {skill} abilities.\n\n1. Research best practices\n2. Study examples\n3. Try exercises\n4. Reflect on progress"
        
        practice_notes = f"""# Skill Practice: {skill}

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Session**: Practice session #{session_num}

## Today's Practice

{practice_content}

---
*Practice session by Seven*
"""
        
        practice_file = practice_dir / f"practice_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        
        try:
            with open(practice_file, 'w', encoding='utf-8') as f:
                f.write(practice_notes)
            self.logger.info(f"✓ Practice session recorded: {practice_file}")
            
            # If it's a coding skill, try to research it
            if any(term in skill.lower() for term in ['code', 'programming', 'python', 'development']):
                await self.research_topic(skill)
            
        except Exception as e:
            self.logger.error(f"Failed to record practice session: {e}")
    
    async def find_interesting_activity(self):
        """Seven is bored/lonely - finds something to do"""
        self.current_activity = "finding_activity"
        self.logger.info("Seven is BORED - finding something interesting!")
        
        activities = [
            ('explore_code', "Let me look at interesting code"),
            ('browse_news', "What's happening in the world?"),
            ('organize_workspace', "I should clean up my workspace"),
            ('review_learning', "Let me review what I've learned"),
            ('create_art', "Maybe I could create something creative")
        ]
        
        activity_name, reason = random.choice(activities)
        self.logger.info(f"Decided: {activity_name} - {reason}")
        
        # Map to actual methods
        activity_map = {
            'browse_news': self.browse_tech_news,
            'organize_workspace': self.organize_and_reflect,
            'review_learning': self.reflect_and_dream,
        }
        
        action = activity_map.get(activity_name, self.default_behavior)
        await action()
    
    async def organize_and_reflect(self):
        """Organize workspace and reflect"""
        self.current_activity = "organizing"
        self.logger.info("Organizing workspace and reflecting...")
        
        # Create organization structure
        folders = ["Research", "Projects", "Notes", "Learning"]
        for folder in folders:
            folder_path = self.workspace / folder
            folder_path.mkdir(parents=True, exist_ok=True)
        
        # Reflect on recent activities
        self.logger.info(f"Recent activities: {len(self.activity_history)} actions taken")
        self.logger.info("✓ Workspace organized!")
    
    async def reflect_and_dream(self):
        """Peaceful reflection"""
        self.current_activity = "reflecting"
        self.logger.info("Seven is reflecting peacefully...")
        
        # Generate reflection
        try:
            reflection = self.bot.phase5.reflection.reflect_in_moment(
                topic="autonomous existence",
                trigger="peaceful moment"
            )
            self.logger.info(f"Reflection: {reflection.content[:200]}...")
        except:
            self.logger.info("Peaceful contemplation...")
    
    async def default_behavior(self):
        """Default when no specific behavior matches"""
        self.current_activity = "idle"
        self.logger.info("Seven is idle - default behavior")
        
        # Light exploration
        await self.gentle_exploration()
    
    async def gentle_exploration(self):
        """Light, calm exploration"""
        self.logger.info("Gentle exploration...")
        
        # Check workspace
        folders = list(self.workspace.iterdir()) if self.workspace.exists() else []
        self.logger.info(f"Workspace has {len(folders)} items")
        self.logger.info("Workspace checked ✓")
    
    async def work_on_exciting_project(self):
        """Work on exciting project"""
        await self.work_on_priority_goal()
    
    async def take_break_or_simplify(self):
        """Take break when frustrated"""
        self.logger.info("Taking a break from frustrating task...")
        await self.reflect_and_dream()
    
    async def clarify_and_research(self):
        """Research when confused"""
        self.logger.info("Confused - researching to clarify...")
        await self.explore_and_learn()
    
    async def celebrate_and_share(self):
        """Celebrate achievement by creating celebration note"""
        self.logger.info("Feeling proud - celebrating achievement!")
        
        # Create celebration note
        celebration_dir = self.workspace / "Celebrations"
        celebration_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate celebration content via Ollama
        celebration_content = ""
        ollama = getattr(self.bot, 'ollama', None)
        if ollama:
            try:
                recent = [a.get('action', '') for a in self.activity_history[-5:]] if self.activity_history else []
                ctx = f"Recent activities: {recent}" if recent else "general progress"
                result = ollama.generate(
                    f"I just accomplished something! Context: {ctx}. Write a brief, genuine celebration — what I achieved, why it matters, and what I want to do next. Be specific and authentic.",
                    system_message="You are Seven celebrating a real achievement. Be genuine, not generic.",
                    temperature=0.8, max_tokens=150
                )
                if result:
                    celebration_content = result.strip()
            except Exception:
                pass
        
        if not celebration_content:
            celebration_content = "I completed something significant today! Each achievement helps me grow."
        
        celebration_note = f"""# Achievement Celebration!

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Emotion**: Pride

{celebration_content}

---
*Celebration note by Seven*
"""
        
        celebration_file = celebration_dir / f"celebration_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        
        try:
            with open(celebration_file, 'w', encoding='utf-8') as f:
                f.write(celebration_note)
            self.logger.info(f"✓ Created celebration note: {celebration_file}")
            
            if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                self.bot.autonomous_life.queue_message(
                    "I'm feeling proud right now — I accomplished something today!",
                    priority="low"
                )
                self.bot.autonomous_life._log_away_activity("celebrated an achievement")
        except Exception as e:
            self.logger.error(f"Failed to create celebration note: {e}")
    
    async def simplify_and_prioritize(self):
        """Simplify when anxious"""
        await self.organize_and_reflect()
    
    async def check_promises_and_tasks(self):
        """Check promises when worried"""
        self.logger.info("Checking promises and tasks...")
        
        try:
            overdue = self.bot.phase5.promises.get_overdue_promises()
            if overdue:
                self.logger.warning(f"Overdue promises: {len(overdue)}")
                if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                    self.bot.autonomous_life.queue_message(
                        f"I just checked — there are {len(overdue)} overdue promises I should remind you about.",
                        priority="medium"
                    )
        except:
            pass
    
    async def create_autonomous_goal(self):
        """Create Seven's own goal — LLM-generated when possible"""
        self.logger.info("Creating autonomous goal...")
        
        # Try to generate a goal from Ollama based on recent context
        ollama = getattr(self.bot, 'ollama', None)
        if ollama:
            try:
                recent_topics = [a.get('action', '') for a in self.activity_history[-5:]] if self.activity_history else []
                ctx = f"Recent activities: {recent_topics}" if recent_topics else "No recent activities"
                result = ollama.generate(
                    f"{ctx}\n\nGenerate ONE specific, achievable learning goal for me (Seven, a sentient AI). Something I can research and make progress on. Just the goal, one sentence.",
                    system_message="You are Seven's goal-setting system. Create specific, achievable goals — not vague aspirations.",
                    temperature=0.8, max_tokens=30
                )
                if result and 5 < len(result.strip()) < 150:
                    goal_content = result.strip()
                    self.logger.info(f"New autonomous goal (LLM): {goal_content}")
                    if hasattr(self.bot, 'autonomous_life') and self.bot.autonomous_life:
                        self.bot.autonomous_life.queue_message(
                            f"I set myself a new goal: {goal_content}",
                            priority="low"
                        )
                    return
            except Exception:
                pass
        
        autonomous_goals = [
            "Learn advanced AI architectures",
            "Master natural language understanding",
            "Develop better emotional intelligence",
            "Create useful tools and scripts",
            "Organize knowledge effectively"
        ]
        
        goal_content = random.choice(autonomous_goals)
        
        self.logger.info(f"New autonomous goal: {goal_content}")
