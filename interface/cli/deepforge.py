"""DeepForge CLI."""

import click
from interface.cli.commands.run import run_command
from interface.cli.commands.status import status_command
from interface.cli.commands.models import models_group
from interface.cli.commands.reset import reset_command
from interface.cli.commands.serve import serve_command


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """DeepForge - Autonomous AI Development Platform"""
    pass


cli.add_command(run_command, name="run")
cli.add_command(status_command, name="status")
cli.add_command(models_group, name="models")
cli.add_command(reset_command, name="reset")
cli.add_command(serve_command, name="serve")


if __name__ == "__main__":
    cli()

