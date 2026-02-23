"""
Text Summarizer — Seven AI

Summarize long text, documents, or conversation history
using Ollama LLM. Supports different summary styles.
"""

import logging
from typing import Optional, Dict

logger = logging.getLogger("TextSummarizer")


class TextSummarizer:
    """Summarize text using Ollama LLM"""

    def __init__(self, ollama=None):
        self.ollama = ollama
        self.available = ollama is not None
        if self.available:
            logger.info("[OK] Text summarizer ready (via Ollama)")
        else:
            logger.info("[INFO] Text summarizer unavailable — needs Ollama")

    def summarize(self, text: str, style: str = "concise",
                  max_words: int = 100) -> Dict:
        """
        Summarize text.

        Args:
            text: Text to summarize
            style: 'concise', 'detailed', 'bullet', 'eli5'
            max_words: Approximate max words for summary

        Returns:
            Dict with 'summary', 'original_length', 'summary_length'
        """
        if not self.ollama:
            return {'success': False, 'message': 'Ollama not available'}

        if len(text.strip()) < 50:
            return {'success': False, 'message': 'Text too short to summarize'}

        style_instructions = {
            'concise': f"Provide a concise summary in {max_words} words or fewer.",
            'detailed': f"Provide a detailed summary covering all main points, in about {max_words} words.",
            'bullet': f"Summarize as bullet points (max {max_words} words total).",
            'eli5': f"Explain this like I'm 5 years old, in about {max_words} words.",
        }

        instruction = style_instructions.get(style, style_instructions['concise'])

        prompt = f"""{instruction}

Text to summarize:
{text[:8000]}"""

        system = (
            "You are an expert summarizer. Produce clear, accurate summaries. "
            "Output ONLY the summary with no preamble or commentary."
        )

        try:
            summary = self.ollama.generate(
                prompt,
                system_message=system,
                temperature=0.3,
                max_tokens=max(max_words * 2, 200)
            )

            if summary:
                return {
                    'success': True,
                    'summary': summary.strip(),
                    'style': style,
                    'original_length': len(text),
                    'summary_length': len(summary.strip()),
                    'compression_ratio': round(len(summary.strip()) / max(len(text), 1), 2),
                }
            return {'success': False, 'message': 'Empty summary returned'}

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return {'success': False, 'message': f'Summarization error: {e}'}

    def summarize_file(self, filepath: str, style: str = "concise") -> Dict:
        """Summarize a text file"""
        try:
            from pathlib import Path
            path = Path(filepath)
            if not path.exists():
                return {'success': False, 'message': f'File not found: {filepath}'}
            if path.stat().st_size > 500_000:
                return {'success': False, 'message': 'File too large (>500KB)'}
            text = path.read_text(encoding='utf-8')
            result = self.summarize(text, style=style)
            result['filepath'] = filepath
            return result
        except Exception as e:
            return {'success': False, 'message': f'File read error: {e}'}
