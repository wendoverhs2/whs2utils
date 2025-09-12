import click
import noiserun

@click.group()
def cli():
    """whs2utils: A utility CLI for various tasks."""
    pass

@cli.command()
def todo():
    """
    Stub click command

    Example: whs2utils todo
    """
    print('Welcome to whs2utils')
    noiserun.run()

if __name__ == "__main__":
    todo()
