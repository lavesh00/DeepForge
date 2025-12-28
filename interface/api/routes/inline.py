"""Inline editor API routes."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from execution.inline.inline_editor import InlineEditor

router = APIRouter()


@router.post("/inline/edit")
async def inline_edit(request: Dict[str, Any]):
    """Perform inline edit (Cmd+K style)."""
    file_path = request.get("file_path")
    selected_code = request.get("selected_code", "")
    query = request.get("query", "")
    context_lines = request.get("context_lines", 500)
    
    if not file_path or not query:
        raise HTTPException(status_code=400, detail="file_path and query are required")
    
    editor = InlineEditor()
    result = editor.edit_code(file_path, selected_code, query, context_lines)
    
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/inline/apply")
async def apply_inline_edit(request: Dict[str, Any]):
    """Apply inline edit to file."""
    file_path = request.get("file_path")
    new_content = request.get("new_content", "")
    
    if not file_path or not new_content:
        raise HTTPException(status_code=400, detail="file_path and new_content are required")
    
    editor = InlineEditor()
    success = editor.apply_edit(file_path, new_content)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to apply edit")
    
    return {"success": True, "file_path": file_path}

