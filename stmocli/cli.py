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
@click.argument('query_name')
@click.option(
    '--redash_api_key',
    default=lambda: os.environ.get('REDASH_API_KEY', '')
)
def track(conf, query_id, query_name, redash_api_key):
    # Get query: https://github.com/getredash/redash/blob/1573e06e710733714d47940cc1cb196b8116f670/redash/handlers/api.py#L74
    redash = RedashClient(redash_api_key)
    url_path = 'queries/{}?api_key={}'.format(query_id, redash_api_key)
    results, response = redash._make_request(
        requests.get, 
        urljoin(redash.BASE_URL, url_path)
    )
    query = results['query']

    filename = query_name + '.sql'
    with open(filename, 'w') as outfile:
        outfile.write(query)

    conf.add_query(query_name, query_id, filename)


if __name__ == '__main__':
    cli()
