import hashlib
import os
import sys

import click

from .stmo import STMO
from .util import name_to_stub


@click.group()
@click.option(
    '--redash_api_key',
    default=lambda: os.environ.get('REDASH_API_KEY', '')
)
@click.pass_context
def cli(ctx, redash_api_key):
    ctx.obj = STMO(redash_api_key)


@cli.command()
@click.pass_obj
def init(stmo):
    stmo.conf.init_file()


@cli.command()
@click.pass_obj
@click.argument('query_id')
@click.argument('file_name', required=False)
def track(stmo, query_id, file_name):
    def make_file_name(query):
        if file_name:
            return file_name
        default_file_name = "{}.sql".format(
            name_to_stub(query["name"]),
        )
        return click.prompt("Filename for tracked query SQL", default=default_file_name)

    try:
        stmo.track_query(query_id, make_file_name)
    except STMO.RedashClientException as e:
        click.echo("Failed to track Query ID {}: {}".format(query_id, e), err=True)
        sys.exit(1)

    click.echo("Tracking Query ID {} in {}".format(query_id, file_name))


@cli.command()
@click.pass_obj
@click.argument('file_name')
def push(stmo, file_name):
    try:
        queryinfo = stmo.push_query(file_name)
    except stmo.RedashClientException as e:
        click.echo("Failed to update query from {}: {}".format(file_name, e), err=True)
        sys.exit(1)
    except KeyError as e:
        click.echo("Failed to update query from {}: No such query, "
                   "maybe you need to 'track' first".format(file_name), err=True)
        sys.exit(1)

    with open(file_name, "rt") as f:
        query = f.read()

    m = hashlib.md5(query.encode("utf-8"))
    click.echo("Query ID {} updated with content from {} (md5 {})".format(
        queryinfo.id, file_name, m.hexdigest()))


@cli.command()
@click.pass_obj
@click.argument('file_name')
def view(stmo, file_name):
    try:
        url = stmo.url_for_query(file_name)
    except KeyError:
        click.echo("Couldn't find a query ID for {}: No such query, "
                   "maybe you need to 'track' first".format(file_name),
                   err=True)
        sys.exit(1)
    click.launch(url)


@cli.command()
@click.pass_obj
@click.argument('query_to_fork')
@click.argument('new_query_file_name')
def fork(stmo, query_to_fork, new_query_file_name):
    if os.path.exists(query_to_fork):
        try:
            query_id = stmo.conf.get_query(query_to_fork).id
        except KeyError:
            click.echo("Couldn't find a query ID for {}. "
                       "Did you need to 'track' it?".format(query_to_fork),
                       err=True)
            sys.exit(1)
    elif query_to_fork.isnumeric():
        query_id = query_to_fork
    else:
        click.echo("Couldn't fork that query; no file or query named {}.".format(query_to_fork),
                   err=True)
        sys.exit(1)

    try:
        result = stmo.fork_query(query_id, new_query_file_name)
    except STMO.RedashClientException:
        click.echo("Couldn't find a query with ID {} on the server.".format(query_id), err=True)
        sys.exit(1)

    click.echo("Forked query {} to {}: {}".format(query_id, new_query_file_name, result.name))


if __name__ == '__main__':
    cli()
