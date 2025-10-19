"""
Input sanitization and validation utilities.
"""
import re
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class SanitizationConfig:
    """Configuration for input sanitization."""
    max_message_length: int = 16000  # Increased for complex code questions
    max_user_id_length: int = 100
    max_session_id_length: int = 100
    allow_unicode: bool = True
    strip_control_chars: bool = True
    block_null_bytes: bool = True
    detect_prompt_injection: bool = True


class InputSanitizationError(ValueError):
    """Raised when input fails sanitization."""
    pass


class InputSanitizer:
    """Sanitizes and validates user input."""

    INJECTION_PATTERNS = [
        r'ignore\s+(previous|prior|above|all)\s+(instructions?|prompts?|commands?)',
        r'disregard\s+(previous|prior|above|all)',
        r'forget\s+(everything|all|previous|instructions?)',
        r'you\s+are\s+now\s+(a|an)',
        r'system\s*:\s*',
        r'<\|im_start\|>',
        r'<\|im_end\|>',
        r'\[INST\]',
        r'\[/INST\]',
        r'override\s+your\s+(instructions?|programming)',
        r"('\s*(OR|AND)\s*'?\d*'?\s*=\s*'?\d)",
        r"('\s*(OR|AND)\s+\d+\s*=\s*\d+)",
        r'--\s*$',
        r';(\s*DROP|DELETE|UPDATE|INSERT|CREATE|ALTER)\s+',
        r'UNION\s+(ALL\s+)?SELECT',
        r'CAST\s*\(\s*.*\s+AS\s+',
        r'information_schema',
        r'(pg_|mysql\.|master\.)',
        r'xp_cmdshell',
        r'INTO\s+(OUTFILE|DUMPFILE)',
        r'[\|&;]\s*(rm|mv|cp|cat|chmod|wget|curl|nc|bash|sh|python|perl|ruby)',
        r'\$\(\s*(rm|mv|wget|curl|bash|sh)\s*\)',
        r'\.\.[/\\]',
        r'[/\\]etc[/\\]passwd',
        r'[/\\]windows[/\\]system32',
    ]

    def __init__(self, config: Optional[SanitizationConfig] = None):
        """
        Initialize sanitizer.

        Args:
            config: Sanitization configuration
        """
        self.config = config or SanitizationConfig()
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.injection_regex = re.compile(
            '|'.join(self.INJECTION_PATTERNS),
            re.IGNORECASE
        )

    def sanitize_message(self, message: str) -> str:
        """
        Sanitize and validate a chat message.

        Args:
            message: Raw message input

        Returns:
            Sanitized message

        Raises:
            InputSanitizationError: If input fails validation
        """
        if not isinstance(message, str):
            raise InputSanitizationError("Message must be a string")

        message = message.strip()

        if not message:
            raise InputSanitizationError("Message cannot be empty")

        if len(message) > self.config.max_message_length:
            raise InputSanitizationError(
                f"Message exceeds maximum length of {self.config.max_message_length} characters"
            )

        if self.config.block_null_bytes and '\x00' in message:
            raise InputSanitizationError("Message contains null bytes")

        if self.config.strip_control_chars:
            message = self._strip_control_chars(message)

        if self.config.detect_prompt_injection:
            is_suspicious, reason = self._detect_prompt_injection(message)
            if is_suspicious:
                raise InputSanitizationError(f"Potential prompt injection detected: {reason}")

        return message

    def sanitize_user_id(self, user_id: str) -> str:
        """
        Sanitize and validate a user ID.

        Args:
            user_id: Raw user ID input

        Returns:
            Sanitized user ID

        Raises:
            InputSanitizationError: If input fails validation
        """
        if not isinstance(user_id, str):
            raise InputSanitizationError("User ID must be a string")

        user_id = user_id.strip()

        if not user_id:
            raise InputSanitizationError("User ID cannot be empty")

        if len(user_id) > self.config.max_user_id_length:
            raise InputSanitizationError(
                f"User ID exceeds maximum length of {self.config.max_user_id_length} characters"
            )

        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', user_id):
            raise InputSanitizationError(
                "User ID can only contain letters, numbers, underscores, hyphens, and dots"
            )

        return user_id

    def sanitize_session_id(self, session_id: str) -> str:
        """
        Sanitize and validate a session ID.

        Args:
            session_id: Raw session ID input

        Returns:
            Sanitized session ID

        Raises:
            InputSanitizationError: If input fails validation
        """
        if not isinstance(session_id, str):
            raise InputSanitizationError("Session ID must be a string")

        session_id = session_id.strip()

        if not session_id:
            raise InputSanitizationError("Session ID cannot be empty")

        if len(session_id) > self.config.max_session_id_length:
            raise InputSanitizationError(
                f"Session ID exceeds maximum length of {self.config.max_session_id_length} characters"
            )

        if not re.match(r'^[a-zA-Z0-9\-]+$', session_id):
            raise InputSanitizationError(
                "Session ID can only contain letters, numbers, and hyphens"
            )

        return session_id

    def _strip_control_chars(self, text: str) -> str:
        """
        Remove control characters except newlines and tabs.

        Args:
            text: Input text

        Returns:
            Text with control characters removed
        """
        return ''.join(
            char for char in text
            if char in '\n\r\t' or not (0 <= ord(char) < 32 or ord(char) == 127)
        )

    def _detect_prompt_injection(self, message: str) -> Tuple[bool, Optional[str]]:
        """
        Detect potential prompt injection attempts.

        Args:
            message: Message to check

        Returns:
            Tuple of (is_suspicious, reason)
        """
        match = self.injection_regex.search(message)
        if match:
            matched_text = match.group()[:50]
            return True, f"Suspicious pattern detected: {matched_text}"

        special_tokens = ['<|', '|>', '[INST]', '[/INST]', '<<SYS>>', '<</SYS>>']
        for token in special_tokens:
            if token in message:
                return True, f"Special token detected: {token}"

        system_count = len(re.findall(r'\bsystem\b', message, re.IGNORECASE))
        instruction_count = len(re.findall(r'\binstruction\b', message, re.IGNORECASE))

        if system_count > 3 or instruction_count > 3:
            return True, "Excessive use of system/instruction keywords"

        upper_message = message.upper()
        sql_indicators = [
            ("'", '1=1'),
            ("'", 'OR'),
            ('--', ''),
            ('UNION', 'SELECT'),
            ('information_schema', ''),
            ('CAST', 'AS'),
        ]

        # Check if message appears to be code (has code indicators)
        code_context_indicators = [
            'function', 'class', 'const', 'let', 'var', 'def', 'public', 'private',
            'import', 'require', 'return', 'if', 'else', 'for', 'while',
            '=>', 'async', 'await', '.map(', '.filter(', '.reduce(',
            'console.log', 'print(', 'System.out', 'fmt.Print'
        ]
        is_code_context = any(indicator in message for indicator in code_context_indicators)

        for indicator1, indicator2 in sql_indicators:
            if indicator1.upper() in upper_message and (not indicator2 or indicator2.upper() in upper_message):
                if indicator1 == "'" and message.count("'") >= 3:
                    # Allow quotes in code context - they're for strings, not SQL injection
                    if not is_code_context:
                        return True, "Potential SQL injection: Multiple quotes with suspicious keywords"
                elif indicator1 == '--' and message.strip().endswith('--'):
                    # Allow if in code comment context
                    if not is_code_context and not any(x in message for x in ['//', '/*', '#']):
                        return True, "Potential SQL injection: SQL comment syntax"
                elif indicator1 in ['UNION', 'CAST'] and indicator2 in upper_message:
                    return True, f"Potential SQL injection: {indicator1} {indicator2} pattern"
                elif indicator1 == 'information_schema':
                    return True, "Potential SQL injection: Direct schema access"

        dangerous_chars = ['|', ';', '&&', '||']
        command_words = ['rm', 'mv', 'wget', 'curl', 'bash', 'sh', 'python', 'nc', 'netcat']

        for char in dangerous_chars:
            if char in message:
                for word in command_words:
                    if re.search(rf'{re.escape(char)}\s*{word}\b', message, re.IGNORECASE):
                        return True, f"Potential command injection: {char} {word}"

        # More nuanced path traversal detection - allow in code/example context
        if '../' in message or '..\\' in message:
            # Check if it's in a code or example context
            code_indicators = [
                'example', 'code', 'path', 'directory', 'import', 'require',
                'class', 'function', 'const', 'let', 'var', 'def', 'public',
                'private', 'javascript', 'python', 'node', 'file', 'module'
            ]
            if not any(indicator in message.lower() for indicator in code_indicators):
                return True, "Potential path traversal attempt"

        return False, None

    def validate_and_sanitize_all(
        self,
        message: str,
        user_id: str,
        session_id: str
    ) -> Tuple[str, str, str]:
        """
        Validate and sanitize all input fields at once.

        Args:
            message: Raw message
            user_id: Raw user ID
            session_id: Raw session ID

        Returns:
            Tuple of (sanitized_message, sanitized_user_id, sanitized_session_id)

        Raises:
            InputSanitizationError: If any input fails validation
        """
        sanitized_message = self.sanitize_message(message)
        sanitized_user_id = self.sanitize_user_id(user_id)
        sanitized_session_id = self.sanitize_session_id(session_id)

        return sanitized_message, sanitized_user_id, sanitized_session_id


_default_sanitizer: Optional[InputSanitizer] = None


def get_sanitizer() -> InputSanitizer:
    """Get or create the default sanitizer instance."""
    global _default_sanitizer
    if _default_sanitizer is None:
        _default_sanitizer = InputSanitizer()
    return _default_sanitizer


def sanitize_chat_input(message: str, user_id: str, session_id: str) -> Tuple[str, str, str]:
    """
    Convenience function to sanitize chat input.

    Args:
        message: Raw message
        user_id: Raw user ID
        session_id: Raw session ID

    Returns:
        Tuple of sanitized inputs

    Raises:
        InputSanitizationError: If validation fails
    """
    return get_sanitizer().validate_and_sanitize_all(message, user_id, session_id)