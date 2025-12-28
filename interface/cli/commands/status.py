"""Status command."""

import click
from state.state_store_sqlite import SQLiteStateStore
from core.config import load_config
from pathlib import Path


@click.command()
@click.option("--mission-id", help="Mission ID to check")
@click.option("--all", is_flag=True, help="List all missions")
def status_command(mission_id, all):
    """Check status of a mission or list all missions."""
    config = load_config()
    paths = config.get_paths()
    state_dir = Path(paths.get("state", {}).get("missions", ""))
    
    state_store = SQLiteStateStore(state_dir / "state.db")
    
    if all:
        missions = state_store.list_missions()
        click.echo(f"Found {len(missions)} missions")
        for mid in missions[:10]:
            mission = state_store.load_mission(mid)
            if mission:
                click.echo(f"  {mid[:8]}... - {mission.status.value} - {mission.description[:50]}")
    elif mission_id:
        mission = state_store.load_mission(mission_id)
        if mission:
            click.echo(f"Mission: {mission.mission_id}")
            click.echo(f"Status: {mission.status.value}")
            click.echo(f"Description: {mission.description}")
            click.echo(f"Progress: {mission.completed_steps}/{mission.total_steps} steps")
        else:
            click.echo(f"Mission {mission_id} not found")
    else:
        click.echo("Use --mission-id or --all")





