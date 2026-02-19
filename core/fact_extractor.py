"""
Fact Extraction - Extract knowledge from natural language

This module analyzes conversation text and extracts structured facts
that can be added to the knowledge graph.
"""

from typing import List, Dict
import re

class FactExtractor:
    """
    Extract knowledge triples from natural language text.
    
    Patterns:
    - "I love/like X" → (user, likes, X)
    - "I use X" → (user, uses, X)
    - "I'm learning X" → (user, is_learning, X)
    - "X requires Y" → (X, requires, Y)
    - "X is for Y" → (X, is_for, Y)
    """
    
    def __init__(self):
        # Compile patterns once for efficiency
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> List[Dict]:
        """Compile regex patterns for fact extraction"""
        return [
            # Preference patterns
            {
                'pattern': re.compile(r"i (?:love|like|enjoy|prefer) (\w+)", re.IGNORECASE),
                'relation': 'likes',
                'subject': 'user',
                'confidence': 0.9
            },
            {
                'pattern': re.compile(r"i (?:hate|dislike|can't stand) (\w+)", re.IGNORECASE),
                'relation': 'dislikes',
                'subject': 'user',
                'confidence': 0.9
            },
            
            # Usage patterns
            {
                'pattern': re.compile(r"i (?:use|work with|utilize) (\w+)", re.IGNORECASE),
                'relation': 'uses',
                'subject': 'user',
                'confidence': 0.85
            },
            
            # Learning patterns
            {
                'pattern': re.compile(r"i'?m? (?:learning|studying|practicing) (\w+)", re.IGNORECASE),
                'relation': 'is_learning',
                'subject': 'user',
                'confidence': 0.9
            },
            
            # Working on patterns
            {
                'pattern': re.compile(r"i'?m? (?:working on|building|creating|developing) (?:a |an )?(\w+)", re.IGNORECASE),
                'relation': 'is_building',
                'subject': 'user',
                'confidence': 0.85
            },
            
            # Knowledge patterns
            {
                'pattern': re.compile(r"i (?:know|understand) (\w+)", re.IGNORECASE),
                'relation': 'knows',
                'subject': 'user',
                'confidence': 0.8
            },
            
            # Want/need patterns
            {
                'pattern': re.compile(r"i (?:want to|need to|planning to) (?:learn|try|explore) (\w+)", re.IGNORECASE),
                'relation': 'wants_to_learn',
                'subject': 'user',
                'confidence': 0.75
            },
            
            # General relationships (X is Y)
            {
                'pattern': re.compile(r"(\w+) is (?:a |an )?(\w+)", re.IGNORECASE),
                'relation': 'is_a',
                'subject': None,  # Extracted from match
                'confidence': 0.7
            },
            
            # X requires Y
            {
                'pattern': re.compile(r"(\w+) requires (\w+)", re.IGNORECASE),
                'relation': 'requires',
                'subject': None,
                'confidence': 0.75
            },
            
            # X is for Y
            {
                'pattern': re.compile(r"(\w+) is (?:for|used for) (\w+)", re.IGNORECASE),
                'relation': 'is_for',
                'subject': None,
                'confidence': 0.75
            }
        ]
    
    def extract_facts(self, text: str) -> List[Dict]:
        """
        Extract all facts from text
        
        Args:
            text: Natural language text
            
        Returns:
            List of fact dictionaries with {subject, relation, object, confidence}
        """
        facts = []
        text_lower = text.lower()
        
        for pattern_def in self.patterns:
            matches = pattern_def['pattern'].finditer(text)
            
            for match in matches:
                if pattern_def['subject']:
                    # Fixed subject (like 'user')
                    subject = pattern_def['subject']
                    obj = match.group(1)
                else:
                    # Subject from pattern
                    if len(match.groups()) >= 2:
                        subject = match.group(1)
                        obj = match.group(2)
                    else:
                        continue
                
                # Clean up extracted entities
                obj = self._clean_entity(obj)
                subject = self._clean_entity(subject)
                
                # Skip if too short or stopwords
                if len(obj) < 3 or len(subject) < 2:
                    continue
                
                if self._is_stopword(obj) or self._is_stopword(subject):
                    continue
                
                facts.append({
                    'subject': subject,
                    'relation': pattern_def['relation'],
                    'object': obj,
                    'confidence': pattern_def['confidence']
                })
        
        # Remove duplicates
        unique_facts = []
        seen = set()
        for fact in facts:
            key = (fact['subject'], fact['relation'], fact['object'])
            if key not in seen:
                seen.add(key)
                unique_facts.append(fact)
        
        return unique_facts
    
    def _clean_entity(self, text: str) -> str:
        """Clean up extracted entity"""
        # Remove punctuation
        text = re.sub(r'[^\w\s-]', '', text)
        # Lowercase and strip
        text = text.lower().strip()
        # Replace multiple spaces
        text = re.sub(r'\s+', '_', text)
        return text
    
    def _is_stopword(self, word: str) -> bool:
        """Check if word is a stopword"""
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        return word.lower() in stopwords


# Example usage
if __name__ == "__main__":
    extractor = FactExtractor()
    
    # Test texts
    test_texts = [
        "I love Python programming",
        "I'm learning machine learning with TensorFlow",
        "I use Docker for my projects",
        "Python is a programming language",
        "Python requires problem solving skills",
        "Machine learning is for data analysis",
        "I want to learn Rust next year"
    ]
    
    print("Extracting facts from test texts:\n")
    for text in test_texts:
        print(f"Text: {text}")
        facts = extractor.extract_facts(text)
        for fact in facts:
            print(f"  → {fact['subject']} {fact['relation']} {fact['object']} (confidence: {fact['confidence']})")
        print()
