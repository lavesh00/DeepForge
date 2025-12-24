"""
Transformers Adapter
Uses HuggingFace transformers for model inference.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path


class TransformersAdapter:
    """Adapter for transformers models."""
    
    def __init__(self, model_path: Optional[Path] = None, model_name: Optional[str] = None):
        """
        Initialize transformers adapter.
        
        Args:
            model_path: Path to model files
            model_name: HuggingFace model name
        """
        self.model_path = model_path
        self.model_name = model_name or "gpt2"
        self._model = None
        self._tokenizer = None
    
    def load(self):
        """Load the model."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            if self.model_path and self.model_path.exists():
                model_path = str(self.model_path)
            else:
                model_path = self.model_name
            
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)
            self._model = AutoModelForCausalLM.from_pretrained(model_path)
            
            # Set pad_token properly - use unk_token or create a new one, not eos_token
            if self._tokenizer.pad_token is None:
                if self._tokenizer.unk_token is not None:
                    self._tokenizer.pad_token = self._tokenizer.unk_token
                else:
                    # Add a new pad token
                    self._tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                    self._model.resize_token_embeddings(len(self._tokenizer))
                
        except ImportError:
            raise ImportError("transformers library not installed. Install with: pip install transformers torch")
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: List[str] = None
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop_sequences: Stop sequences
            
        Returns:
            Generated text
        """
        if self._model is None or self._tokenizer is None:
            self.load()
        
        try:
            import torch
            
            # Encode with return_attention_mask
            encoded = self._tokenizer(prompt, return_tensors="pt", return_attention_mask=True)
            input_ids = encoded["input_ids"]
            attention_mask = encoded["attention_mask"]
            
            # Move to device if model is on GPU
            device = next(self._model.parameters()).device if hasattr(self._model, 'parameters') else "cpu"
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            
            with torch.no_grad():
                outputs = self._model.generate(
                    input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=temperature > 0,
                    pad_token_id=self._tokenizer.pad_token_id,
                    eos_token_id=self._tokenizer.eos_token_id,
                )
            
            generated = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Remove the prompt from the generated text
            if generated.startswith(prompt):
                generated = generated[len(prompt):].strip()
            
            if stop_sequences:
                for stop in stop_sequences:
                    if stop in generated:
                        generated = generated.split(stop)[0]
            
            return generated.strip()
            
        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")

