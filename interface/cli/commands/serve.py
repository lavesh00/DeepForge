"""Serve command."""

import click


@click.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8080, help="Port to bind to")
def serve_command(host, port):
    """Start the DeepForge web interface."""
    click.echo(f"\n{'='*60}")
    click.echo("  DeepForge Web Interface")
    click.echo(f"{'='*60}")
    click.echo(f"\n  Starting server at http://{host}:{port}")
    click.echo(f"  Open http://localhost:{port} in your browser")
    click.echo(f"\n  Press Ctrl+C to stop\n")
    
    from interface.api.server import run_server
    run_server(host=host, port=port)





