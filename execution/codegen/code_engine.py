"""
Code Engine
AI-driven code generation.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from core.registry import get_service
from model_runtime.serving.local_api import LocalModelAPI
from model_runtime.serving.router import ModelRouter


class CodeEngine:
    """Generates code using AI models."""
    
    def __init__(self, model_api=None):
        """
        Initialize code engine.
        
        Args:
            model_api: Model API instance (auto-detect if None)
        """
        if model_api is None:
            model_api = self._get_model_api()
        self.model_api = model_api
    
    def _get_model_api(self):
        """Get model API from registry or create new."""
        try:
            model_manager = get_service("model_manager")
            if model_manager:
                router = ModelRouter(model_manager=model_manager)
                return LocalModelAPI(router)
        except Exception:
            pass
        return None
    
    def generate_code(
        self,
        prompt: str,
        context: Dict[str, Any] = None,
        language: str = "python"
    ) -> str:
        """
        Generate code from prompt.
        
        Args:
            prompt: Code generation prompt
            context: Additional context
            language: Target language
            
        Returns:
            Generated code
        """
        if context is None:
            context = {}
        
        full_prompt = self._build_prompt(prompt, context, language)
        
        if self.model_api:
            try:
                # Get default model from config
                from core.config import load_config
                config = load_config()
                model_config = config.get_section("models")
                default_model = model_config.get("default_model", "deepseek-coder")
                
                response = self.model_api.chat_completion(
                    model=default_model,
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=2048,
                )
                code = response["choices"][0]["message"]["content"]
                if code and code.strip():
                    return code
            except Exception as e:
                # Log error but continue to fallback
                import logging
                logging.getLogger("deepforge.codegen").warning(f"Model generation failed: {e}")
                pass
        
        return self._generate_placeholder_code(prompt, language)
    
    def _generate_placeholder_code(self, prompt: str, language: str) -> str:
        """Generate placeholder code when model is not available."""
        if language == "python":
            return f'''# Generated code for: {prompt}

def main():
    """Main function."""
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
        elif language == "javascript":
            return f'''// Generated code for: {prompt}

function main() {{
    console.log("Hello, World!");
}}

main();
'''
        else:
            return f"# Generated {language} code\n# {prompt}\n"
    
    def _build_prompt(
        self,
        prompt: str,
        context: Dict[str, Any],
        language: str
    ) -> str:
        """Build full prompt with context."""
        full_prompt = f"Generate {language} code for: {prompt}\n\n"
        
        if context.get("existing_code"):
            full_prompt += f"Existing code:\n{context['existing_code']}\n\n"
        
        if context.get("requirements"):
            full_prompt += f"Requirements:\n{context['requirements']}\n\n"
        
        if context.get("mission_description"):
            full_prompt += f"Mission context: {context['mission_description']}\n\n"
        
        full_prompt += f"Return only valid {language} code, no explanations."
        
        return full_prompt
    
    def polish_template(self, template_code: str, mission_desc: str) -> str:
        """
        Polish template code using DeepSeek.
        
        Args:
            template_code: Template code to polish
            mission_desc: Mission description for context
            
        Returns:
            Polished code
        """
        if not self.model_api:
            return template_code
        
        prompt = f"""Polish this template code for mission '{mission_desc}':

{template_code[:2000]}

Output only improved, production-ready code. Keep the same structure but enhance:
- Add proper error handling
- Improve code quality
- Add docstrings
- Optimize where possible
"""
        
        try:
            response = self.model_api.chat_completion(
                model="deepseek-coder",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
            )
            polished = response["choices"][0]["message"]["content"]
            
            # Extract code block if present
            if "```" in polished:
                code_block = polished.split("```")[1]
                if "\n" in code_block:
                    code_block = code_block.split("\n", 1)[1]
                polished = code_block.split("```")[0] if "```" in code_block else code_block
            
            return polished.strip() if polished.strip() else template_code
        except Exception:
            return template_code

