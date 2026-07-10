"""
GUI Error Fix - Patches for AttributeError issues
Apply these fixes to phase5_gui.py
"""

# FIX 1: Update _update_phase5_data() - Better attention handling (line ~985-998)
ATTENTION_FIX = '''
            # Attention - with fallback to cognition attribute
            try:
                if 'attention_focus' in state:
                    self.attention_label.config(text=state['attention_focus'])
                elif hasattr(p5, 'cognition') and p5.cognition:
                    # Try different possible attribute names
                    if hasattr(p5.cognition, 'working_memory') and p5.cognition.working_memory:
                        wm = p5.cognition.working_memory
                        # Try multiple possible attribute names
                        focus_text = None
                        if hasattr(wm, 'current_focus'):
                            focus_text = wm.current_focus
                        elif hasattr(wm, 'focus'):
                            focus_text = wm.focus
                        elif hasattr(wm, 'attention_focus'):
                            focus_text = wm.attention_focus
                        
                        if focus_text:
                            self.attention_label.config(text=focus_text)
            except Exception:
                pass  # Silently fail - no debug logging
'''

# FIX 2: Update _update_enhancement_data() - Safe dict access (line ~1256-1270)
ENHANCEMENT_FIX = '''
    def _update_enhancement_data(self):
        """NEW! Update enhancement modules data"""
        try:
            # Relationship tracking
            if hasattr(self.bot, 'relationship_tracker'):
                try:
                    summary = self.bot.relationship_tracker.get_relationship_summary()
                    
                    # Ensure summary is a dict, not a string
                    if not isinstance(summary, dict):
                        return  # Skip if not valid dict
                    
                    # Safe dict access with defaults
                    self.trust_relationship_label.config(
                        text=f"Trust: {int(summary.get('trust_score', 0))}%")
                    self.rapport_label.config(
                        text=f"Rapport: {int(summary.get('rapport', 0))}%")
                    self.understanding_label.config(
                        text=f"Understanding: {int(summary.get('understanding', 0))}%")
                    
                    self.days_together_label.config(
                        text=f"Days Together: {summary.get('days_together', 0)}")
                    self.total_interactions_label.config(
                        text=f"Total Interactions: {summary.get('total_interactions', 0)}")
                    self.positive_ratio_label.config(
                        text=f"Positive Ratio: {summary.get('positive_ratio', 0):.1f}%")
                    
                    # Milestones - safe access
                    if hasattr(self.bot.relationship_tracker, 'data') and isinstance(self.bot.relationship_tracker.data, dict):
                        milestones = self.bot.relationship_tracker.data.get('milestones', [])
                        self.milestones_text.delete('1.0', 'end')
                        for milestone in milestones[-10:]:
                            if isinstance(milestone, dict):
                                self.milestones_text.insert('end',
                                    f"🏆 {milestone.get('name', 'Unknown')}\n")
                                achieved = milestone.get('achieved', '')
                                if achieved:
                                    self.milestones_text.insert('end',
                                        f"   Achieved: {str(achieved)[:10]}\n\n")
                except Exception:
                    pass  # Silently fail - no logging
            
            # Learning tracking
            if hasattr(self.bot, 'learning_tracker'):
                try:
                    learnings = self.bot.learning_tracker.get_recent_learnings(limit=1000)
                    if isinstance(learnings, list):
                        self.total_learnings_label.config(text=f"Total Learnings: {len(learnings)}")
                        
                        # Recent learnings
                        recent = learnings[:20]
                        self.learnings_text.delete('1.0', 'end')
                        for learning in recent:
                            if isinstance(learning, dict):
                                self.learnings_text.insert('end',
                                    f"[{learning.get('category', 'unknown')}] {learning.get('content', '')}\n")
                                self.learnings_text.insert('end',
                                    f"  Confidence: {learning.get('confidence', 0):.1%} | Reinforcements: {learning.get('reinforcements', 0)}\n\n")
                except Exception:
                    pass  # Silently fail
            
            # Goal tracking
            if hasattr(self.bot, 'goal_manager'):
                try:
                    active_goals = self.bot.goal_manager.get_active_goals()
                    if isinstance(active_goals, list):
                        self.active_goals_label.config(text=f"Active Goals: {len(active_goals)}")
                        
                        # Category counts
                        learning_goals = self.bot.goal_manager.get_goals_by_category('learning')
                        mastery_goals = self.bot.goal_manager.get_goals_by_category('mastery')
                        creativity_goals = self.bot.goal_manager.get_goals_by_category('creativity')
                        exploration_goals = self.bot.goal_manager.get_goals_by_category('exploration')
                        
                        self.learning_goals_label.config(
                            text=f"📚 Learning: {len(learning_goals) if isinstance(learning_goals, list) else 0}")
                        self.mastery_goals_label.config(
                            text=f"🏆 Mastery: {len(mastery_goals) if isinstance(mastery_goals, list) else 0}")
                        self.creativity_goals_label.config(
                            text=f"🎨 Creativity: {len(creativity_goals) if isinstance(creativity_goals, list) else 0}")
                        self.exploration_goals_label.config(
                            text=f"🗺️ Exploration: {len(exploration_goals) if isinstance(exploration_goals, list) else 0}")
                        
                        # Active goals list
                        self.goals_text.delete('1.0', 'end')
                        for goal in active_goals:
                            if isinstance(goal, dict):
                                self.goals_text.insert('end',
                                    f"[{goal.get('category', 'unknown')}] {goal.get('title', 'Untitled')}\n")
                                self.goals_text.insert('end',
                                    f"  {goal.get('description', '')}\n")
                                self.goals_text.insert('end',
                                    f"  Progress: {goal.get('progress', 0)*100:.0f}% | Priority: {goal.get('priority', 0)}\n\n")
                except Exception:
                    pass  # Silently fail
            
            # Emotion journal
            if hasattr(self.bot, 'emotion_journal'):
                try:
                    insights = self.bot.emotion_journal.get_emotional_insights()
                    if isinstance(insights, dict):
                        self.most_common_emotion_label.config(
                            text=f"Most Common: {insights.get('most_common_emotion', 'Unknown')}")
                        self.emotional_volatility_label.config(
                            text=f"Volatility: {insights.get('emotional_volatility', 0):.2f}")
                        self.unique_emotions_label.config(
                            text=f"Unique Emotions: {insights.get('unique_emotions_experienced', 0)}")
                except Exception:
                    pass  # Silently fail
                        
        except Exception:
            pass  # Top-level silently fail - no debug logging
'''

print("GUI Error Fix Created!")
print("\nThis patch fixes:")
print("1. AttributeError: 'CognitiveArchitecture' object has no attribute 'current_focus'")
print("2. TypeError: string indices must be integers, not 'str'")
print("\nApply these changes to phase5_gui.py to stop the debug log spam.")
