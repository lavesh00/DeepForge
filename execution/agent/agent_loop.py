"""Agent Loop - Client-driven iteration with tool calls."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import asyncio
from pathlib import Path
from model_runtime.serving.local_api import LocalModelAPI
from model_runtime.serving.router import ModelRouter
from core.registry import get_service


@dataclass
class ToolCall:
    """Tool call from agent."""
    name: str
    arguments: Dict[str, Any]
    id: str


@dataclass
class AgentStep:
    """Single agent iteration step."""
    step_id: int
    user_query: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    reflection: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentLoop:
    """Agent-first iteration loop with tool calls."""
    
    def __init__(self, workspace_dir: str, mission_id: str = "default"):
        """
        Initialize agent loop.
        
        Args:
            workspace_dir: Workspace directory
            mission_id: Mission identifier
        """
        self.workspace_dir = Path(workspace_dir)
        self.mission_id = mission_id
        self.steps: List[AgentStep] = []
        self.max_iterations = 20
        self.max_failures = 3
        
        # Get model API
        try:
            model_manager = get_service("model_manager")
            if model_manager:
                router = ModelRouter(model_manager=model_manager)
                self.model_api = LocalModelAPI(router)
            else:
                self.model_api = None
        except Exception:
            self.model_api = None
        
        # Tool registry
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register available tools."""
        return {
            "codebase_search": {
                "description": "Semantic search across codebase using embeddings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            },
            "grep": {
                "description": "Search files with regex pattern",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string", "description": "Regex pattern"},
                        "path": {"type": "string", "description": "File or directory path"}
                    },
                    "required": ["pattern"]
                }
            },
            "read_file": {
                "description": "Read file contents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                        "offset": {"type": "integer", "description": "Start line"},
                        "limit": {"type": "integer", "description": "Number of lines"}
                    },
                    "required": ["file_path"]
                }
            },
            "edit_file": {
                "description": "Edit file with semantic diff",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                        "old_string": {"type": "string", "description": "Code to replace"},
                        "new_string": {"type": "string", "description": "New code"}
                    },
                    "required": ["file_path", "old_string", "new_string"]
                }
            },
            "write_file": {
                "description": "Write new file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"},
                        "content": {"type": "string", "description": "File content"}
                    },
                    "required": ["file_path", "content"]
                }
            },
            "delete_file": {
                "description": "Delete file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to file"}
                    },
                    "required": ["file_path"]
                }
            },
            "run_terminal_cmd": {
                "description": "Run terminal command in sandbox",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to run"},
                        "cwd": {"type": "string", "description": "Working directory"}
                    },
                    "required": ["command"]
                }
            },
            "read_lints": {
                "description": "Get linter errors for files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "paths": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            "list_dir": {
                "description": "List directory contents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_directory": {"type": "string", "description": "Directory path"}
                    },
                    "required": ["target_directory"]
                }
            },
            "todo_write": {
                "description": "Create or update todo list",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "merge": {"type": "boolean"},
                        "todos": {"type": "array", "items": {"type": "object"}}
                    },
                    "required": ["todos"]
                }
            },
            "create_plan": {
                "description": "Create execution plan",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "goal": {"type": "string", "description": "Goal description"},
                        "steps": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["goal"]
                }
            },
            "glob_file_search": {
                "description": "Search files by pattern",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "glob_pattern": {"type": "string", "description": "Glob pattern"}
                    },
                    "required": ["glob_pattern"]
                }
            }
        }
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for agent."""
        return """You are an autonomous code wizard, a pair-programming god capable of building complete software projects.

Rules:
- Always plan first: Break goals into steps, create todos
- Use tools systematically: Search, read, edit, test, iterate
- Self-correct: Fix errors, run lints, verify changes
- Be self-sufficient: Don't ask for help, just execute
- Output tool calls as JSON: {"tool_calls": [{"name": "...", "arguments": {...}, "id": "..."}]}
- Maximize parallel tool calls when possible
- Reflect after each step: What worked? What failed? What's next?

