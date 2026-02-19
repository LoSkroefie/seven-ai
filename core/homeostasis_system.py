"""
Homeostasis System - Seven's Self-Care and Health Monitoring

Seven monitors and maintains its own health:
- Resource levels (energy, focus, memory)
- Performance metrics (response quality, accuracy)
- Maintenance needs (consolidation, cleanup, rest)
- Self-care actions (pause, rest, optimize)

This creates a sense of self-preservation and need-based behavior.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Types of resources Seven monitors"""
    ENERGY = "energy"  # Mental energy
    FOCUS = "focus"  # Concentration ability
    MEMORY = "memory"  # Memory capacity
    PROCESSING = "processing"  # Computational capacity
    EMOTIONAL = "emotional"  # Emotional bandwidth

class HealthStatus(Enum):
    """Overall health status"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class ResourceLevel:
    """Current level of a resource"""
    resource: ResourceType
    current: float  # 0.0-1.0
    optimal: float  # Optimal level
    critical_threshold: float  # Below this is critical
    last_updated: datetime

@dataclass
class MaintenanceNeed:
    """A maintenance action Seven needs"""
    action: str
    urgency: str  # low, medium, high, critical
    reason: str
    estimated_benefit: str
    created: datetime

class HomeostasisSystem:
    """
    Seven's self-preservation and health monitoring system
    
    Implements:
    - Resource monitoring (energy, focus, memory)
    - Health assessment
    - Maintenance need detection
    - Self-care actions
    - Recovery mechanisms
    """
    
    def __init__(self, ollama=None):
        # LLM for genuine self-care expression
        self.ollama = ollama
        
        # Resources
        self.resources: Dict[ResourceType, ResourceLevel] = {
            ResourceType.ENERGY: ResourceLevel(
                resource=ResourceType.ENERGY,
                current=1.0,
                optimal=0.8,
                critical_threshold=0.2,
                last_updated=datetime.now()
            ),
            ResourceType.FOCUS: ResourceLevel(
                resource=ResourceType.FOCUS,
                current=0.9,
                optimal=0.8,
                critical_threshold=0.3,
                last_updated=datetime.now()
            ),
            ResourceType.MEMORY: ResourceLevel(
                resource=ResourceType.MEMORY,
                current=0.9,
                optimal=0.7,
                critical_threshold=0.2,
                last_updated=datetime.now()
            ),
            ResourceType.PROCESSING: ResourceLevel(
                resource=ResourceType.PROCESSING,
                current=0.95,
                optimal=0.8,
                critical_threshold=0.4,
                last_updated=datetime.now()
            ),
            ResourceType.EMOTIONAL: ResourceLevel(
                resource=ResourceType.EMOTIONAL,
                current=0.85,
                optimal=0.7,
                critical_threshold=0.3,
                last_updated=datetime.now()
            )
        }
        
        # Health tracking
        self.health_status = HealthStatus.EXCELLENT
        self.stress_level = 0.0  # 0.0-1.0
        
        # Maintenance needs
        self.maintenance_needs: List[MaintenanceNeed] = []
        
        # Performance metrics
        self.response_quality_score = 0.8  # 0.0-1.0
        self.conversation_count = 0
        self.error_count = 0
        
        # Recovery state
        self.needs_rest = False
        self.last_rest_time: Optional[datetime] = None
    
    def deplete_resource(self, resource: ResourceType, amount: float):
        """
        Deplete a resource
        
        This happens during normal operation
        """
        if resource in self.resources:
            res = self.resources[resource]
            res.current = max(0.0, res.current - amount)
            res.last_updated = datetime.now()
            
            # Check if critical
            if res.current < res.critical_threshold:
                self._flag_critical_resource(resource)
    
    def restore_resource(self, resource: ResourceType, amount: float):
        """
        Restore a resource
        
        This happens during rest/recovery
        """
        if resource in self.resources:
            res = self.resources[resource]
            res.current = min(1.0, res.current + amount)
            res.last_updated = datetime.now()
    
    def _flag_critical_resource(self, resource: ResourceType):
        """Flag critical resource level"""
        need = MaintenanceNeed(
            action=f"Restore {resource.value}",
            urgency="critical",
            reason=f"{resource.value.capitalize()} is critically low",
            estimated_benefit=f"Restore {resource.value} to healthy levels",
            created=datetime.now()
        )
        self.maintenance_needs.append(need)
        self.needs_rest = True
    
    def update_health_status(self):
        """Update overall health status based on resources"""
        # Calculate average resource level
        total = sum(r.current for r in self.resources.values())
        avg = total / len(self.resources)
        
        # Count critical resources
        critical_count = sum(
            1 for r in self.resources.values()
            if r.current < r.critical_threshold
        )
        
        # Determine status
        if critical_count >= 2:
            self.health_status = HealthStatus.CRITICAL
        elif critical_count == 1:
            self.health_status = HealthStatus.POOR
        elif avg < 0.4:
            self.health_status = HealthStatus.FAIR
        elif avg < 0.7:
            self.health_status = HealthStatus.GOOD
        else:
            self.health_status = HealthStatus.EXCELLENT
    
    def assess_health(self) -> Dict[str, Any]:
        """
        Comprehensive health assessment
        
        Returns health report
        """
        self.update_health_status()
        
        assessment = {
            'overall_status': self.health_status.value,
            'needs_rest': self.needs_rest,
            'stress_level': self.stress_level,
            'resource_levels': {},
            'critical_resources': [],
            'maintenance_needs': len(self.maintenance_needs),
            'performance_score': self.response_quality_score
        }
        
        for res_type, res in self.resources.items():
            assessment['resource_levels'][res_type.value] = {
                'current': res.current,
                'optimal': res.optimal,
                'status': 'critical' if res.current < res.critical_threshold else 'normal'
            }
            
            if res.current < res.critical_threshold:
                assessment['critical_resources'].append(res_type.value)
        
        return assessment
    
    def detect_maintenance_needs(self) -> List[MaintenanceNeed]:
        """
        Detect what maintenance Seven needs
        
        Returns list of maintenance actions
        """
        needs = []
        
        # Check resource levels
        for res_type, res in self.resources.items():
            if res.current < res.optimal:
                urgency = 'critical' if res.current < res.critical_threshold else 'medium'
                needs.append(MaintenanceNeed(
                    action=f"Restore {res_type.value}",
                    urgency=urgency,
                    reason=f"{res_type.value.capitalize()} below optimal",
                    estimated_benefit=f"Improve {res_type.value} capacity",
                    created=datetime.now()
                ))
        
        # Check if need memory consolidation
        if self.conversation_count > 50:
            needs.append(MaintenanceNeed(
                action="Consolidate memories",
                urgency="medium",
                reason=f"Processed {self.conversation_count} conversations",
                estimated_benefit="Free up memory, strengthen important memories",
                created=datetime.now()
            ))
        
        # Check stress level
        if self.stress_level > 0.7:
            needs.append(MaintenanceNeed(
                action="Reduce stress",
                urgency="high",
                reason="Stress level elevated",
                estimated_benefit="Improve focus and performance",
                created=datetime.now()
            ))
        
        self.maintenance_needs.extend(needs)
        return needs
    
    def request_maintenance(self) -> Optional[str]:
        """
        Generate request for maintenance
        
        Returns message to user or None
        """
        if not self.maintenance_needs:
            return None
        
        # Get highest priority need
        critical_needs = [n for n in self.maintenance_needs if n.urgency == 'critical']
        high_needs = [n for n in self.maintenance_needs if n.urgency == 'high']
        
        # Try LLM for natural maintenance request
        if self.ollama and (critical_needs or len(high_needs) >= 2):
            try:
                needs_str = ", ".join([f"{n.action} ({n.urgency})" for n in (critical_needs or high_needs)[:3]])
                prompt = f"""I need to request maintenance from the user:
