"""
Knowledge Graph System - Connect and reason about learned information

This module builds a graph of knowledge where facts are nodes and relationships are edges.
Seven can then reason about connections, make inferences, and discover patterns.
"""

import networkx as nx
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
import json
from pathlib import Path
import config

class KnowledgeGraph:
    """
    Semantic knowledge graph using NetworkX.
    
    Features:
    - Store knowledge triples (subject, relation, object)
    - Automatic inference from patterns
    - Confidence scoring
    - Reasoning path discovery
    - Graph persistence
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()  # Directed graph for relationships
        self.node_data = {}  # Additional metadata per node
        self.inference_rules = []  # Rules for automatic inference
        self.load_from_disk()
        
    def add_fact(self, subject: str, relation: str, obj: str, 
                 confidence: float = 0.8, source: str = "learned"):
        """
        Add a knowledge triple to the graph
        
        Args:
            subject: Entity (e.g., "User")
            relation: Relationship (e.g., "likes", "knows", "uses")
            obj: Object entity (e.g., "Python")
            confidence: How confident we are (0.0 to 1.0)
            source: Where this came from ("learned", "inferred", "corrected")
        """
        # Normalize strings
        subject = subject.strip().lower()
        relation = relation.strip().lower().replace(" ", "_")
        obj = obj.strip().lower()
        
        # Add nodes if they don't exist
        if subject not in self.graph:
            self.graph.add_node(subject)
            self.node_data[subject] = {
                'first_seen': datetime.now().isoformat(),
                'mention_count': 0,
                'type': self._infer_node_type(subject)
            }
        
        if obj not in self.graph:
            self.graph.add_node(obj)
            self.node_data[obj] = {
                'first_seen': datetime.now().isoformat(),
                'mention_count': 0,
                'type': self._infer_node_type(obj)
            }
        
        # Update mention counts
        self.node_data[subject]['mention_count'] += 1
        self.node_data[obj]['mention_count'] += 1
        
        # Add or update edge
        if self.graph.has_edge(subject, obj):
            # Update existing edge
            edge_data = self.graph[subject][obj]
            edge_data['confidence'] = max(edge_data['confidence'], confidence)
            edge_data['updated'] = datetime.now().isoformat()
            edge_data['mention_count'] = edge_data.get('mention_count', 0) + 1
        else:
            # New edge
            self.graph.add_edge(subject, obj,
                              relation=relation,
                              confidence=confidence,
                              source=source,
                              added=datetime.now().isoformat(),
                              updated=datetime.now().isoformat(),
                              mention_count=1)
        
        # Try automatic inference
        if source == "learned":  # Only infer from learned facts
            self._try_inference(subject, relation, obj)
    
    def get_connections(self, entity: str, max_depth: int = 2) -> List[Dict]:
        """
        Get all connections for an entity up to max_depth
        
        Returns list of {target, relation, confidence, path_length}
        """
        entity = entity.strip().lower()
        
        if entity not in self.graph:
            return []
        
        connections = []
        
        # Direct connections (depth 1)
        for neighbor in self.graph.neighbors(entity):
            edge_data = self.graph[entity][neighbor]
            connections.append({
                'target': neighbor,
                'relation': edge_data['relation'],
                'confidence': edge_data['confidence'],
                'path_length': 1,
                'source': edge_data.get('source', 'unknown')
            })
        
        # Indirect connections (depth 2+)
        if max_depth > 1:
            for neighbor in list(self.graph.neighbors(entity)):
                for second_neighbor in self.graph.neighbors(neighbor):
                    if second_neighbor != entity:  # Avoid cycles
                        edge_data = self.graph[neighbor][second_neighbor]
                        connections.append({
                            'target': second_neighbor,
                            'relation': f"{self.graph[entity][neighbor]['relation']}_then_{edge_data['relation']}",
                            'confidence': edge_data['confidence'] * 0.7,  # Reduce confidence for indirect
                            'path_length': 2,
                            'via': neighbor,
                            'source': 'inferred'
                        })
        
        # Sort by confidence
        connections.sort(key=lambda x: x['confidence'], reverse=True)
        
        return connections[:20]  # Limit results
    
    def find_path(self, start: str, end: str, max_length: int = 3) -> Optional[List[str]]:
        """
        Find reasoning path between two concepts
        
        Returns: List of entities forming the path, or None
        """
        start = start.strip().lower()
        end = end.strip().lower()
        
        if start not in self.graph or end not in self.graph:
            return None
        
        try:
            path = nx.shortest_path(self.graph, start, end)
            if len(path) <= max_length + 1:  # +1 because path includes start and end
                return path
        except nx.NetworkXNoPath:
            pass
        
        return None
    
    def explain_connection(self, start: str, end: str) -> Optional[str]:
        """
        Generate natural language explanation of connection
        
        Returns: Explanation string or None
        """
        path = self.find_path(start, end)
        
        if not path or len(path) < 2:
            return None
        
        # Build explanation from path
        explanation_parts = []
        for i in range(len(path) - 1):
            edge_data = self.graph[path[i]][path[i+1]]
            relation = edge_data['relation'].replace('_', ' ')
            explanation_parts.append(f"{path[i]} {relation} {path[i+1]}")
        
        return " → ".join(explanation_parts)
    
    def infer_from_pattern(self, pattern_type: str, fact: Dict) -> List[Dict]:
        """
        Apply inference rules to generate new knowledge
        
        Args:
            pattern_type: Type of pattern to apply
            fact: The triggering fact {subject, relation, object}
        
        Returns: List of inferred facts
        """
        inferences = []
        subject = fact['subject']
        relation = fact['relation']
        obj = fact['object']
        
        # Pattern 1: If user likes X and X requires Y, user might like Y
        if relation == "likes":
            # Check what object requires
            for neighbor in self.graph.neighbors(obj):
                edge = self.graph[obj][neighbor]
                if edge['relation'] == "requires":
                    inferences.append({
                        'subject': subject,
                        'relation': 'might_like',
                        'object': neighbor,
                        'confidence': 0.5,
                        'reasoning': f"because {obj} requires {neighbor}"
                    })
        
        # Pattern 2: If user uses X and X is_for Y, user is interested_in Y
        if relation == "uses":
            for neighbor in self.graph.neighbors(obj):
                edge = self.graph[obj][neighbor]
                if edge['relation'] == "is_for":
                    inferences.append({
                        'subject': subject,
                        'relation': 'interested_in',
                        'object': neighbor,
                        'confidence': 0.6,
                        'reasoning': f"because {obj} is for {neighbor}"
                    })
        
        # Pattern 3: If X is_a Y and user likes X, user might like other things in Y
        if relation == "likes":
            # Find category of liked thing
            for source in self.graph.predecessors(obj):
                edge = self.graph[source][obj]
                if edge['relation'] == "is_a":
                    category = source
                    # Find other things in same category
                    for other in self.graph.neighbors(category):
                        if other != obj:
                            inferences.append({
                                'subject': subject,
                                'relation': 'might_like',
                                'object': other,
                                'confidence': 0.4,
                                'reasoning': f"because both {obj} and {other} are {category}"
                            })
        
        return inferences
    
    def _try_inference(self, subject: str, relation: str, obj: str):
        """Try to infer new knowledge from a learned fact"""
        fact = {'subject': subject, 'relation': relation, 'object': obj}
        
        # Apply inference patterns
        inferences = self.infer_from_pattern('likes_requires', fact)
        
        # Add inferred facts to graph
        for inference in inferences:
            self.add_fact(
                inference['subject'],
                inference['relation'],
                inference['object'],
                confidence=inference['confidence'],
                source='inferred'
            )
    
    def _infer_node_type(self, node: str) -> str:
        """Infer what type of entity this is"""
        node_lower = node.lower()
        
        if node_lower == 'user':
            return 'person'
        elif any(word in node_lower for word in ['python', 'javascript', 'java', 'rust']):
            return 'programming_language'
        elif any(word in node_lower for word in ['coding', 'programming', 'development']):
            return 'skill'
        elif any(word in node_lower for word in ['project', 'app', 'application']):
            return 'project'
        else:
            return 'concept'
    
    def get_user_interests(self, min_confidence: float = 0.5) -> List[Dict]:
        """Get what we know about user's interests"""
        if 'user' not in self.graph:
            return []
        
        interests = []
        for neighbor in self.graph.neighbors('user'):
            edge = self.graph['user'][neighbor]
            if edge['confidence'] >= min_confidence:
                interests.append({
                    'interest': neighbor,
                    'relation': edge['relation'],
                    'confidence': edge['confidence'],
                    'source': edge.get('source', 'unknown')
                })
        
        interests.sort(key=lambda x: x['confidence'], reverse=True)
        return interests
    
    def get_node_context(self, entity: str) -> str:
        """
        Generate context summary about an entity
        
        Returns: Natural language summary
        """
        entity = entity.strip().lower()
        
        if entity not in self.graph:
            return f"I don't know much about {entity} yet."
        
        # Get connections
        connections = self.get_connections(entity, max_depth=1)
        
        if not connections:
            return f"I've heard of {entity} but don't know details."
        
        # Build summary
        node_type = self.node_data[entity].get('type', 'concept')
        summary_parts = [f"{entity} ({node_type})"]
        
        # Group by relation type
        relations = {}
        for conn in connections[:5]:  # Top 5
            rel = conn['relation']
            if rel not in relations:
                relations[rel] = []
            relations[rel].append(conn['target'])
        
        # Format
        for rel, targets in relations.items():
            rel_text = rel.replace('_', ' ')
            targets_text = ', '.join(targets[:3])
            summary_parts.append(f"{rel_text}: {targets_text}")
        
        return '; '.join(summary_parts)
    
    def save_to_disk(self):
        """Persist graph to disk"""
        save_path = config.DATA_DIR / "knowledge_graph.json"
        
        try:
            # Convert graph to JSON-serializable format
            data = {
                'nodes': list(self.graph.nodes()),
                'edges': [
                    {
                        'source': u,
                        'target': v,
                        'data': self.graph[u][v]
                    }
                    for u, v in self.graph.edges()
                ],
                'node_data': self.node_data,
                'saved_at': datetime.now().isoformat()
            }
            
            save_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"[WARNING]  Error saving knowledge graph: {e}")
    
    def load_from_disk(self):
        """Load graph from disk"""
        load_path = config.DATA_DIR / "knowledge_graph.json"
        
        if not load_path.exists():
            return
        
        try:
            data = json.loads(load_path.read_text())
            
            # Reconstruct graph
            self.graph = nx.DiGraph()
            self.graph.add_nodes_from(data['nodes'])
            
            for edge in data['edges']:
                self.graph.add_edge(
                    edge['source'],
                    edge['target'],
                    **edge['data']
                )
            
            self.node_data = data.get('node_data', {})
            
        except Exception as e:
            print(f"[WARNING]  Error loading knowledge graph: {e}")
    
    def get_stats(self) -> Dict:
        """Get graph statistics"""
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'learned_facts': sum(1 for _, _, d in self.graph.edges(data=True) if d.get('source') == 'learned'),
            'inferred_facts': sum(1 for _, _, d in self.graph.edges(data=True) if d.get('source') == 'inferred'),
            'avg_connections': self.graph.number_of_edges() / max(self.graph.number_of_nodes(), 1)
        }


