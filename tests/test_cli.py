import traceback
import pytest
import click
import json
import md5
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

@all_requests
def push_response(url, request):
    return {'status_code': 200,
            'content': '{}'}

@all_requests
def push_response_fail(url, request):
    return {'status_code': 500,
            'content': '{}'}

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
    file_name = 'poc.sql'

    with runner.isolated_filesystem():
        with HTTMock(response_content):
            result = runner.invoke(cli.track, [
                query_id,
                file_name,
                '--redash_api_key',
                'TOTALLY_FAKE_KEY'
            ])

        print_debug_for_runner(result)

        # Verify we save the query to the right file
        assert os.path.isfile(file_name)
        with open(file_name, 'r') as query:
            assert "SELECT" in query.read()

        # Verify we save the query_id to the config file
        assert os.path.isfile(conf_path)
        with open(conf_path, 'r') as conf_file:
            config = json.loads(conf_file.read())
            assert file_name in config
            assert config[file_name]['id'] == query_id

def setup_tracked_query(runner, query_id, file_name):
    with HTTMock(response_content):
        result = runner.invoke(cli.track, [
            query_id,
            file_name
        ])

    # Read the saved query
    assert os.path.isfile(file_name)
    with open(file_name, 'r') as fin:
        query_contents = fin.read()
    return query_contents

def update_tracked_query(file_name, original_query):
    updated_query = original_query + "--appended"
    with open(file_name, 'w') as fout:
        fout.write(updated_query)
    return updated_query

def test_push_tracked(runner):
    query_id = '49741'
    file_name = 'poc.sql'

    with runner.isolated_filesystem():
        # Track the example query
        query_before = setup_tracked_query(runner, query_id, file_name)
        # Overwrite with a new query string
        query_after = update_tracked_query(file_name, query_before)

        # Now push the result
        with HTTMock(push_response):
            push_result = runner.invoke(cli.push, [
                file_name
            ])

        m = md5.new()
        m.update(query_after)
        expected_output = "Query ID {} updated with content from {} (md5 {})".format(
            query_id, file_name, m.hexdigest())
        assert push_result.output.strip() == expected_output

def test_push_fail(runner):
    query_id = '49741'
    file_name = 'poc.sql'

    with runner.isolated_filesystem():
        query_before = setup_tracked_query(runner, query_id, file_name)
        query_after = update_tracked_query(file_name, query_before)

        # Now push the result, expecting a failure
        with HTTMock(push_response_fail):
            push_result = runner.invoke(cli.push, [
                file_name
            ])

        expected_output = "Failed to update query from {}:".format(file_name)
        assert push_result.output.startswith(expected_output)
        assert "500" in push_result.output

def test_push_untracked(runner):
    file_name = 'missing.sql'

    # Try to push a nonexistent query
    with HTTMock(push_response):
        push_result = runner.invoke(cli.push, [
            file_name
        ])

    assert "No such query" in push_result.output


def print_debug_for_runner(result):
    """Helper function for printing click.runner debug tracebacks."""
    print(result.output)
    print(result.exc_info)
    traceback.print_tb(result.exc_info[2])
    print(result.exit_code)
    print(result.exception)
