"""
Document Reader - Seven Can Read PDFs and Documents

Extracts text from PDF, DOCX, TXT, CSV, JSON and summarizes via Ollama.

Requires: PyPDF2
"""

import logging
import json
import csv
import io
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger("DocumentReader")

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 not installed — PDF reading unavailable. pip install PyPDF2")


class DocumentReader:
    """
    Seven reads documents.
    
    - PDF extraction via PyPDF2
    - TXT, CSV, JSON, MD, LOG, XML, HTML
    - Summarization through Ollama
    - Page-by-page or full extraction
    """
    
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.txt', '.md', '.csv', '.json', '.log',
        '.xml', '.html', '.htm', '.py', '.cs', '.vb',
        '.js', '.ts', '.css', '.yaml', '.yml', '.ini',
        '.cfg', '.conf', '.bat', '.ps1', '.sh',
    }
    
    def __init__(self, bot_instance=None):
        self.bot = bot_instance
        self.logger = logging.getLogger("DocumentReader")
        self.logger.info(f"[OK] Document reader ready (PDF: {PYPDF2_AVAILABLE})")
    
    def can_read(self, filepath: str) -> bool:
        """Check if we can read this file type"""
        ext = Path(filepath).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    def read_document(self, filepath: str, max_chars: int = 10000) -> Dict:
        """
        Read a document and extract text.
        
        Returns:
            Dict with 'success', 'text', 'pages', 'type'
        """
        path = Path(filepath)
        
        if not path.exists():
            return {'success': False, 'message': f'File not found: {filepath}'}
        
        ext = path.suffix.lower()
        
        try:
            if ext == '.pdf':
                return self._read_pdf(path, max_chars)
            elif ext == '.csv':
                return self._read_csv(path, max_chars)
            elif ext == '.json':
                return self._read_json(path, max_chars)
            elif ext in self.SUPPORTED_EXTENSIONS:
                return self._read_text(path, max_chars)
            else:
                return {'success': False, 'message': f'Unsupported file type: {ext}'}
        except Exception as e:
            return {'success': False, 'message': f'Error reading {filepath}: {str(e)[:200]}'}
    
    def summarize_document(self, filepath: str) -> str:
        """Read and summarize a document through Ollama"""
        result = self.read_document(filepath, max_chars=8000)
        if not result['success']:
            return result['message']
        
        text = result['text']
        filename = Path(filepath).name
        
        ollama = getattr(self.bot, 'ollama', None) if self.bot else None
        if not ollama:
            # Return raw text if no Ollama
            return f"Contents of {filename} ({len(text)} chars):\n\n{text[:3000]}"
        
        try:
            summary = ollama.generate(
                f"Summarize this document concisely. Include key points, important details, and any action items:\n\n{text[:6000]}",
                system_message="You are a document analyst. Provide clear, structured summaries. Be thorough but concise.",
                temperature=0.3,
                max_tokens=500
            )
            
            pages = result.get('pages', 'unknown')
            return f"Summary of {filename} ({pages} pages):\n\n{summary}"
        except Exception as e:
            return f"Read {filename} but couldn't summarize: {str(e)[:200]}\n\nRaw text:\n{text[:2000]}"
    
    # ============ READERS ============
    
    def _read_pdf(self, path: Path, max_chars: int) -> Dict:
        """Extract text from PDF"""
        if not PYPDF2_AVAILABLE:
            return {'success': False, 'message': 'PyPDF2 not installed. pip install PyPDF2'}
        
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            pages = len(reader.pages)
            
            text_parts = []
            total_chars = 0
            
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ''
                text_parts.append(f"--- Page {i+1} ---\n{page_text}")
                total_chars += len(page_text)
                
                if total_chars >= max_chars:
                    text_parts.append(f"\n... (truncated at page {i+1}/{pages})")
                    break
            
            text = '\n\n'.join(text_parts)
            
            return {
                'success': True,
                'text': text[:max_chars],
                'pages': pages,
                'type': 'pdf',
                'total_chars': total_chars,
            }
    
    def _read_text(self, path: Path, max_chars: int) -> Dict:
        """Read plain text files"""
        content = path.read_text(encoding='utf-8', errors='replace')
        truncated = len(content) > max_chars
        
        return {
            'success': True,
            'text': content[:max_chars] + ('...(truncated)' if truncated else ''),
            'pages': 1,
            'type': path.suffix.lstrip('.'),
            'total_chars': len(content),
        }
    
    def _read_csv(self, path: Path, max_chars: int) -> Dict:
        """Read CSV files"""
        content = path.read_text(encoding='utf-8', errors='replace')
        reader = csv.reader(io.StringIO(content))
        
        rows = []
        for i, row in enumerate(reader):
            rows.append(' | '.join(row))
            if i > 100:
                rows.append(f'... (showing first 100 of more rows)')
                break
        
        text = '\n'.join(rows)
        return {
            'success': True,
            'text': text[:max_chars],
            'pages': 1,
            'type': 'csv',
            'rows': len(rows),
        }
    
    def _read_json(self, path: Path, max_chars: int) -> Dict:
        """Read JSON files"""
        content = path.read_text(encoding='utf-8', errors='replace')
        try:
            data = json.loads(content)
            formatted = json.dumps(data, indent=2)
        except Exception:
            formatted = content
        
        return {
            'success': True,
            'text': formatted[:max_chars],
            'pages': 1,
            'type': 'json',
            'total_chars': len(formatted),
        }
