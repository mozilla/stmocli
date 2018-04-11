import hashlib
import os

import click
from redash_client.client import RedashClient
import requests
from requests.compat import urljoin

from .conf import Conf
from .util import name_to_stub

pass_conf = click.make_pass_decorator(Conf, ensure=True)


@click.group()
def cli():
    pass


@cli.command()
@pass_conf
def init(conf):
    conf.init_file()


@cli.command()
@pass_conf
@click.argument('query_id')
@click.argument('file_name', required=False)
@click.option(
    '--redash_api_key',
    default=lambda: os.environ.get('REDASH_API_KEY', '')
)
def track(conf, query_id, file_name, redash_api_key):
    # Get query:
    # https://github.com/getredash/redash/blob/1573e06e710733714d47940cc1cb196b8116f670/redash/handlers/api.py#L74
    redash = RedashClient(redash_api_key)
    url_path = 'queries/{}?api_key={}'.format(query_id, redash_api_key)
    try:
        results, response = redash._make_request(
            requests.get,
            urljoin(redash.API_BASE_URL, url_path)
        )

        if not file_name:
            file_name = "{}_{}.sql".format(
                query_id,
                name_to_stub(results["name"]),
            )

        query = results['query']
        with open(file_name, 'w') as outfile:
            outfile.write(query)

        query_meta = {
            "id": query_id,
            "data_source_id": results['data_source_id'],
            "name": results['name'],
            "description": results['description'],
            "schedule": results['schedule'],
            "options": results['options']
        }
        conf.add_query(file_name, query_meta)
        click.echo("Tracking Query ID {} in {}".format(query_id, file_name))
    except RedashClient.RedashClientException as e:
        click.echo("Failed to track Query ID {}: {}".format(query_id, e))


@cli.command()
@pass_conf
@click.argument('file_name')
@click.option(
    '--redash_api_key',
    default=lambda: os.environ.get('REDASH_API_KEY', '')
)
def push(conf, file_name, redash_api_key):
    redash = RedashClient(redash_api_key)

    try:
        meta = conf.get_query(file_name)
        with open(file_name, 'r') as fin:
            query = fin.read()

        try:
            redash.update_query(meta['id'], meta['name'],
                                query, meta['data_source_id'],
                                meta['description'], meta['options'])

            m = hashlib.md5(query.encode("utf-8"))
            click.echo("Query ID {} updated with content from {} (md5 {})".format(
                meta["id"], file_name, m.hexdigest()))
        except RedashClient.RedashClientException as e:
            click.echo("Failed to update query from {}: {}".format(file_name, e))
    except KeyError as e:
        click.echo("Failed to update query from {}: No such query, "
                   "maybe you need to 'track' first".format(file_name))


if __name__ == '__main__':
    cli()
