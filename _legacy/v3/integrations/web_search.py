"""
Web search and content fetching capabilities
Enables Seven to search the web AND read page content
"""
from googlesearch import search
from typing import List, Optional
import re
import logging

logger = logging.getLogger(__name__)


def google_search(query: str, num_results: int = 5) -> str:
    """
    Perform Google search
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        Formatted search results
    """
    if not query or not query.strip():
        return "[ERROR] No search query provided"
    
    try:
        print(f"[SEARCH] Searching Google for: {query}")
        results = []
        
        for url in search(query, num_results=num_results):
            results.append(url)
        
        if not results:
            return f"No results found for '{query}'"
        
        # Format results
        output = [f"[SEARCH] Top {len(results)} results for '{query}':"]
        for i, url in enumerate(results, 1):
            output.append(f"{i}. {url}")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"[ERROR] Search error: {str(e)}"


def fetch_webpage_content(url: str, max_chars: int = 3000) -> str:
    """
    Fetch and extract readable text content from a webpage.
    This gives Seven the ability to actually READ web pages, not just list URLs.
    
    Args:
        url: URL to fetch
        max_chars: Maximum characters to return
        
    Returns:
        Extracted text content or error message
    """
    try:
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        html = response.text
        
        # Try BeautifulSoup first for better extraction
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
        except ImportError:
            # Fallback: regex-based HTML stripping
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', text)
            text = re.sub(r'\s+', ' ', text).strip()
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        if len(text) > max_chars:
            text = text[:max_chars] + "...[truncated]"
        
        return f"[WEB CONTENT from {url}]\n{text}" if text else f"[WARNING] No readable content found at {url}"
        
    except ImportError:
        return "[ERROR] 'requests' package not installed. Install with: pip install requests"
    except Exception as e:
        return f"[ERROR] Failed to fetch {url}: {str(e)}"


def search_and_read(query: str, num_results: int = 3) -> str:
    """
    Search Google AND fetch content from top results.
    This is Seven's full web browsing capability.
    
    Args:
        query: Search query
        num_results: Number of results to fetch content from
        
    Returns:
        Search results with extracted content
    """
    if not query or not query.strip():
        return "[ERROR] No search query provided"
    
    try:
        print(f"[SEARCH+READ] Searching and reading: {query}")
        urls = list(search(query, num_results=num_results))
        
        if not urls:
            return f"No results found for '{query}'"
        
        output = [f"[SEARCH+READ] Results for '{query}':\n"]
        
        for i, url in enumerate(urls, 1):
            output.append(f"--- Result {i}: {url} ---")
            content = fetch_webpage_content(url, max_chars=1000)
            output.append(content)
            output.append("")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"[ERROR] Search+read error: {str(e)}"


def extract_search_query(text: str) -> Optional[str]:
    """Extract search query from natural language"""
    text_lower = text.lower().strip()
    
    # Look for search keywords
    triggers = ["search for", "google", "look up", "find", "search about", "research"]
    
    for trigger in triggers:
        if trigger in text_lower:
            # Extract everything after the trigger
            parts = text_lower.split(trigger, 1)
            if len(parts) > 1:
                query = parts[1].strip()
                # Clean up
                query = query.replace("?", "").replace("!", "").strip()
                return query if query else None
    
    return None


def extract_url(text: str) -> Optional[str]:
    """Extract URL from text for direct page reading"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(url_pattern, text)
    return match.group(0) if match else None
