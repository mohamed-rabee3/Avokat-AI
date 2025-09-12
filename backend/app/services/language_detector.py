"""
Language Detection Service
Minimal utility to detect document language for multilingual KG support
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Simple language detector for Arabic and English content"""
    
    def __init__(self):
        # Arabic Unicode ranges
        self.arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        self.english_pattern = re.compile(r'[a-zA-Z]')
    
    def detect_language(self, text: str) -> str:
        """
        Detect the primary language of the text
        Returns: 'arabic', 'english', or 'mixed'
        """
        if not text or not text.strip():
            return 'english'  # Default to English
        
        # Count Arabic and English characters
        arabic_chars = len(self.arabic_pattern.findall(text))
        english_chars = len(self.english_pattern.findall(text))
        total_chars = arabic_chars + english_chars
        
        if total_chars == 0:
            return 'english'  # Default to English
        
        arabic_ratio = arabic_chars / total_chars
        english_ratio = english_chars / total_chars
        
        # Determine primary language
        if arabic_ratio > 0.3:  # More than 30% Arabic characters
            if english_ratio > 0.2:  # Also significant English
                return 'mixed'
            else:
                return 'arabic'
        elif english_ratio > 0.5:  # More than 50% English characters
            return 'english'
        else:
            return 'mixed'
    
    def get_language_specific_prompt(self, language: str, base_prompt: str) -> str:
        """
        Enhance the base prompt with language-specific instructions
        """
        if language == 'arabic':
            return f"""
{base_prompt}

IMPORTANT: This text is in Arabic. Please:
- Extract entities and relationships in Arabic
- Preserve Arabic names, terms, and legal concepts exactly as they appear
- Use Arabic legal terminology appropriately
- Maintain cultural and linguistic context
"""
        elif language == 'mixed':
            return f"""
{base_prompt}

IMPORTANT: This text contains both Arabic and English content. Please:
- Extract entities and relationships in their original language
- Preserve Arabic names, terms, and legal concepts exactly as they appear
- Preserve English terms exactly as they appear
- Maintain both cultural and linguistic contexts
"""
        else:  # English (default)
            return base_prompt


# Global instance
language_detector = LanguageDetector()