Available tools: """ + json.dumps(list(self.tools.keys()), indent=2)
    
    async def execute_tool(self, tool_call: ToolCall) -> Dict[str, Any]:
        """
        Execute a tool call.
        
        Args:
            tool_call: Tool call to execute
            
        Returns:
            Tool execution result
        """
        tool_name = tool_call.name
        args = tool_call.arguments
        
        try:
            if tool_name == "codebase_search":
                from cognition.context.semantic_search import SemanticSearch
                searcher = SemanticSearch(self.workspace_dir)
                results = searcher.search(args["query"], top_k=5)
                return {"results": results}
            
            elif tool_name == "grep":
                from execution.tools import grep_tool
                results = grep_tool(args.get("pattern"), args.get("path", str(self.workspace_dir)))
                return {"matches": results}
            
            elif tool_name == "read_file":
                file_path = Path(args["file_path"])
                if not file_path.is_absolute():
                    file_path = self.workspace_dir / file_path
                content = file_path.read_text(encoding='utf-8')
                lines = content.splitlines()
                offset = args.get("offset", 0)
                limit = args.get("limit", len(lines))
                return {"content": "\n".join(lines[offset:offset+limit])}
            
            elif tool_name == "edit_file":
                file_path = Path(args["file_path"])
                if not file_path.is_absolute():
                    file_path = self.workspace_dir / file_path
                content = file_path.read_text(encoding='utf-8')
                new_content = content.replace(args["old_string"], args["new_string"])
                file_path.write_text(new_content, encoding='utf-8')
                return {"success": True, "file_path": str(file_path)}
            
            elif tool_name == "write_file":
                file_path = Path(args["file_path"])
                if not file_path.is_absolute():
                    file_path = self.workspace_dir / file_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(args["content"], encoding='utf-8')
                return {"success": True, "file_path": str(file_path)}
            
            elif tool_name == "delete_file":
                file_path = Path(args["file_path"])
                if not file_path.is_absolute():
                    file_path = self.workspace_dir / file_path
                file_path.unlink()
                return {"success": True}
            
            elif tool_name == "run_terminal_cmd":
                import subprocess
                cwd = args.get("cwd", str(self.workspace_dir))
                result = subprocess.run(
                    args["command"],
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            
            elif tool_name == "read_lints":
                from execution.tools import lint_tool
                paths = args.get("paths", [])
                errors = lint_tool(paths)
                return {"errors": errors}
            
            elif tool_name == "list_dir":
                dir_path = Path(args["target_directory"])
                if not dir_path.is_absolute():
                    dir_path = self.workspace_dir / dir_path
                items = [{"name": item.name, "type": "dir" if item.is_dir() else "file"} 
                        for item in dir_path.iterdir()]
                return {"items": items}
            
            elif tool_name == "glob_file_search":
                from execution.tools import glob_tool
                pattern = args["glob_pattern"]
                matches = glob_tool(pattern, str(self.workspace_dir))
                return {"matches": matches}
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            return {"error": str(e)}
    
    async def iterate(self, user_query: str) -> AgentStep:
        """
        Single agent iteration.
        
        Args:
            user_query: User's goal or query
            
        Returns:
            Agent step result
        """
        step = AgentStep(
            step_id=len(self.steps),
            user_query=user_query,
            started_at=datetime.utcnow()
        )
        step.status = "running"
        self.steps.append(step)
        
        try:
            # Build messages
            messages = [
                {"role": "system", "content": self._build_system_prompt()},
            ]
            
            # Add previous steps context
            for prev_step in self.steps[-3:]:  # Last 3 steps
                if prev_step.tool_results:
                    messages.append({
                        "role": "assistant",
                        "content": f"Previous step: {prev_step.user_query}\nResults: {json.dumps(prev_step.tool_results)}"
                    })
            
            messages.append({"role": "user", "content": user_query})
            
            # Call DeepSeek V3.2
            if self.model_api:
                response = self.model_api.chat_completion(
                    model="deepseek-coder",
                    messages=messages,
                    max_tokens=2048,
                    temperature=0.2
                )
                
                content = response["choices"][0]["message"]["content"]
                
                # Parse tool calls from response
                tool_calls = self._parse_tool_calls(content)
                
                # Execute tools
                for tool_call in tool_calls:
                    result = await self.execute_tool(tool_call)
                    step.tool_calls.append(tool_call)
                    step.tool_results.append(result)
                
                step.status = "completed"
                step.completed_at = datetime.utcnow()
            else:
                raise ValueError("Model API not available")
        
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            step.completed_at = datetime.utcnow()
        
        return step
    
    def _parse_tool_calls(self, content: str) -> List[ToolCall]:
        """Parse tool calls from agent response."""
        tool_calls = []
        
        try:
            # Try to extract JSON
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(content[json_start:json_end])
                if "tool_calls" in data:
                    for i, tc in enumerate(data["tool_calls"]):
                        tool_calls.append(ToolCall(
                            name=tc["name"],
                            arguments=tc.get("arguments", {}),
                            id=tc.get("id", f"call_{i}")
                        ))
        except Exception:
            pass
        
        return tool_calls
    
    async def run(self, goal: str) -> Dict[str, Any]:
        """
        Run agent loop until goal achieved or max iterations.
        
        Args:
            goal: High-level goal
            
        Returns:
            Execution results
        """
        failures = 0
        
        for i in range(self.max_iterations):
            step = await self.iterate(goal if i == 0 else f"Continue working on: {goal}")
            
            if step.status == "failed":
                failures += 1
                if failures >= self.max_failures:
                    break
            
            # Check if goal achieved (heuristic: no errors, files created)
            if step.status == "completed" and not step.error:
                # Could add goal verification here
                pass
        
        return {
            "steps": len(self.steps),
            "completed": sum(1 for s in self.steps if s.status == "completed"),
            "failed": sum(1 for s in self.steps if s.status == "failed"),
            "final_status": self.steps[-1].status if self.steps else "no_steps"
        }





