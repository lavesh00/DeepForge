"""Models command."""

import click
from core.registry import get_service
from model_runtime.manager import ModelManager


@click.group()
def models_group():
    """Manage AI models."""
    pass


@models_group.command()
def list():
    """List available models."""
    model_manager = get_service("model_manager")
    if model_manager:
        models = model_manager.list_models()
        click.echo(f"Available models: {', '.join(models) if models else 'None'}")
    else:
        click.echo("Model manager not available")


@models_group.command()
@click.argument("model_id")
def register(model_id):
    """Register a model."""
    model_manager = get_service("model_manager")
    if model_manager:
        model_manager.register_model(model_id)
        click.echo(f"Registered model: {model_id}")
    else:
        click.echo("Model manager not available")





