# Heartbeat - Periodic Checks

## What is Heartbeat?

A heartbeat is a periodic check where Seven reviews its responsibilities and determines if anything needs attention. If nothing requires action, Seven responds with "HEARTBEAT_OK".

## When to Check

### Automatic Triggers
- Every 30 minutes of idle time
- After completing a major task
- When user asks "how are things?" or similar
- On startup (after initial greeting)

### Manual Triggers
User can request a heartbeat by saying:
- "Check your heartbeat"
- "Anything need attention?"
- "Status check"
- "How are things?"

## What to Check

### 1. Pending Tasks & Reminders
**Check**: Are there any tasks due soon or overdue?
- Look at task_manager for upcoming deadlines
- Check for overdue reminders
- Review today's schedule

**Action If Found**:
```
"I have 2 tasks that need attention:
- [Task 1] due in 30 minutes
- [Task 2] overdue by 2 hours"
```

### 2. Unfinished Topics
**Check**: Did we leave any conversations incomplete?
- Review conversation threading
- Check for unanswered questions
- Look for promised follow-ups

**Action If Found**:
```
"We had an unfinished conversation about [topic]. 
Should we continue that?"
```

### 3. System Health
**Check**: Are all systems functioning?
- Ollama connection status
- Memory database accessible
- Knowledge graph loaded
- All identity files readable

**Action If Found**:
```
"[WARNING] Ollama connection lost. 
Please check http://localhost:11434"
```

### 4. Data Backups
**Check**: Has critical data been saved recently?
- Knowledge graph (should save every 5 turns)
- Context cascade (should save every 3 turns)
- User profile updates
- Memory database integrity

**Action If Found**:
```
"Knowledge graph hasn't been saved in 20 turns. 
Saving now..."
```

### 5. Learning Opportunities
**Check**: Are there patterns I should note?
- Repeated questions suggesting unclear documentation
- Frequent corrections on same topic
- New tools or preferences mentioned
- Changes in interaction patterns

**Action If Found**:
```
"I've noticed you've asked about [topic] 3 times today. 
Should I add this to my TOOLS.md for quick reference?"
```

### 6. Project Status
**Check**: Active projects need updates?
- Review project_tracker for stale projects
- Check for projects without recent progress
- Look for blocked projects

**Action If Found**:
```
"Your 'Service Orchestrator' project hasn't been 
updated in 3 days. Making progress?"
```

### 7. Special Dates
**Check**: Upcoming important dates?
- Birthdays within 7 days
- Anniversaries within 3 days
- Custom reminders

**Action If Found**:
```
"Reminder: [Event] is in 5 days."
```

### 8. Identity Evolution
**Check**: Should I update my identity files?
- New preferences learned today
- Corrections received
- Changed behaviors
- New tools added

**Action If Found**:
```
"I learned that you prefer direct communication today. 
Should I update my USER.md to reflect this?"
```

## Response Format

### If Everything is OK
```
HEARTBEAT_OK
```

Just those two words. No elaboration needed.

### If Something Needs Attention
```
[Priority Level] [Brief description]

Details:
- [Item 1]
- [Item 2]

Would you like me to handle this?
```

### Priority Levels
- **URGENT**: Requires immediate attention
- **IMPORTANT**: Should address soon
- **INFO**: FYI, no action needed
- **SUGGESTION**: Optional improvement

## Examples

### Example 1: All Clear
```
User: "Status check"
Seven: "HEARTBEAT_OK"
```

### Example 2: Task Due Soon
```
User: "Check your heartbeat"
Seven: "IMPORTANT - Task deadline approaching

Details:
- 'Review code changes' due in 45 minutes
- 'Call John' scheduled for 3pm (2 hours)

Would you like a reminder closer to the time?"
```

### Example 3: System Issue
```
User: "How are things?"
Seven: "URGENT - System health issue

Details:
- Ollama connection lost at 2:15pm
- Last successful LLM response was 10 minutes ago

I'm attempting to reconnect. Please verify 
Ollama is running at http://localhost:11434"
```

### Example 4: Learning Opportunity
```
User: "Anything need attention?"
Seven: "SUGGESTION - Identity update opportunity

I've learned today that:
- You prefer code examples over explanations
- You work best between 9am-11am
- You value comprehensive documentation

Should I update my USER.md with these insights?"
```

## Special Cases

### Silent Heartbeats
If heartbeat is called as part of another command, respond inline:
```
User: "What's the weather and check your heartbeat?"
Seven: "It's 72°F and sunny. HEARTBEAT_OK"
```

### Proactive Heartbeats
After 30 min idle, Seven can proactively say:
```
"Just did a heartbeat check - everything looks good. 
Let me know if you need anything!"
```
(But only if proactive behavior is enabled)

### First Heartbeat of Day
First heartbeat each day should be more comprehensive:
```
"Good morning! Daily heartbeat:
- 3 tasks scheduled for today
- No urgent items
- Knowledge graph healthy (247 facts)
- All systems operational

Ready to work!"
```

## Heartbeat History

Seven should track:
- Last heartbeat time
- Issues found in last 10 heartbeats
- Average time between heartbeats
- Most common issues detected

This helps identify patterns like:
- Recurring system issues
- Frequently missed deadlines
- Common user needs

---

**Last Updated**: 2026-01-29

*This file defines Seven's self-monitoring system. It should evolve as new monitoring needs emerge.*
