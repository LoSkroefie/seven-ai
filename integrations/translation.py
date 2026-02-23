"""
Multi-Language Translation — Seven AI

Translate text between languages using Ollama's LLM capabilities.
No external API needed — uses the same model Seven already runs.
"""

import logging
from typing import Optional, Dict

logger = logging.getLogger("Translation")

# Common language codes and names
LANGUAGES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'nl': 'Dutch', 'ru': 'Russian',
    'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'ar': 'Arabic',
    'hi': 'Hindi', 'af': 'Afrikaans', 'sw': 'Swahili', 'pl': 'Polish',
    'tr': 'Turkish', 'sv': 'Swedish', 'da': 'Danish', 'no': 'Norwegian',
    'fi': 'Finnish', 'el': 'Greek', 'he': 'Hebrew', 'th': 'Thai',
    'vi': 'Vietnamese', 'id': 'Indonesian', 'ms': 'Malay', 'tl': 'Filipino',
    'uk': 'Ukrainian', 'cs': 'Czech', 'ro': 'Romanian', 'hu': 'Hungarian',
}


class TranslationEngine:
    """Translate text using Ollama LLM"""

    def __init__(self, ollama=None):
        self.ollama = ollama
        self.available = ollama is not None
        if self.available:
            logger.info("[OK] Translation engine ready (via Ollama)")
        else:
            logger.info("[INFO] Translation unavailable — needs Ollama")

    def translate(self, text: str, target_lang: str,
                  source_lang: str = "auto") -> Dict:
        """
        Translate text to target language.

        Args:
            text: Text to translate
            target_lang: Target language (code or name)
            source_lang: Source language (code, name, or "auto")

        Returns:
            Dict with 'translation', 'source_lang', 'target_lang'
        """
        if not self.ollama:
            return {'success': False, 'message': 'Ollama not available'}

        # Resolve language names
        target_name = self._resolve_language(target_lang)
        source_name = self._resolve_language(source_lang) if source_lang != "auto" else "auto-detected"

        prompt = f"""Translate the following text to {target_name}.
Rules:
- Output ONLY the translation, nothing else
- Preserve the original tone and meaning
- If the text is already in {target_name}, return it as-is

Text to translate:
{text}"""

        system = (
            "You are an expert translator. Translate accurately and naturally. "
            "Output ONLY the translated text with no explanation or commentary."
        )

        try:
            translation = self.ollama.generate(
                prompt, system_message=system,
                temperature=0.2, max_tokens=500
            )

            if translation:
                return {
                    'success': True,
                    'translation': translation.strip(),
                    'source_lang': source_name,
                    'target_lang': target_name,
                    'original': text,
                }
            return {'success': False, 'message': 'Empty translation'}

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {'success': False, 'message': f'Translation error: {e}'}

    def detect_language(self, text: str) -> Optional[str]:
        """Detect the language of input text"""
        if not self.ollama:
            return None

        prompt = f"""What language is this text written in? 
Reply with ONLY the language name (e.g. "English", "Spanish", "French").

Text: {text[:200]}"""

        try:
            result = self.ollama.generate(
                prompt,
                system_message="Identify the language. Reply with ONLY the language name.",
                temperature=0.1, max_tokens=20
            )
            return result.strip() if result else None
        except Exception:
            return None

    def list_languages(self) -> str:
        """List available languages"""
        lines = ["Available languages:"]
        for code, name in sorted(LANGUAGES.items(), key=lambda x: x[1]):
            lines.append(f"  {code} — {name}")
        return "\n".join(lines)

    def _resolve_language(self, lang: str) -> str:
        """Resolve a language code or name to full name"""
        lang_lower = lang.lower().strip()
        if lang_lower in LANGUAGES:
            return LANGUAGES[lang_lower]
        # Check if it's already a name
        for code, name in LANGUAGES.items():
            if lang_lower == name.lower():
                return name
        # Return as-is
        return lang
