"""
Internationalization (i18n) module for OPC UA Certificate Manager.

This module provides translation support for the application UI.

Usage:
    from src.utils.i18n import Translator
    
    _ = Translator("en")
    title = _("app.title")
    
    # Or with dynamic language:
    from src.utils.config import load_config
    config = load_config()
    lang = config.get("language", "en")
    _ = Translator(lang)
"""

import json
from pathlib import Path
from typing import Optional


class Translator:
    """
    Translation manager for the application.
    
    Loads translation files from locales/ folder and provides
    dot-notation access to translation strings.
    """
    
    def __init__(self, lang_code: str = "en") -> None:
        """
        Initialize translator with specified language.
        
        Args:
            lang_code: Language code (e.g., "en", "es").
        """
        self.lang_code = lang_code
        self.translations: dict = {}
        self.fallback_translations: dict = {}
        self._load_translations(lang_code)
    
    def _load_translations(self, lang_code: str) -> None:
        """
        Load translation files for specified language.
        
        Args:
            lang_code: Language code to load.
        """
        locales_dir = Path(__file__).parent.parent / "locales"
        
        # Load fallback (English) first
        fallback_path = locales_dir / "en.json"
        if fallback_path.exists():
            with open(fallback_path, "r", encoding="utf-8") as f:
                self.fallback_translations = json.load(f)
        
        # Load requested language
        translation_path = locales_dir / f"{lang_code}.json"
        if translation_path.exists():
            with open(translation_path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        else:
            # Fallback to English if requested language not found
            self.translations = self.fallback_translations.copy()
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get translation by dot-notation key.
        
        Args:
            key: Dot-notation key (e.g., "app.menu.files").
            default: Default value if key not found.
        
        Returns:
            Translated string or key/default if not found.
        """
        keys = key.split(".")
        value = self.translations
        
        # Try to find in primary language
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # Try fallback
                value = self.fallback_translations
                for fk in keys:
                    if isinstance(value, dict) and fk in value:
                        value = value[fk]
                    else:
                        return default or key
                return value
        
        return value if isinstance(value, str) else (default or key)
    
    def _(self, key: str, default: Optional[str] = None) -> str:
        """
        Shorthand for get() method.
        
        Args:
            key: Dot-notation key.
            default: Default value if key not found.
        
        Returns:
            Translated string.
        """
        return self.get(key, default)
    
    def set_language(self, lang_code: str) -> None:
        """
        Change the current language.
        
        Args:
            lang_code: New language code.
        """
        self.lang_code = lang_code
        self._load_translations(lang_code)
    
    def get_available_languages(self) -> list[dict]:
        """
        Get list of available languages.
        
        Returns:
            List of dicts with 'code' and 'name' keys.
        """
        locales_dir = Path(__file__).parent.parent / "locales"
        languages = []
        
        # Language metadata
        lang_names = {
            "en": "English",
            "es": "Españłłł",
            "de": "Deutsch",
            "fr": "Françłłais",
            "pt": "Portuguęś",
            "it": "Italiano",
        }
        
        if locales_dir.exists():
            for file in locales_dir.glob("*.json"):
                code = file.stem
                languages.append({
                    "code": code,
                    "name": lang_names.get(code, code.upper()),
                })
        
        return sorted(languages, key=lambda x: x["code"])


# Global translator instance (lazy initialization)
_translator: Optional[Translator] = None


def get_translator(lang_code: Optional[str] = None) -> Translator:
    """
    Get or create global translator instance.
    
    Args:
        lang_code: Language code (uses current config if not specified).
    
    Returns:
        Translator instance.
    """
    global _translator
    
    if _translator is None:
        # Auto-detect language from config
        if lang_code is None:
            try:
                from src.utils.config import load_config
                config = load_config()
                lang_code = config.get("language", "en")
            except Exception:
                lang_code = "en"
        
        _translator = Translator(lang_code)
    
    if lang_code and lang_code != _translator.lang_code:
        _translator.set_language(lang_code)
    
    return _translator


def _(key: str, default: Optional[str] = None) -> str:
    """
    Shorthand function for translation.
    
    Usage:
        from src.utils.i18n import _
        
        title = _("app.title")
    
    Args:
        key: Dot-notation translation key.
        default: Default value if key not found.
    
    Returns:
        Translated string.
    """
    translator = get_translator()
    return translator._(key, default)


def set_language(lang_code: str) -> None:
    """
    Set global language for translations.
    
    Args:
        lang_code: Language code (e.g., "en", "es").
    """
    translator = get_translator()
    translator.set_language(lang_code)