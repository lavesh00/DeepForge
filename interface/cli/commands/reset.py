"""Reset command."""

import click
from pathlib import Path
from core.config import load_config


@click.command()
@click.confirmation_option(prompt="Are you sure you want to reset DeepForge?")
def reset_command():
    """Reset DeepForge configuration and state."""
    config = load_config()
    paths = config.get_paths()
    
    state_dir = Path(paths.get("state", {}).get("missions", ""))
    if state_dir.exists():
        import shutil
        shutil.rmtree(state_dir)
        click.echo("State directory cleared")
    
    click.echo("DeepForge reset complete")





