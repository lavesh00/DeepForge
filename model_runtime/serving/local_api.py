"""
Local Model API
OpenAI-compatible local API endpoint.
"""

from typing import Dict, Any, Optional, List
from .router import ModelRouter
from .request_validator import RequestValidator


class LocalModelAPI:
    """OpenAI-compatible local API."""
    
    def __init__(self, router: ModelRouter):
        """
        Initialize local API.
        
        Args:
            router: Model router instance
        """
        self.router = router
        self.validator = RequestValidator()
    
    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion.
        
        Args:
            model: Model identifier
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            Completion response
        """
        prompt = self._messages_to_prompt(messages)
        
        if not self.validator.validate_prompt(prompt, max_tokens):
            raise ValueError("Invalid prompt or token limit exceeded")
        
        try:
            adapter = self.router.get_adapter(model, model_path=None)
            
            response_text = adapter.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get("top_p", 0.9),
                stop_sequences=kwargs.get("stop", []),
            )
        except Exception as e:
            # Return placeholder instead of raising - let caller handle fallback
            return {
                "id": f"chatcmpl-{hash(prompt)}",
                "object": "chat.completion",
                "created": 0,
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"# Placeholder response - model not available: {str(e)}",
                    },
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": 0,
                    "total_tokens": len(prompt.split()),
                },
            }
        
        return {
            "id": f"chatcmpl-{hash(prompt)}",
            "object": "chat.completion",
            "created": 0,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(prompt.split()) + len(response_text.split()),
            },
        }
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert message list to prompt string."""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n".join(prompt_parts) + "\nAssistant:"

