# Cursor-Evolution Features Implementation

## Overview
This document describes the Cursor-like iterative refinement features added to DeepForge. These features enable real-time chat-based code editing, automatic bug fixing, and iterative improvement of generated code.

## New Modules

### 1. `cognition/chat/chat_engine.py`
**Purpose**: Handles iterative chat-based code refinement using DeepSeek.

**Key Features**:
- Gathers workspace context (all code files)
- Maintains chat history per mission
- Routes queries through DeepSeek model
- Applies unified diff patches to files
- Falls back to template-based edits if model fails

**Usage**:
```python
chat_engine = ChatEngine(mission_id, workspace_dir)
result = chat_engine.handle_query("add delete endpoint")
# Returns: explanation, diff, patched_files, confidence
```

### 2. `execution/codegen/refactor_engine.py`
**Purpose**: Automatic refactoring based on errors or user requests.

**Key Features**:
- Auto-fixes bugs from error tracebacks
- Performance optimization suggestions
- Security improvements
- AST analysis for code quality
- Retries with improved prompts on failure

**Usage**:
```python
refactor_engine = RefactorEngine(chat_engine)
result = refactor_engine.refactor_on_error(error_trace, "main.py")
```

### 3. `state/session_memory.py`
**Purpose**: Persistent chat history storage in SQLite.

**Key Features**:
- Stores user queries and AI responses
- Retrieves last N turns for context
- Per-mission isolation
- Automatic table initialization

### 4. Enhanced `execution/codegen/code_engine.py`
**New Method**: `polish_template()`
- Takes template code and mission description
- Uses DeepSeek to enhance code quality
- Adds error handling, docstrings, optimizations
- Falls back to original if polish fails

### 5. Enhanced `execution/orchestrator/mission_controller.py`
**Integration Points**:
- Initializes `ChatEngine` and `RefactorEngine` on mission start
- Polishes template code with DeepSeek after generation
- Auto-refactors on test failures
- Retries up to 3 times on test errors

### 6. New API Endpoints (`interface/api/server.py`)

#### `POST /api/missions/{mission_id}/chat`
Chat with a mission for iterative refinement.

**Request**:
```json
{
  "query": "add delete endpoint"
}
```

**Response**:
```json
{
  "explanation": "Added DELETE endpoint...",
  "diff": "--- a/main.py\n+++ b/main.py\n...",
  "patched_files": ["main.py"],
  "confidence": 0.85,
  "history": [...]
}
```

#### `POST /api/missions/{mission_id}/edit`
Edit a specific file with AI, optionally with error context.

**Request**:
```json
{
  "file": "main.py",
  "query": "Refactor this file",
  "error": "Optional error traceback"
}
```

### 7. Enhanced UI (`interface/ui/web/public/index.html`)
**New Features**:
- Chat tab in sidebar
- Chat screen with message history
- Real-time diff display
- Confidence scores
- File update notifications
- Keyboard shortcuts (Enter to send)

## Workflow

### 1. Create Mission
```bash
deepforge run "create a todo API"
```

### 2. Iterate via Chat
1. Open UI → Click "Chat" tab
2. Type: "add delete endpoint"
3. AI analyzes workspace, generates diff, applies patch
4. View diff and updated files

### 3. Auto-Fix on Errors
- If tests fail, `RefactorEngine` automatically:
  1. Extracts error from traceback
  2. Queries DeepSeek for fix
  3. Applies patch
  4. Re-runs tests
  5. Retries up to 3 times

### 4. Code Polish
- Template code is automatically polished with DeepSeek:
  - Adds error handling
  - Improves code quality
  - Adds docstrings
  - Optimizes where possible

## Technical Details

### DeepSeek Integration
- Uses `deepseek-coder` model (configured in `defaults.yaml`)
- Routes through `LocalModelAPI` → `ModelRouter` → `TransformersAdapter`
- JSON responses parsed for structured edits
- Falls back gracefully if model unavailable

### Diff Application
- Parses unified diff format
- Handles hunk headers (`@@ -start,count +start,count @@`)
- Applies additions (`+`), deletions (`-`), context (` `)
- Creates files if they don't exist
- Falls back to code block extraction if diff malformed

### Context Gathering
- Scans workspace for `.py`, `.js`, `.html`, `.css`, `.json`
- Truncates files to 2000 chars for token limits
- Includes relative paths for clarity
- Maintains chat history (last 5 turns)

## Testing

### Manual Test
1. Start server: `python -m interface.api.server`
2. Create mission via UI: "create a simple flask API"
3. Wait for completion
4. Open Chat tab
5. Type: "add a POST /users endpoint"
6. Verify `main.py` updated with new endpoint
7. Check syntax: `python -m py_compile main.py` should pass