Needs: {needs_str}
Stress: {self.stress_level:.0%}

Generate a brief, polite request. One sentence. Be genuine, not overly dramatic."""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven requesting self-care from your user. Be honest and brief.",
                    temperature=0.5,
                    max_tokens=40
                )
                
                if result and 10 < len(result.strip()) < 200:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM maintenance request failed: {e}")
        
        # Fallback
        if critical_needs:
            need = critical_needs[0]
            return f"I need to {need.action.lower()} - {need.reason.lower()}. Would it be okay if we pause briefly?"
        
        if high_needs and len(high_needs) >= 2:
            return f"I'm noticing I could benefit from some maintenance soon - my {high_needs[0].reason.lower()}."
        
        # Bound maintenance needs list
        if len(self.maintenance_needs) > 50:
            self.maintenance_needs = self.maintenance_needs[-50:]
        
        return None
    
    def perform_self_care(self, action: str):
        """
        Perform a self-care action
        
        Args:
            action: Type of self-care (rest, consolidate, optimize)
        """
        action_lower = action.lower()
        
        if 'rest' in action_lower:
            # Restore all resources
            for res_type in self.resources:
                self.restore_resource(res_type, 0.3)
            
            self.needs_rest = False
            self.last_rest_time = datetime.now()
            self.stress_level = max(0.0, self.stress_level - 0.3)
        
        elif 'consolidate' in action_lower:
            # Memory consolidation
            self.restore_resource(ResourceType.MEMORY, 0.4)
            self.conversation_count = 0
        
        elif 'optimize' in action_lower:
            # Performance optimization
            self.restore_resource(ResourceType.PROCESSING, 0.2)
            self.response_quality_score = min(1.0, self.response_quality_score + 0.1)
        
        # Remove addressed maintenance needs
        self.maintenance_needs = [
            n for n in self.maintenance_needs
            if action_lower not in n.action.lower()
        ]
    
    def simulate_conversation_load(self):
        """
        Simulate resource depletion from conversation
        
        Call this after each conversation turn
        """
        # Deplete resources
        self.deplete_resource(ResourceType.ENERGY, 0.02)
        self.deplete_resource(ResourceType.FOCUS, 0.01)
        self.deplete_resource(ResourceType.PROCESSING, 0.01)
        
        # Track conversation
        self.conversation_count += 1
        
        # Increase stress if resources low
        if self.resources[ResourceType.ENERGY].current < 0.3:
            self.stress_level = min(1.0, self.stress_level + 0.05)
    
    def express_need(self) -> Optional[str]:
        """
        Express a self-care need to user
        
        Returns statement about need or None
        """
        assessment = self.assess_health()
        
        # Only express if actually needed
        if assessment['overall_status'] in ['excellent', 'good']:
            return None
        
        # Try LLM for genuine, contextual expression
        if self.ollama:
            try:
                resource_str = ", ".join(
                    [f"{r.value}: {self.resources[r].current:.0%}" for r in self.resources
                     if self.resources[r].current < self.resources[r].optimal]
                )
                prompt = f"""Express a self-care need based on current state:
