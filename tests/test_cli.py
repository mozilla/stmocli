import traceback
import pytest
import click
import os
from httmock import all_requests, HTTMock
from redash_client.client import RedashClient
from click.testing import CliRunner
from stmocli import cli


with open('tests/data/example_query_response.json', 'rt') as infile:
    example_response = infile.read()

@all_requests
def response_content(url, request):
    return {
        'status_code': 200,
        'content': example_response,
    }

@pytest.fixture
def runner():
    return CliRunner()

def test_init(runner):
    with runner.isolated_filesystem():
        runner.invoke(cli.init)

        assert os.path.isfile('.stmocli.conf')

def test_track(runner):
    query_id = '49741'
    filename = 'poc.sql'

    with runner.isolated_filesystem():
        with HTTMock(response_content):
            result = runner.invoke(cli.track, [
                query_id,
                filename,
                '--redash_api_key',
                'TOTALLY_FAKE_KEY'
            ])


        assert os.path.isfile(filename)
        with open(filename, 'r') as query:
            assert "SELECT" in query.read()


def print_debug_for_runner(result):
    """Helper function for printing click.runner debug tracebacks."""
    print(result.output)
    print(result.exc_info)
    traceback.print_tb(result.exc_info[2])
    print(result.exit_code)
    print(result.exception)
