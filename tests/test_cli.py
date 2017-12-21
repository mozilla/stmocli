import traceback
import pytest
import click
import json
import os
from httmock import all_requests, HTTMock
from redash_client.client import RedashClient
from click.testing import CliRunner
from stmocli import cli
from stmocli.conf import default_path as conf_path


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
        result = runner.invoke(cli.init)

        print_debug_for_runner(result)

        assert os.path.isfile(conf_path)

def test_track(runner):
    query_id = '49741'
    query_name = 'poc'
    filename = query_name + '.sql'

    with runner.isolated_filesystem():
        with HTTMock(response_content):
            result = runner.invoke(cli.track, [
                query_id,
                query_name,
                '--redash_api_key',
                'TOTALLY_FAKE_KEY'
            ])

        print_debug_for_runner(result)

        # Verify we save the query to the right file
        assert os.path.isfile(filename)
        with open(filename, 'r') as query:
            assert "SELECT" in query.read()

        # Verify we save the query_id to the config file
        assert os.path.isfile(conf_path)
        with open(conf_path, 'r') as conf_file:
            config = json.loads(conf_file.read())
            assert query_name in config
            assert config[query_name]['redash_id'] == query_id


def print_debug_for_runner(result):
    """Helper function for printing click.runner debug tracebacks."""
    print(result.output)
    print(result.exc_info)
    traceback.print_tb(result.exc_info[2])
    print(result.exit_code)
    print(result.exception)
