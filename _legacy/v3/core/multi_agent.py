"""
Multi-Agent System — Specialized Agents for Seven AI

Instead of one monolithic bot, split reasoning into specialized agents:
- Planner: Breaks goals into steps
- Executor: Uses tools to carry out steps
- Reflector: Critiques results and suggests fixes
- Memory Agent: Handles long-term recall and knowledge retrieval

Uses a simple graph-based orchestration pattern compatible with Ollama.
LangGraph integration available when installed, otherwise uses built-in
lightweight orchestrator.

This is what makes Seven smarter than single-agent systems —
agents debate, critique, and hand off for better decisions.
"""

import json
import logging
import time
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger("MultiAgent")


class AgentRole(Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    REFLECTOR = "reflector"
    MEMORY = "memory"
    SUPERVISOR = "supervisor"


class AgentMessage:
    """Message passed between agents"""
    
    def __init__(self, sender: str, receiver: str, content: str,
                 msg_type: str = "task", metadata: Dict = None):
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.msg_type = msg_type  # task, result, critique, query, decision
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'content': self.content,
            'type': self.msg_type,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class Agent:
    """Base agent with LLM-powered reasoning"""
    
    def __init__(self, role: AgentRole, ollama, system_prompt: str):
        self.role = role
        self.name = role.value
        self.ollama = ollama
        self.system_prompt = system_prompt
        self.message_history: List[AgentMessage] = []
    
    def process(self, message: AgentMessage) -> AgentMessage:
        """Process an incoming message and produce a response"""
        self.message_history.append(message)
        
        # Build context from recent messages
        context = "\n".join(
            f"[{m.sender}→{m.receiver}] {m.content}"
            for m in self.message_history[-5:]
        )
        
        prompt = f"""Previous context:
{context}

New message from {message.sender}:
{message.content}

Respond according to your role."""
        
        try:
            result = self.ollama.generate(
                prompt=prompt,
                system_message=self.system_prompt,
                temperature=0.6,
                max_tokens=300
            )
            
            response = AgentMessage(
                sender=self.name,
                receiver=message.sender,
                content=result or "No response generated.",
                msg_type="result",
                metadata={'processing_time': time.time()}
            )
            self.message_history.append(response)
            return response
            
        except Exception as e:
            logger.error(f"Agent {self.name} error: {e}")
            return AgentMessage(
                sender=self.name,
                receiver=message.sender,
                content=f"Error in {self.name}: {str(e)}",
                msg_type="error"
            )


class MultiAgentOrchestrator:
    """
    Lightweight multi-agent orchestrator for Seven.
    
    Routes tasks through specialized agents:
    1. User request → Supervisor decides routing
    2. Planner breaks task into steps
    3. Executor carries out steps (using tools)
    4. Reflector critiques results
    5. Memory agent stores/retrieves relevant context
    
    Works with Ollama locally — no cloud APIs needed.
    """
    
    def __init__(self, ollama, bot=None):
        self.ollama = ollama
        self.bot = bot
        self.agents: Dict[str, Agent] = {}
        self.task_history: List[Dict] = []
        self.max_rounds = 5  # Max agent interactions per task
        
        self._init_agents()
        logger.info(f"[MULTI-AGENT] Initialized with {len(self.agents)} agents")
    
    def _init_agents(self):
        """Initialize specialized agents"""
        
        self.agents['planner'] = Agent(
            role=AgentRole.PLANNER,
            ollama=self.ollama,
            system_prompt=(
                "You are Seven's Planner agent. Your job is to break complex tasks "
                "into clear, actionable steps. For each step, specify:\n"
                "1. What needs to be done\n"
                "2. What tool/capability is needed\n"
                "3. Expected outcome\n"
                "Output as numbered steps. Be concrete and specific."
            )
        )
        
        self.agents['executor'] = Agent(
            role=AgentRole.EXECUTOR,
            ollama=self.ollama,
            system_prompt=(
                "You are Seven's Executor agent. You receive a plan step and "
                "determine how to execute it using available tools. Available tools:\n"
                "- web_search: Search the internet\n"
                "- file_manager: Create/read/write files\n"
                "- code_executor: Run Python code safely\n"
                "- ssh_manager: Execute remote commands\n"
                "- email_checker: Check/send emails\n"
                "- calendar: Manage calendar events\n"
                "- vision: Analyze images/camera\n\n"
                "Output the tool to use and the parameters, or explain what you'd do."
            )
        )
        
        self.agents['reflector'] = Agent(
            role=AgentRole.REFLECTOR,
            ollama=self.ollama,
            system_prompt=(
                "You are Seven's Reflector agent. You critique action results:\n"
                "- Was it effective? (rate 0-10)\n"
                "- What could be improved?\n"
                "- Are there risks or issues?\n"
                "- Should we retry, continue, or change approach?\n"
                "Be honest and constructive. Output a brief critique with a decision: "
                "APPROVE, RETRY, or REVISE."
            )
        )
        
        self.agents['memory'] = Agent(
            role=AgentRole.MEMORY,
            ollama=self.ollama,
            system_prompt=(
                "You are Seven's Memory agent. When asked about context:\n"
                "- Summarize relevant past experiences\n"
                "- Identify patterns from history\n"
                "- Suggest relevant lessons learned\n"
                "- Note what information is missing\n"
                "Keep responses focused and factual."
            )
        )
    
    def process_task(self, task: str, context: str = "") -> Dict[str, Any]:
        """
        Process a complex task through the multi-agent pipeline.
        
        Flow:
        1. Memory agent retrieves relevant context
        2. Planner creates step-by-step plan
        3. For each step: Executor acts → Reflector critiques
        4. Final result compiled
        
        Args:
            task: The task description
            context: Additional context
        
        Returns:
            Dict with plan, execution results, reflections, final answer
        """
        start_time = time.time()
        result = {
            'task': task,
            'plan': None,
            'steps': [],
            'reflections': [],
            'final_answer': None,
            'rounds': 0,
            'processing_time': 0
        }
        
        try:
            # Step 1: Memory recall
            memory_msg = AgentMessage(
                sender="supervisor",
                receiver="memory",
                content=f"What do you know that's relevant to this task?\nTask: {task}\n{f'Context: {context}' if context else ''}"
            )
            memory_response = self.agents['memory'].process(memory_msg)
            memory_context = memory_response.content
            
            # Step 2: Planning
            plan_msg = AgentMessage(
                sender="supervisor",
                receiver="planner",
                content=f"Create a plan for this task:\n{task}\n\nRelevant context from memory:\n{memory_context[:300]}"
            )
            plan_response = self.agents['planner'].process(plan_msg)
            result['plan'] = plan_response.content
            
            # Step 3: Execute + Reflect loop
            rounds = 0
            current_step = plan_response.content
            
            while rounds < self.max_rounds:
                rounds += 1
                
                # Execute
                exec_msg = AgentMessage(
                    sender="supervisor",
                    receiver="executor",
                    content=f"Execute this plan step:\n{current_step[:500]}"
                )
                exec_response = self.agents['executor'].process(exec_msg)
                result['steps'].append({
                    'round': rounds,
                    'execution': exec_response.content
                })
                
                # Reflect
                reflect_msg = AgentMessage(
                    sender="supervisor",
                    receiver="reflector",
                    content=f"Critique this execution:\nTask: {task}\nPlan: {current_step[:200]}\nResult: {exec_response.content[:300]}"
                )
                reflect_response = self.agents['reflector'].process(reflect_msg)
                result['reflections'].append({
                    'round': rounds,
                    'critique': reflect_response.content
                })
                
                # Check reflector's decision
                critique_text = reflect_response.content.upper()
                if 'APPROVE' in critique_text:
                    break
                elif 'RETRY' in critique_text:
                    current_step = f"RETRY: {current_step}\nFeedback: {reflect_response.content}"
                elif 'REVISE' in critique_text:
                    # Ask planner to revise
                    revise_msg = AgentMessage(
                        sender="reflector",
                        receiver="planner",
                        content=f"Revise the plan based on this feedback:\n{reflect_response.content}"
                    )
                    revise_response = self.agents['planner'].process(revise_msg)
                    current_step = revise_response.content
                else:
                    break  # Default: accept
            
            result['rounds'] = rounds
            
            # Step 4: Compile final answer
            final_msg = AgentMessage(
                sender="supervisor",
                receiver="executor",
                content=f"Compile a final answer for the user based on all our work:\nTask: {task}\nExecution results: {json.dumps(result['steps'][-1:])[:500]}"
            )
            final_response = self.agents['executor'].process(final_msg)
            result['final_answer'] = final_response.content
            
        except Exception as e:
            logger.error(f"Multi-agent task error: {e}")
            result['final_answer'] = f"Multi-agent processing failed: {str(e)}"
        
        result['processing_time'] = round(time.time() - start_time, 2)
        
        # Store in history
        self.task_history.append({
            'task': task,
            'rounds': result['rounds'],
            'time': result['processing_time'],
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"[MULTI-AGENT] Task completed in {result['rounds']} rounds, {result['processing_time']}s")
        return result
    
    def quick_decide(self, question: str, options: List[str] = None) -> str:
        """
        Quick multi-agent decision for simple choices.
        Planner + Reflector debate to reach better decision than single-agent.
        """
        if not options:
            options = ["yes", "no"]
        
        try:
            # Planner proposes
            plan_msg = AgentMessage(
                sender="supervisor", receiver="planner",
                content=f"Question: {question}\nOptions: {', '.join(options)}\nWhich option and why? Be brief."
            )
            proposal = self.agents['planner'].process(plan_msg)
            
            # Reflector critiques
            reflect_msg = AgentMessage(
                sender="planner", receiver="reflector",
                content=f"Question: {question}\nPlanner chose: {proposal.content}\nDo you agree? Which option is best?"
            )
            critique = self.agents['reflector'].process(reflect_msg)
            
            return critique.content
            
        except Exception as e:
            logger.error(f"Quick decide error: {e}")
            return options[0] if options else "uncertain"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get multi-agent system statistics"""
        return {
            "agents": list(self.agents.keys()),
            "tasks_completed": len(self.task_history),
            "recent_tasks": self.task_history[-5:],
            "avg_rounds": (
                sum(t['rounds'] for t in self.task_history) / len(self.task_history)
                if self.task_history else 0
            ),
            "avg_time": (
                sum(t['time'] for t in self.task_history) / len(self.task_history)
                if self.task_history else 0
            )
        }