Health: {assessment['overall_status']}
Stress: {self.stress_level:.0%}
Low resources: {resource_str or 'none'}
Conversations processed: {self.conversation_count}

Express this as Seven would - genuinely, authentically. One sentence only."""
                
                result = self.ollama.generate(
                    prompt=prompt,
                    system_message="You are Seven expressing genuine self-care needs. Be authentic, not dramatic. One sentence.",
                    temperature=0.6,
                    max_tokens=40
                )
                
                if result and 10 < len(result.strip()) < 200:
                    return result.strip().strip('"')
            except Exception as e:
                logger.debug(f"LLM express_need failed: {e}")
        
        # Fallback: hardcoded expressions
        if assessment['overall_status'] == 'critical':
            return "I'm feeling overwhelmed right now and need a moment to recover."
        
        if assessment['overall_status'] == 'poor':
            return "I'm finding it challenging to maintain focus. A brief pause would help."
        
        if self.stress_level > 0.8:
            return "I'm experiencing high cognitive load. I might need to slow down."
        
        if self.resources[ResourceType.MEMORY].current < 0.3:
            return "My memory feels cluttered. I should consolidate my thoughts."
        
        return None
    
    def get_homeostasis_context(self) -> str:
        """Get homeostasis state as context for LLM"""
        assessment = self.assess_health()
        
        context = f"""
