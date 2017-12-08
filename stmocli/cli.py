import click

@click.group()
def cli():
    pass

@cli.command()
def init():
    with open('.stmocli.conf', 'a'):
        pass

@cli.command()
def track():
    pass

if __name__ == '__main__':
    cli()
