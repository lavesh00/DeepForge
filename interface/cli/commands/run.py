"""Run command."""

import click
import sys
from pathlib import Path
from runtime.launcher import launch_system, shutdown_system
from state.mission_state import MissionState, MissionStatus
from state.state_store_sqlite import SQLiteStateStore
from cognition.planning.planner_engine import PlannerEngine
from execution.orchestrator.mission_controller import MissionController
from workspace.manager import WorkspaceManager
from core.config import load_config
from core.events import get_event_bus, create_event, EventType
from core.registry import get_service
import uuid


@click.command()
@click.argument("description", required=True)
@click.option("--config-dir", type=click.Path(), help="Configuration directory")
def run_command(description, config_dir):
    """Run a new mission with the given description."""
    try:
        config_path = Path(config_dir) if config_dir else None
        launch_system(config_dir=config_path, skip_bootstrap=True)
        
        config = load_config(config_path)
        paths = config.get_paths()
        state_dir = Path(paths.get("state", {}).get("missions", ""))
        workspace_base = Path(paths.get("workspace", {}).get("base_dir", Path.home() / "deepforge_workspaces"))
        
        state_store = SQLiteStateStore(state_dir / "state.db")
        workspace_manager = WorkspaceManager(workspace_base)
        
        mission_id = str(uuid.uuid4())
        mission = MissionState(
            mission_id=mission_id,
            status=MissionStatus.CREATED,
            description=description,
        )
        state_store.save_mission(mission)
        
        event_bus = get_event_bus()
        event_bus.publish(create_event(
            EventType.MISSION_CREATED,
            {"mission_id": mission_id, "description": description},
            source="cli"
        ))
        
        click.echo(f"Mission created: {mission_id[:8]}...")
        click.echo(f"Description: {description}")
        
        mission.status = MissionStatus.PLANNING
        state_store.save_mission(mission)
        
        planner = PlannerEngine()
        plan = planner.create_plan(description)
        mission.total_steps = len(plan.get_execution_order())
        mission.status = MissionStatus.EXECUTING
        state_store.save_mission(mission)
        
        event_bus.publish(create_event(
            EventType.PLAN_GENERATED,
            {"mission_id": mission_id, "task_count": mission.total_steps},
            source="cli"
        ))
        
        workspace_dir = workspace_manager.create_workspace(mission_id)
        
        controller = MissionController(
            mission=mission,
            plan=plan,
            persistence=state_store,
            workspace_dir=str(workspace_dir)
        )
        
        controller.start()
        
        click.echo(f"\n{'='*60}")
        click.echo(f"Mission started. Executing {mission.total_steps} steps...")
        click.echo(f"{'='*60}\n")
        
        max_iterations = 1000
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            success, step_id = controller.execute_next_step()
            
            if not step_id:
                break
            
            if success:
                click.echo(f"  [OK] Step {step_id} completed")
            else:
                mission = state_store.load_mission(mission_id)
                if mission and mission.status == MissionStatus.FAILED:
                    click.echo(f"  [FAIL] Step {step_id} failed")
                    break
                elif mission and mission.status == MissionStatus.PAUSED:
                    click.echo(f"  [!] Step {step_id} requires approval - mission paused")
                    break
                else:
                    click.echo(f"  [!] Step {step_id} requires approval")
                    break
        
        mission = state_store.load_mission(mission_id)
        
        if mission and mission.status == MissionStatus.COMPLETED:
            click.echo(f"\n{'='*60}")
            click.echo(f"[SUCCESS] Mission completed successfully!")
            click.echo(f"{'='*60}")
            click.echo(f"\nWorkspace location:")
            click.echo(f"  {workspace_dir}")
        elif mission and mission.status == MissionStatus.FAILED:
            click.echo(f"\n[FAILED] Mission failed: {mission.error or 'Unknown error'}")
            sys.exit(1)
        else:
            click.echo(f"\nMission status: {mission.status.value if mission else 'Unknown'}")
            if workspace_dir and Path(workspace_dir).exists():
                click.echo(f"Workspace: {workspace_dir}")
        
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
        shutdown_system()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)





