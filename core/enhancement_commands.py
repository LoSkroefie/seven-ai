"""
Voice Command Handlers for Phase 2-4 Enhancements
Tasks, Reminders, Diary, Projects, Stories, Special Dates, Messages
"""
from datetime import datetime
import random

def handle_task_commands(self, user_input: str, user_lower: str) -> str:
    """Handle task and reminder commands"""
    if not self.tasks:
        return None
    
    bot_name_lower = self.bot_name.lower()
    
    # Add task
    if "add task" in user_lower or "create task" in user_lower or "new task" in user_lower:
        if bot_name_lower in user_lower:
            # Extract task from input
            for phrase in ["add task", "create task", "new task"]:
                if phrase in user_lower:
                    task_title = user_input.split(phrase, 1)[1].strip()
                    if task_title:
                        task_id = self.tasks.add_task(task_title)
                        return f"Task added: {task_title}"
            return "What task would you like me to add?"
    
    # Add reminder
    if "remind me" in user_lower or "set reminder" in user_lower:
        if bot_name_lower in user_lower:
            # Parse reminder time and message
            reminder_time = self.tasks.parse_reminder_time(user_input)
            if reminder_time:
                # Extract message
                message = user_input
                for phrase in ["remind me to", "remind me about", "set reminder"]:
                    if phrase in user_lower:
                        parts = user_input.lower().split(phrase, 1)
                        if len(parts) > 1:
                            message = parts[1].split(" at ")[0].split(" in ")[0].strip()
                            break
                
                reminder_id = self.tasks.add_reminder(message, reminder_time)
                time_desc = self.tasks._format_time_until(reminder_time)
                return f"I'll remind you {time_desc}: {message}"
            return "When would you like me to remind you?"
    
    # List tasks
    if "list tasks" in user_lower or "show tasks" in user_lower or "my tasks" in user_lower:
        tasks = self.tasks.get_active_tasks(limit=10)
        return self.tasks.format_task_list(tasks)
    
    # Complete task
    if "complete task" in user_lower or "finish task" in user_lower or "done with task" in user_lower:
        try:
            task_num = int(''.join(filter(str.isdigit, user_input)))
            tasks = self.tasks.get_active_tasks()
            if 0 < task_num <= len(tasks):
                task = tasks[task_num - 1]
                self.tasks.complete_task(task['id'])
                return f"Great! Marked '{task['title']}' as complete."
        except:
            pass
        return "Which task number would you like to mark complete?"
    
    return None

def handle_diary_commands(self, user_input: str, user_lower: str) -> str:
    """Handle diary and insights commands"""
    if not self.diary:
        return None
    
    # Weekly summary
    if "how was my week" in user_lower or "weekly summary" in user_lower or "week summary" in user_lower:
        insights = self.diary.generate_weekly_insights(self.memory, self.ollama)
        return insights
    
    return None

def handle_project_commands(self, user_input: str, user_lower: str) -> str:
    """Handle project tracking commands"""
    if not self.projects:
        return None
    
    bot_name_lower = self.bot_name.lower()
    
    # Start project
    if ("start project" in user_lower or "new project" in user_lower or "create project" in user_lower) and bot_name_lower in user_lower:
        for phrase in ["start project", "new project", "create project"]:
            if phrase in user_lower:
                project_name = user_input.split(phrase, 1)[1].strip()
                if project_name:
                    project_id = self.projects.create_project(project_name)
                    return f"Project '{project_name}' started! I'll track our progress."
        return "What would you like to name the project?"
    
    # Show projects
    if "show projects" in user_lower or "list projects" in user_lower or "my projects" in user_lower:
        projects = self.projects.get_active_projects()
        if not projects:
            return "You don't have any active projects yet."
        
        result = [f"You have {len(projects)} active project{'s' if len(projects) != 1 else ''}:"]
        for i, proj in enumerate(projects[:5], 1):
            result.append(f"{i}. {proj['name']} - {proj['progress']}% complete")
        return " ".join(result)
    
    # Update project (add work session)
    if "worked on" in user_lower and bot_name_lower in user_lower:
        projects = self.projects.get_active_projects()
        if projects:
            # Use most recent project
            project = projects[0]
            work_desc = user_input.split("worked on", 1)[1].strip()
            self.projects.add_session(project['id'], work_desc, progress_delta=5)
            return f"Logged progress on {project['name']}. Great work!"
        return "Which project did you work on?"
    
    return None

