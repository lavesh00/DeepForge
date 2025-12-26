"""Request Validator."""

from typing import Optional


class RequestValidator:
    """Validates API requests."""
    
    def __init__(self, max_prompt_length: int = 10000, max_tokens: int = 4096):
        """
        Initialize validator.
        
        Args:
            max_prompt_length: Maximum prompt length
            max_tokens: Maximum tokens
        """
        self.max_prompt_length = max_prompt_length
        self.max_tokens = max_tokens
    
    def validate_prompt(self, prompt: str, max_tokens: int) -> bool:
        """
        Validate prompt.
        
        Args:
            prompt: Prompt text
            max_tokens: Requested max tokens
            
        Returns:
            True if valid
        """
        if len(prompt) > self.max_prompt_length:
            return False
        
        if max_tokens > self.max_tokens:
            return False
        
        return True



