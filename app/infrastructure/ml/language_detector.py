"""Simple programming language detector."""
import re
from typing import Dict, Optional

class LanguageDetector:
    """Detects programming language from source code."""

    # Language keywords and patterns
    LANGUAGE_PATTERNS: Dict[str, list] = {
        "java": [
            r"public\s+class\s+\w+",
            r"import\s+java\.",
            r"@Override",
            r"System\.(out|in|err)",
            r"String\s+\w+\s*=",
        ],
        "c": [
            r"#include\s*<.*\.h>",
            r"printf\s*\(",
            r"scanf\s*\(",
            r"int\s+main\s*\(",
        ],
        "cpp": [
            r"#include\s*<.*>",
            r"std::",
            r"cout\s*<<",
            r"cin\s*>>",
            r"namespace\s+\w+",
            r"template\s*<",
        ],
        "python": [
            r"def\s+\w+\s*\(",
            r"import\s+\w+",
            r"from\s+\w+\s+import",
            r"if\s+__name__\s*==",
            r"print\s*\(",
        ],
        "javascript": [
            r"function\s+\w+\s*\(",
            r"const\s+\w+\s*=",
            r"let\s+\w+\s*=",
            r"console\.(log|error|warn)",
        ],
        "php": [
            r"<\?php",
            r"\$\w+\s*=",
            r"echo\s+",
        ],
        "ruby": [
            r"def\s+\w+\s*\(",
            r"require\s+['\"]",
            r"puts\s+",
        ],
        "go": [
            r"package\s+\w+",
            r"func\s+\w+\s*\(",
            r"import\s+\(",
        ],
    }

    @classmethod
    def detect(cls, code: str) -> str:
        """Detect the programming language of the code."""
        if not code or not isinstance(code, str):
            return "unknown"

        # Score each language
        scores: Dict[str, int] = {lang: 0 for lang in cls.LANGUAGE_PATTERNS.keys()}

        for lang, patterns in cls.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, code, re.MULTILINE):
                    scores[lang] += 1

        # Get the language with the highest score
        max_score = max(scores.values())
        if max_score == 0:
            return "unknown"

        # Return the first language with max score
        for lang, score in scores.items():
            if score == max_score:
                return lang

        return "unknown"

    @classmethod
    def normalize_language(cls, lang: Optional[str]) -> str:
        """Normalize language name to our standard set."""
        if not lang or not isinstance(lang, str):
            return "unknown"

        lang_lower = lang.lower().strip()
        # Map common variations
        if "c++" in lang_lower or "cxx" in lang_lower or "cpp" in lang_lower:
            return "cpp"
        if "java" in lang_lower:
            return "java"
        if "python" in lang_lower or "py" == lang_lower:
            return "python"
        if "javascript" in lang_lower or "js" == lang_lower:
            return "javascript"
        if "php" in lang_lower:
            return "php"
        if "ruby" in lang_lower or "rb" == lang_lower:
            return "ruby"
        if "go" in lang_lower or "golang" in lang_lower:
            return "go"
        if "c" == lang_lower:
            return "c"

        # If we don't recognize it, try to detect it anyway
        return "unknown"
