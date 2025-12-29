"""Check which model is currently being used."""

from runtime.launcher import launch_system
from core.registry import get_service
from model_runtime.manager.model_manager import ModelManager

# Initialize system
launch_system(skip_bootstrap=True)

print("=" * 60)
print("  DEEPFORGE MODEL STATUS")
print("=" * 60)
print()

# Get model manager
model_manager = get_service("model_manager")

if not model_manager:
    print("ERROR: Model Manager not initialized!")
    exit(1)

# List registered models
registered_models = model_manager.list_models()
print(f"Registered Models: {len(registered_models)}")
if registered_models:
    for model_id in registered_models:
        model_info = model_manager.get_model(model_id)
        print(f"  - {model_id}")
        if model_info:
            print(f"    State: {model_info.state.value}")
            print(f"    Path: {model_info.model_path or 'Not set'}")
            print(f"    Memory: {model_info.memory_mb} MB")
else:
    print("  (none)")

print()
print("=" * 60)
print("  CURRENT CODE GENERATION METHOD")
print("=" * 60)
print()

# Check what CodeEngine is using
from execution.codegen.code_engine import CodeEngine

code_engine = CodeEngine()
if code_engine.model_api:
    print("Code Engine: Using Model API")
    print(f"  Router: {type(code_engine.model_api.router).__name__}")
    print(f"  Model Manager: {code_engine.model_api.router.model_manager is not None}")
else:
    print("Code Engine: Using PLACEHOLDER/TEMPLATE-BASED generation")
    print("  (No AI model is loaded or available)")

print()
print("=" * 60)
print("  CONCLUSION")
print("=" * 60)
print()

if not registered_models:
    print("NO MODELS REGISTERED")
    print("The system is using template-based code generation.")
    print("Different code is generated based on mission description keywords:")
    print("  - 'todo' -> TodoList class")
    print("  - 'api'/'rest' -> FastAPI endpoints")
    print("  - 'web'/'react' -> Web app backend")
    print()
    print("To use a real AI model:")
    print("  1. Install a model (e.g., from HuggingFace)")
    print("  2. Register it: deepforge models register <id> --path <path>")
    print("  3. The system will automatically use it")
elif registered_models and not any(
    model_manager.get_model(mid).model_path 
    for mid in registered_models 
    if model_manager.get_model(mid)
):
    print("MODELS REGISTERED BUT NOT CONFIGURED")
    print("Models are registered but no model paths are set.")
    print("The system falls back to template-based generation.")
else:
    print("MODELS AVAILABLE")
    print("Check individual model status above.")






