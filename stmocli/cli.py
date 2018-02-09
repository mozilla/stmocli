from redash_client.client import RedashClient
from requests.compat import urljoin
from .conf import Conf
import click
import os
import requests


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
@click.argument('file_name')
@click.option(
    '--redash_api_key',
    default=lambda: os.environ.get('REDASH_API_KEY', '')
)
def track(conf, query_id, file_name, redash_api_key):
    # Get query: https://github.com/getredash/redash/blob/1573e06e710733714d47940cc1cb196b8116f670/redash/handlers/api.py#L74
    redash = RedashClient(redash_api_key)
    url_path = 'queries/{}?api_key={}'.format(query_id, redash_api_key)
    results, response = redash._make_request(
        requests.get,
        urljoin(redash.API_BASE_URL, url_path)
    )

    query = results['query']
    with open(file_name, 'w') as outfile:
        outfile.write(query)

    query_meta = {
        "query_id": query_id,
        "data_source_id": results['data_source_id'],
        "name": results['name'],
        "description": results['description'],
        "schedule": results['schedule'],
        "options": results['options']
    }
    conf.add_query(file_name, query_meta)


@cli.command()
@pass_conf
@click.argument('file_name')
@click.option(
    '--redash_api_key',
    default=lambda: os.environ.get('REDASH_API_KEY', '')
)
def push(conf, file_name, redash_api_key):
    redash = RedashClient(redash_api_key)

    query_meta = conf.get_query(file_name)
    with open(file_name, 'r') as fin:
        query = fin.read()

    redash.update_query(query_meta['query_id'], query_meta['name'],
                        query, query_meta['data_source_id'],
                        query_meta['description'], query_meta['options'])



if __name__ == '__main__':
    cli()