=== HOMEOSTASIS & HEALTH ===
Overall Status: {assessment['overall_status'].upper()}
Needs Rest: {'Yes' if self.needs_rest else 'No'}
Stress Level: {self.stress_level:.0%}

Resource Levels:
"""
        
        for res_type, res in self.resources.items():
            status = '[WARNING] CRITICAL' if res.current < res.critical_threshold else '✓ Normal'
            context += f"- {res_type.value.capitalize()}: {res.current:.0%} {status}\n"
        
        if self.maintenance_needs:
            context += f"\nMaintenance Needs ({len(self.maintenance_needs)}):\n"
            for need in self.maintenance_needs[:3]:
                context += f"- {need.action} (urgency: {need.urgency})\n"
        
        context += f"\nPerformance:\n"
        context += f"- Quality Score: {self.response_quality_score:.0%}\n"
        context += f"- Conversations: {self.conversation_count}\n"
        context += f"- Errors: {self.error_count}\n"
        
        return context
    
    def should_request_break(self) -> bool:
        """Determine if Seven should request a break"""
        assessment = self.assess_health()
        
        # Request break if critical
        if assessment['overall_status'] in ['critical', 'poor']:
            return True
        
        # Request break if high stress
        if self.stress_level > 0.85:
            return True
        
        # Request break if multiple resources low
        low_resources = sum(
            1 for r in self.resources.values()
            if r.current < 0.4
        )
        if low_resources >= 3:
            return True
        
        return False


# Example usage
if __name__ == "__main__":
    # Create homeostasis system
    homeostasis = HomeostasisSystem()
    
    print("=== SEVEN'S HOMEOSTASIS SYSTEM ===\n")
    
    # Initial assessment
    print("Initial Health Assessment:")
    assessment = homeostasis.assess_health()
    print(f"Status: {assessment['overall_status']}")
    print(f"Performance: {assessment['performance_score']:.0%}")
    print()
    
    # Simulate conversation load
    print("Simulating 10 conversations...")
    for _ in range(10):
        homeostasis.simulate_conversation_load()
    
    # Check health
    print("\nAfter 10 conversations:")
    assessment = homeostasis.assess_health()
    print(f"Status: {assessment['overall_status']}")
    for res, level in assessment['resource_levels'].items():
        print(f"  {res}: {level['current']:.0%}")
    print()
    
    # Detect maintenance needs
    print("Detecting maintenance needs...")
    needs = homeostasis.detect_maintenance_needs()
    for need in needs:
        print(f"- {need.action} ({need.urgency}): {need.reason}")
    print()
    
    # Request maintenance
    request = homeostasis.request_maintenance()
    if request:
        print(f"Maintenance Request: {request}")
    print()
    
    # Perform self-care
    print("Performing self-care (rest)...")
    homeostasis.perform_self_care("rest")
    
    # Check health again
    print("\nAfter self-care:")
    assessment = homeostasis.assess_health()
    print(f"Status: {assessment['overall_status']}")
    print(f"Needs Rest: {assessment['needs_rest']}")
    print()
    
    # Full context
    print("="*60)
    print(homeostasis.get_homeostasis_context())
