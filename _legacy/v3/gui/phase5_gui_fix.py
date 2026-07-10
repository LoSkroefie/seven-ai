# Phase 5 GUI Fix - Patch for _update_phase5_data method
# Replace lines 789-860 in phase5_gui.py with this version

def _update_phase5_data(self):
    """Update Phase 5 displays with robust error handling"""
    if not self.bot:
        return
    
    # Check if Phase 5 exists
    if not hasattr(self.bot, 'phase5') or not self.bot.phase5:
        return
        
    try:
        p5 = self.bot.phase5
        
        # Get current state from Phase 5
        try:
            state = p5.get_current_state()
        except Exception as e:
            self._log_debug(f"Failed to get Phase 5 state: {e}")
            return
        
        # Working memory - with error handling
        try:
            if 'working_memory' in state and state['working_memory']:
                self.working_memory_text.delete('1.0', 'end')
                for i, concept in enumerate(state['working_memory'][:7], 1):
                    self.working_memory_text.insert('end', f"{i}. {concept}\n")
        except Exception as e:
            self._log_debug(f"Working memory update error: {e}")
        
        # Attention - with correct attribute path
        try:
            if 'attention_focus' in state:
                self.attention_label.config(text=state['attention_focus'])
            # Alternative: try to get from cognition directly if state doesn't have it
            elif hasattr(p5, 'cognition') and hasattr(p5.cognition, 'working_memory'):
                if hasattr(p5.cognition.working_memory, 'current_focus'):
                    focus = p5.cognition.working_memory.current_focus
                    if focus:
                        self.attention_label.config(text=focus)
        except Exception as e:
            self._log_debug(f"Attention update error: {e}")
        
        # Emotions
        try:
            if 'seven_emotion' in state and state['seven_emotion']:
                emotion = state['seven_emotion']
                text = f"{emotion.emotion.value.title()} ({emotion.intensity:.2f})"
                if hasattr(emotion, 'secondary_emotions') and emotion.secondary_emotions:
                    for e, i in list(emotion.secondary_emotions.items())[:2]:
                        text += f" + {e.value.title()} ({i:.2f})"
                self.current_emotion_label.config(text=text)
                
                # Update emotion bars
                self._update_emotion_bars(emotion)
        except Exception as e:
            self._log_debug(f"Emotion update error: {e}")
        
        # Autonomous goal
        try:
            if hasattr(p5, 'motivation') and hasattr(p5.motivation, 'current_goal'):
                goal = p5.motivation.current_goal
                if goal:
                    self.current_goal_label.config(
                        text=f"[TARGET] {goal.get('description', 'Unknown goal')} (Priority: {goal.get('priority', 0)})")
                    
                    progress = goal.get('progress', 0)
                    self.goal_progress_label.config(text=f"{int(progress*100)}%")
                    self._draw_progress_bar(self.goal_progress_canvas, progress)
        except Exception as e:
            self._log_debug(f"Goal update error: {e}")
        
        # Homeostasis
        try:
            if hasattr(p5, 'homeostasis'):
                h = p5.homeostasis
                if hasattr(h, 'energy'):
                    self._update_health_bar('Energy', h.energy / 100)
                if hasattr(h, 'focus'):
                    self._update_health_bar('Focus', h.focus / 100)
                
                # Mood calculation
                mood_val = 0.5  # Default
                if hasattr(h, 'mood_score'):
                    mood_val = (h.mood_score + 1) / 2  # Normalize -1 to 1 -> 0 to 1
                self._update_health_bar('Mood', mood_val)
        except Exception as e:
            self._log_debug(f"Homeostasis update error: {e}")
        
        # Promises
        try:
            if hasattr(p5, 'promises'):
                ps = p5.promises
                if hasattr(ps, 'trust_score'):
                    self.trust_score_label.config(text=f"Trust Score: {ps.trust_score}/100")
                if hasattr(ps, 'promises_kept'):
                    self.kept_label.config(text=f"[OK] Kept: {ps.promises_kept}")
                if hasattr(ps, 'promises_broken'):
                    self.broken_label.config(text=f"[ERROR] Broken: {ps.promises_broken}")
                
                if hasattr(ps, 'get_pending_promises'):
                    pending = ps.get_pending_promises()
                    self.pending_count_label.config(text=f"[PENDING] Pending: {len(pending)}")
                    
                    self.promises_text.delete('1.0', 'end')
                    for p in pending[:10]:
                        self.promises_text.insert('end',
                            f"[Priority {p.priority}] {p.content}\n")
                        if hasattr(p, 'due_by') and p.due_by:
                            self.promises_text.insert('end',
                                f"  Due: {p.due_by.strftime('%Y-%m-%d %H:%M')}\n")
                        self.promises_text.insert('end', "\n")
        except Exception as e:
            self._log_debug(f"Promise update error: {e}")
                    
    except Exception as e:
        self._log_debug(f"Phase 5 update error (main): {e}")
        import traceback
        self._log_debug(f"Traceback: {traceback.format_exc()}")
