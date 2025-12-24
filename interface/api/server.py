"""DeepForge API Server."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import uvicorn
import uuid

from runtime.launcher import launch_system
from state.state_store_sqlite import SQLiteStateStore
from state.mission_state import MissionState, MissionStatus
from cognition.planning.planner_engine import PlannerEngine
from execution.orchestrator.mission_controller import MissionController
from workspace.manager import WorkspaceManager
from core.config import load_config
from core.events import get_event_bus

# Global state
_initialized = False
_state_store = None
_workspace_manager = None
_event_bus = None


class MissionRequest(BaseModel):
    description: str


class MissionResponse(BaseModel):
    mission_id: str
    status: str
    description: str
    total_steps: int
    completed_steps: int
    workspace: Optional[str] = None


def initialize():
    """Initialize the system."""
    global _initialized, _state_store, _workspace_manager
    
    if _initialized:
        return
    
    config = load_config()
    paths = config.get_paths()
    
    state_dir = Path(paths.get("state", {}).get("missions", ""))
    state_dir.mkdir(parents=True, exist_ok=True)
    _state_store = SQLiteStateStore(state_dir / "state.db")
    
    workspace_base = Path(paths.get("workspace", {}).get("base_dir", Path.home() / "deepforge_workspaces"))
    _workspace_manager = WorkspaceManager(workspace_base)
    
    _initialized = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    global _event_bus
    initialize()
    launch_system(skip_bootstrap=True)
    _event_bus = get_event_bus()
    if _event_bus:
        await _event_bus.start()
    
    yield
    
    # Shutdown
    if _event_bus:
        await _event_bus.stop()


app = FastAPI(
    title="DeepForge API",
    description="Autonomous AI Development Platform API",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Serve the web UI."""
    ui_path = Path(__file__).parent.parent / "ui" / "web" / "public" / "index.html"
    if ui_path.exists():
        return FileResponse(ui_path)
    return {"message": "DeepForge API", "version": "0.1.0"}


@app.get("/api/health")
async def health():
    """Health check."""
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/api/missions", response_model=MissionResponse)
async def create_mission(request: MissionRequest):
    """Create and run a new mission."""
    initialize()
    
    mission_id = str(uuid.uuid4())
    mission = MissionState(
        mission_id=mission_id,
        status=MissionStatus.CREATED,
        description=request.description,
    )
    _state_store.save_mission(mission)
    
    # Plan the mission
    planner = PlannerEngine()
    plan = planner.create_plan(request.description)
    mission.total_steps = len(plan.get_execution_order())
    mission.status = MissionStatus.EXECUTING
    _state_store.save_mission(mission)
    
    # Create workspace
    workspace_dir = _workspace_manager.create_workspace(mission_id)
    
    # Execute mission
    controller = MissionController(
        mission=mission,
        plan=plan,
        persistence=_state_store,
        workspace_dir=str(workspace_dir)
    )
    
    controller.start()
    
    # Execute all steps
    while True:
        success, step_id = controller.execute_next_step()
        if not step_id:
            break
    
    # Reload mission state
    mission = _state_store.load_mission(mission_id)
    
    return MissionResponse(
        mission_id=mission.mission_id,
        status=mission.status.value,
        description=mission.description,
        total_steps=mission.total_steps,
        completed_steps=mission.completed_steps,
        workspace=str(workspace_dir),
    )


@app.get("/api/missions", response_model=List[MissionResponse])
async def list_missions():
    """List all missions."""
    initialize()
    
    mission_ids = _state_store.list_missions()
    missions = []
    
    for mid in mission_ids[:20]:  # Limit to 20
        mission = _state_store.load_mission(mid)
        if mission:
            workspace_dir = _workspace_manager.get_workspace(mid)
            missions.append(MissionResponse(
                mission_id=mission.mission_id,
                status=mission.status.value,
                description=mission.description,
                total_steps=mission.total_steps,
                completed_steps=mission.completed_steps,
                workspace=str(workspace_dir) if workspace_dir else None,
            ))
    
    return missions