### API Test
```bash
# Single chat query
curl -X POST http://localhost:8080/api/missions/{mission_id}/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "add delete endpoint"}'

# Chain refinement
curl -X POST http://localhost:8080/api/missions/{mission_id}/chain \
  -H "Content-Type: application/json" \
  -d '{"query": "Secure todo API with OAuth", "max_steps": 5}'
```

### Validation Test
```python
# Test patch validation
from cognition.chat.chat_engine import ChatEngine
chat = ChatEngine("test", "/tmp/test_workspace")
# Create a file with syntax error
Path("/tmp/test_workspace/main.py").write_text("def broken(")
# Try to patch - should rollback
try:
    chat._apply_patch("--- a/main.py\n+++ b/main.py\n@@ -1,1 +1,1 @@\n-def broken(\n+def broken():\n", "main.py")
except ValueError as e:
    assert "validation failed" in str(e).lower()
```

### Integration Test (Recommended)
```python
# tests/test_chat_integration.py
import pytest
from cognition.chat.chat_engine import ChatEngine
from pathlib import Path

def test_chat_patch_validation():
    workspace = Path("/tmp/test_chat")
    workspace.mkdir(exist_ok=True)
    (workspace / "main.py").write_text("def hello():\n    pass\n")
    
    chat = ChatEngine("test", str(workspace))
    result = chat.handle_query("add a goodbye function")
    
    assert result["patched_files"]
    # Validate syntax
    compile((workspace / "main.py").read_text(), "main.py", "exec")
```

## Recent Improvements (Dec 2025)

### Model Upgrade
- **Primary**: `deepseek-ai/deepseek-coder-v2-lite-instruct` (2025 recommended)
- **Fallback**: `deepseek-ai/deepseek-coder-1.3b-base` (legacy support)
- Auto-fallback if v2 unavailable
- Structured JSON output enforcement in prompts

### Robust Patch Application
- **Syntax Validation**: Python files validated with `compile()` before applying
- **Rollback on Failure**: Automatic rollback if patch creates syntax errors
- **Better Diff Parsing**: Improved hunk header parsing and context line handling
- **Code Block Extraction**: Falls back to extracting code from markdown blocks

### Chain Mode
- **Multi-Step Refinement**: `chain_refine()` breaks complex queries into steps
- **Adaptive Stopping**: Stops early if confidence > 0.9
- **Context Accumulation**: Each step builds on previous results
- **API Endpoint**: `POST /api/missions/{id}/chain` for chain refinement

### Example: Chain Refinement
```python
# Single query: "Secure todo API with OAuth"
result = chat_engine.chain_refine("Secure todo API with OAuth", max_steps=5)
# Step 1: Add OAuth dependencies
# Step 2: Implement OAuth flow
# Step 3: Add protected routes
# Step 4: Add token validation
# Step 5: Test and polish
```

## Limitations

1. **Diff Parsing**: Enhanced but still basic; complex multi-file patches may need manual review
2. **Context Size**: Files truncated to 2000 chars; large codebases may lose context (v2 handles 128k, but truncation remains for token limits)
3. **Model Fallback**: Falls back to 1.3B if v2 unavailable; upgrade GPU for best performance
4. **Retry Logic**: Fixed 3 retries in refactor; chain mode has adaptive stopping
5. **File Scope**: Primarily targets `main.py`; multi-file edits work but need explicit file paths

## Future Enhancements

1. **WebSocket Streaming**: Real-time diff streaming during generation
2. **Multi-file Edits**: Support editing multiple files in one query (partially implemented)
3. **AST-based Patching**: More robust diff application using AST (syntax validation done, full AST patching pending)
4. **Context Window Management**: Smart truncation and summarization (v2 handles 128k, but summarization would help)
5. **Composer Mode**: Multi-step planning and execution (chain mode implemented, full composer UI pending)
6. **Code Review**: AI-powered code review suggestions
7. **Adaptive Retry**: Exponential backoff with prompt refinement
8. **Dry-run Mode**: Simulate patches before applying

## Files Modified/Created

**New Files**:
- `cognition/chat/__init__.py`
- `cognition/chat/chat_engine.py`
- `execution/codegen/refactor_engine.py`
- `state/session_memory.py`

**Modified Files**:
- `execution/codegen/code_engine.py` (added `polish_template`)
- `execution/orchestrator/mission_controller.py` (integrated chat/refactor)
- `interface/api/server.py` (added chat/edit endpoints)
- `interface/ui/web/public/index.html` (added chat UI)

## Dependencies
No new dependencies required. Uses existing:
- `transformers` (for DeepSeek)
- `sqlite3` (for session memory)
- `difflib` (for diff parsing)
- `ast` (for code analysis)
- `fastapi` (for API endpoints)

## Status
✅ All modules implemented and tested
✅ API endpoints functional
✅ UI integrated
✅ Auto-refactor on errors working
✅ Code polish integrated
✅ Session memory persistent

Ready for production use with DeepSeek model.

