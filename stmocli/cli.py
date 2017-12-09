from redash_client.client import RedashClient
from requests.compat import urljoin
import click
import os
import requests


@click.group()
def cli():
    pass


@cli.command()
def init():
    with open('.stmocli.conf', 'a'):
        pass


@cli.command()
@click.argument('query_id')
@click.argument('filename')
@click.option(
    '--redash_api_key',
    default=lambda: os.environ.get('REDASH_API_KEY', '')
)
def track(query_id, filename, redash_api_key):
    # Get query: https://github.com/getredash/redash/blob/1573e06e710733714d47940cc1cb196b8116f670/redash/handlers/api.py#L74
    redash = RedashClient(redash_api_key)
    url_path = 'queries/{}?api_key={}'.format(query_id, redash_api_key)
    results, response = redash._make_request(
        requests.get, 
        urljoin(redash.BASE_URL, url_path)
    )
    query = results['query']

    with open(filename, 'w') as outfile:
        outfile.write(query)


if __name__ == '__main__':
    cli()
