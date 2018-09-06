import hashlib
import os
import sys
import csv
import click

from .stmo import STMO
from .util import name_to_stub


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.option(
    '--redash_api_key',
    default=lambda: os.environ.get('REDASH_API_KEY', ''),
    help=("A redash user API key, from your user settings page. "
          "Defaults to the value of the REDASH_API_KEY environment variable.")
)
@click.pass_context
def cli(ctx, redash_api_key):
    """St. Mocli is a command-line interface for sql.telemetry.mozilla.org."""
    ctx.obj = STMO(redash_api_key)


@cli.command()
@click.pass_obj
def init(stmo):
    """Initializes a repository.

    Creates an empty .stmocli.conf in the current directory, which will hold
    stmocli's metadata.
    """
    stmo.conf.init_file()


@cli.command()
@click.pass_obj
@click.argument('query_id')
@click.argument('file_name', required=False)
def track(stmo, query_id, file_name):
    """Adds a STMO query to the local repository.

    QUERY_ID: The numeric ID of the redash query you wish to track

    FILE_NAME: The filename to use for the query SQL in the local repository.
    You will be prompted with a suggested filename if you don't provide one.

    Downloads the SQL query associated with the given query ID and saves it in a file
    with the given name.
    """
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
    """Uploads a tracked query to STMO.

    FILE_NAME: The filename of the tracked query SQL.

    Overwrites the STMO query SQL with the version in the local repository.
    """
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
    """Opens a query in a browser.

    FILE_NAME: The filename of the tracked query SQL.

    Opens a browser window to the redash query.
    """
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
    """Copies a STMO query and tracks the result.

    QUERY_TO_FORK: Either the filename of a query that's already tracked,
    or the numeric ID of any redash query.

    NEW_QUERY_FILE_NAME: The filename to use for the new query's SQL.
    """
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


@cli.command()
@click.pass_obj
@click.argument('query_id')
@click.argument('file_name', required=False)
def write_csv(stmo, query_id, file_name):
    """gets the dataset resulting from the query_id and writes to a csv.
    data must already exist, this does not execute the query on the server.
    csv will have variable names as first row.

    QUERY_ID: redash id of the query you want data from

    FILE_NAME: optional, filename (with absolute path) of csv file. if None,
    use the query's name + .csv and write to pwd
    """
    try:
        query_name, results = stmo.get_results(query_id)
    except STMO.RedashClientException:
        click.echo("Couldn't find a query with ID {} on the server.".format(query_id), err=True)
        sys.exit(1)
    fn = file_name if file_name else query_name + '.csv'
    headers = results[0].keys()
    with open(fn, 'wb') as output_file:
        dict_writer = csv.DictWriter(output_file, headers)
        dict_writer.writeheader()
        dict_writer.writerows(results)


if __name__ == '__main__':
    cli()