# Example usage and testing
if __name__ == "__main__":
    # Test knowledge graph
    kg = KnowledgeGraph()
    
    # Add some facts
    print("Adding facts...")
    kg.add_fact("user", "likes", "python", confidence=0.9)
    kg.add_fact("python", "is_a", "programming_language", confidence=1.0)
    kg.add_fact("python", "is_for", "data_analysis", confidence=0.8)
    kg.add_fact("python", "requires", "problem_solving", confidence=0.7)
    kg.add_fact("user", "is_building", "chatbot", confidence=0.9)
    kg.add_fact("chatbot", "uses", "python", confidence=0.9)
    
    # Get connections
    print("\nConnections for 'user':")
    connections = kg.get_connections("user")
    for conn in connections:
        print(f"  {conn['relation']} → {conn['target']} (confidence: {conn['confidence']:.2f}, source: {conn['source']})")
    
    # Find path
    print("\nPath from 'user' to 'data_analysis':")
    path = kg.find_path("user", "data_analysis")
    if path:
        print(f"  {' → '.join(path)}")
        explanation = kg.explain_connection("user", "data_analysis")
        print(f"  Explanation: {explanation}")
    
    # Get interests
    print("\nUser interests:")
    interests = kg.get_user_interests()
    for interest in interests:
        print(f"  {interest['relation']} {interest['interest']} (confidence: {interest['confidence']:.2f})")
    
    # Stats
    print("\nGraph statistics:")
    stats = kg.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Save
    kg.save_to_disk()
    print("\n[OK] Saved to disk")