@app.get("/api/missions/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: str):
    """Get mission details."""
    initialize()
    
    mission = _state_store.load_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    return MissionResponse(
        mission_id=mission.mission_id,
        status=mission.status.value,
        description=mission.description,
        total_steps=mission.total_steps,
        completed_steps=mission.completed_steps,
    )


@app.get("/api/missions/{mission_id}/files")
async def get_mission_files(mission_id: str):
    """Get files generated for a mission."""
    initialize()
    
    mission = _state_store.load_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    workspace_dir = _workspace_manager.get_workspace(mission_id)
    if not workspace_dir or not workspace_dir.exists():
        return []
    
    files = []
    for file_path in workspace_dir.rglob("*.py"):
        if file_path.is_file():
            try:
                files.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(workspace_dir)),
                    "content": file_path.read_text()
                })
            except Exception:
                pass
    
    return files


@app.post("/api/missions/{mission_id}/chat")
async def chat_with_mission(mission_id: str, request: Dict[str, str]):
    """Chat with mission for iterative refinement."""
    initialize()
    
    mission = _state_store.load_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    query = request.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    workspace_dir = _workspace_manager.get_workspace(mission_id)
    if not workspace_dir:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    from cognition.chat.chat_engine import ChatEngine
    chat_engine = ChatEngine(mission_id, str(workspace_dir))
    
    result = chat_engine.handle_query(query)
    
    return result


@app.post("/api/missions/{mission_id}/edit")
async def edit_file(mission_id: str, request: Dict[str, Any]):
    """Edit a specific file with AI."""
    initialize()
    
    mission = _state_store.load_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    file_path = request.get("file", "main.py")
    query = request.get("query", "Refactor this file")
    error = request.get("error")
    
    workspace_dir = _workspace_manager.get_workspace(mission_id)
    if not workspace_dir:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    from cognition.chat.chat_engine import ChatEngine
    from execution.codegen.refactor_engine import RefactorEngine
    
    chat_engine = ChatEngine(mission_id, str(workspace_dir))
    
    if error:
        # Auto-refactor on error
        refactor_engine = RefactorEngine(chat_engine)
        result = refactor_engine.refactor_on_error(error, affected_file=file_path)
    else:
        # Regular edit
        edit_query = f"{query} for {file_path}"
        result = chat_engine.handle_query(edit_query)
    
    return result


@app.post("/api/missions/{mission_id}/chain")
async def chain_refine(mission_id: str, request: Dict[str, Any]):
    """Multi-step chain refinement for complex queries."""
    initialize()
    
    mission = _state_store.load_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    query = request.get("query", "")
    max_steps = request.get("max_steps", 5)
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    workspace_dir = _workspace_manager.get_workspace(mission_id)
    if not workspace_dir:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    from execution.orchestrator.mission_controller import MissionController
    from cognition.planning.planner_engine import PlannerEngine
    
    # Get existing controller or create new one
    plan = PlannerEngine().create_plan(mission.description)
    controller = MissionController(
        mission=mission,
        plan=plan,
        persistence=_state_store,
        workspace_dir=str(workspace_dir)
    )
    
    result = controller.chain_refine(query, max_steps)
    
    return result


@app.get("/api/models/active")
async def get_active_model():
    """Get currently active model."""
    from core.registry import get_service
    from core.config import load_config
    
    config = load_config()
    model_config = config.get_section("models")
    default_model_id = model_config.get("default_model", "deepseek-coder")
    model_name = model_config.get("model_name", "deepseek-ai/deepseek-coder-1.3b-base")
    
    model_manager = get_service("model_manager")
    if model_manager:
        model_info = model_manager.get_model(default_model_id)
        if model_info and model_info.model_path:
            return {
                "model": {
                    "id": model_info.model_id,
                    "name": model_name,
                    "status": model_info.state.value,
                    "path": str(model_info.model_path),
                    "loaded": model_info.state.value == "loaded"
                }
            }
        elif model_info:
            return {
                "model": {
                    "id": model_info.model_id,
                    "name": model_name,
                    "status": "registered_not_loaded",
                    "path": None,
                    "loaded": False
                }
            }
    
    return {
        "model": {
            "id": default_model_id,
            "name": model_name,
            "status": "not_registered",
            "path": None,
            "loaded": False
        }
    }


def run_server(host: str = "0.0.0.0", port: int = 8080):
    """Run the API server."""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()