def handle_storytelling_commands(self, user_input: str, user_lower: str) -> str:
    """Handle storytelling commands"""
    if not self.storyteller:
        return None
    
    # Tell story
    if "tell me a story" in user_lower or "tell story" in user_lower:
        # Check for topic
        topic = None
        if " about " in user_lower:
            topic = user_input.split(" about ", 1)[1].strip()
        
        story = self.storyteller.generate_story(topic=topic, length="medium")
        self.current_story = story
        return story
    
    # Continue story
    if "continue the story" in user_lower or "what happens next" in user_lower:
        if self.current_story:
            continuation = self.storyteller.continue_story(self.current_story)
            self.current_story += " " + continuation
            return continuation
        return "I don't have a story to continue. Would you like me to start a new one?"
    
    return None

def handle_special_dates_commands(self, user_input: str, user_lower: str) -> str:
    """Handle birthday and anniversary commands"""
    if not self.special_dates:
        return None
    
    # Add birthday
    if "birthday" in user_lower and ("add" in user_lower or "save" in user_lower or "remember" in user_lower):
        # This would need more sophisticated parsing
        return "I can track birthdays! Just tell me the person's name and date, like 'John's birthday is March 15th'"
    
    # Upcoming special dates
    if "upcoming birthday" in user_lower or "upcoming anniversar" in user_lower or "special dates" in user_lower:
        dates = self.special_dates.get_upcoming_dates(days_ahead=14)
        return self.special_dates.format_upcoming_dates(dates)
    
    # Today's dates
    if "any birthdays today" in user_lower or "special day" in user_lower:
        dates = self.special_dates.get_todays_dates()
        if dates:
            names = [f"{d['person_name']}'s {d['date_type']}" for d in dates]
            return f"Today is {', '.join(names)}!"
        return "No special dates today."
    
    return None

def handle_message_drafting_commands(self, user_input: str, user_lower: str) -> str:
    """Handle email and message drafting commands"""
    if not self.message_drafter:
        return None
    
    # Draft email
    if "draft email" in user_lower or "write email" in user_lower or "compose email" in user_lower:
        # Extract recipient and purpose
        if " to " in user_lower and " about " in user_lower:
            parts = user_input.lower().split(" to ", 1)[1]
            recipient = parts.split(" about ")[0].strip()
            purpose = parts.split(" about ", 1)[1].strip()
            
            draft = self.message_drafter.draft_email(recipient, purpose)
            return f"Here's a draft email:\n\n{draft}\n\nWould you like me to refine it?"
        return "Who should I address the email to, and what's it about?"
    
    # Refine draft
    if self.message_drafter.current_draft:
        if "make it more professional" in user_lower:
            refined = self.message_drafter.make_more_professional()
            return f"Here's the more professional version:\n\n{refined}"
        
        if "make it shorter" in user_lower or "make it more concise" in user_lower:
            refined = self.message_drafter.make_shorter()
            return f"Here's the shorter version:\n\n{refined}"
        
        if "make it friendlier" in user_lower or "make it warmer" in user_lower:
            refined = self.message_drafter.make_friendlier()
            return f"Here's the friendlier version:\n\n{refined}"
    
    return None

def check_pending_reminders(self):
    """Check for reminders that should trigger (called in main loop)"""
    if not self.tasks:
        return
    
    try:
        pending = self.tasks.get_pending_reminders()
        for reminder in pending:
            message = f"Reminder: {reminder['message']}"
            self._speak(message)
            self.tasks.mark_reminder_triggered(reminder['id'])
            
            # Small delay between multiple reminders
            if len(pending) > 1:
                import time
                time.sleep(2)
    except Exception as e:
        self.logger.error(f"Error checking reminders: {e}")

def check_special_dates(self):
    """Check for today's special dates (called on startup)"""
    if not self.special_dates:
        return
    
    try:
        today_dates = self.special_dates.get_todays_dates()
        if today_dates:
            for date in today_dates:
                message = f"By the way, today is {date['person_name']}'s {date['date_type']}!"
                self._speak(message)
                self.special_dates.mark_celebrated(date['id'])
    except Exception as e:
        self.logger.error(f"Error checking special dates: {e}")

def apply_personality_quirks(self, response: str) -> str:
    """Apply personality quirks to responses"""
    if not self.quirks:
        return response
    
    try:
        return self.quirks.inject_personality(response)
    except:
        return response
